from datetime import timedelta, datetime, timezone
import requests_cache
import logging
from core.logging import setup_logging
import os

setup_logging()
logger = logging.getLogger("core.cache")

# ----------------------------
# Cached session configuration
# ----------------------------
cached_session = requests_cache.CachedSession(
    cache_name=".cache/http_cache",
    backend="sqlite",
    expire_after=timedelta(hours=2),
    allowable_methods=("GET", "POST"),
    stale_if_error=True,  # Serve stale cache when upstream fails
)


# ----------------------------
# Smart Cached Request
# ----------------------------
def cached_request(
    method: str,
    url: str,
    *,
    expire_after: timedelta | None = None,
    log_prefix: str = "",
    refetch: bool = False,
    **kwargs,
):
    if refetch:
        kwargs.setdefault("headers", {}).update({"Cache-Control": "no-cache"})
    response = cached_session.request(method, url, expire_after=expire_after, **kwargs)
    from_cache = getattr(response, "from_cache", False)
    ttl_requested = (
        expire_after if expire_after is not None else cached_session.expire_after
    )
    ttl_remaining = "N/A"
    age_str = "N/A"
    now = datetime.now(timezone.utc)

    if from_cache:
        try:
            cache_key = cached_session.cache.create_key(response.request)
            record = cached_session.cache.responses.get(cache_key)
            if record:
                created_at = getattr(record, "created_at", None)
                expires = getattr(record, "expires", None)

                if created_at and created_at.tzinfo is None:
                    created_at = created_at.replace(tzinfo=timezone.utc)
                if expires and expires.tzinfo is None:
                    expires = expires.replace(tzinfo=timezone.utc)

                if created_at:
                    age = now - created_at
                    age_str = f"{age.total_seconds() / 60:.1f} min"

                if expires:
                    remaining = expires - now
                    ttl_remaining = f"{remaining.total_seconds() / 60:.1f} min left"
        except Exception as e:
            logger.debug(f"{log_prefix}Failed to compute cache metadata: {e}")

    cache_event = "HIT" if from_cache else "MISS"
    logger.info(
        f"{log_prefix}Cache {cache_event}, TTL requested: {ttl_requested}, TTL remaining: {ttl_remaining}, age: {age_str}",
        extra={
            "url": url,
            "method": method,
            "source": "cache" if from_cache else "network",
        },
    )

    return response


# ----------------------------
# Smart cache invalidation
# ----------------------------
def invalidate_cache(response) -> None:
    try:
        cache_key = cached_session.cache.create_key(response.request)
        if cache_key in cached_session.cache.responses:
            cached_session.cache.delete(cache_key)
            logger.warning(
                "Invalid cache entry removed",
                extra={"url": response.url, "method": response.request.method},
            )
        else:
            logger.debug(
                "No cache entry found to invalidate",
                extra={"url": response.url, "method": response.request.method},
            )
    except Exception as e:
        logger.error(
            f"Failed to invalidate cache: {e}",
            extra={"url": getattr(response, "url", "unknown")},
        )


# ----------------------------
# Cache maintenance utilities
# ----------------------------
def clear_cache():
    logger = setup_logging(name="core.clear_cache", level="INFO")

    try:
        if "cached_session" not in globals() or cached_session is None:
            logger.warning("Cache clear skipped: cached_session not initialized")
            return

        cache_attr = getattr(cached_session, "cache", None)
        if cache_attr is None:
            logger.warning("Cache clear skipped: no cache attribute on cached_session")
            return
        try:
            cache_attr.clear()
            logger.info(
                "All HTTP cache cleared successfully", extra={"action": "clear_cache"}
            )
        except Exception as inner_exc:
            logger.warning(
                f"Failed to clear cache: {inner_exc}", extra={"action": "clear_cache"}
            )

    except Exception as exc:
        logger.exception(f"Unexpected error while clearing cache: {exc}")


def get_cache_stats() -> dict:
    cache = cached_session.cache
    now = datetime.now(timezone.utc)
    response_ttls = {}

    for key, record in cache.responses.items():
        expires = getattr(record, "expires", None)
        if expires and expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        if expires:
            ttl_remaining = (expires - now).total_seconds() / 60  # minutes
            response_ttls[key] = f"{ttl_remaining:.1f} min left"
        else:
            response_ttls[key] = "N/A"

    stats = {
        "backend": type(cache).__name__,
        "responses": len(cache.responses),
        "expire_after_default": str(cached_session.expire_after),
        "cache_path": str(cache.cache_name),
        "response_ttls": response_ttls,
    }
    logger.debug("Cache stats retrieved", extra=stats)
    return stats
