import asyncio
from contextlib import asynccontextmanager
import httpx
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.logging import setup_logging, get_logger
from app.core.exceptions import DownloadAgentException
from app.routes.download import router as download_router

settings = get_settings()
setup_logging(settings.LOG_LEVEL)
logger = get_logger("main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing download agent application...")
    
    limits = httpx.Limits(max_keepalive_connections=10, max_connections=50)
    app.state.http_client = httpx.AsyncClient(
        limits=limits,
        timeout=settings.REQUEST_TIMEOUT_SECONDS
    )
    
    logger.info(f"Setting concurrency limit to {settings.MAX_CONCURRENT_DOWNLOADS} downloads.")
    app.state.download_semaphore = asyncio.Semaphore(settings.MAX_CONCURRENT_DOWNLOADS)
    
    try:
        settings.DOWNLOAD_PATH.mkdir(parents=True, exist_ok=True)
        logger.info(f"Downloads directory verified: {settings.DOWNLOAD_PATH.absolute()}")
    except Exception as e:
        logger.critical(f"Failed to initialize downloads path {settings.DOWNLOAD_PATH}: {e}")

    yield

    logger.info("Stopping download agent application. Cleaning up connections...")
    await app.state.http_client.aclose()
    logger.info("Outbound client connections closed. Lifespan completed.")

app = FastAPI(
    title="Local Video Download Agent",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(DownloadAgentException)
async def download_agent_exception_handler(request: Request, exc: DownloadAgentException):
    logger.error(f"Application error handling {request.url.path}: {exc.message}")
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    
    if exc.__class__.__name__ == "UpstreamAPIException":
        status_code = status.HTTP_502_BAD_GATEWAY
    elif exc.__class__.__name__ == "ValidationException":
        status_code = status.HTTP_400_BAD_REQUEST
    elif exc.__class__.__name__ == "FileSystemException":
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        
    return JSONResponse(
        status_code=status_code,
        content={"detail": exc.message}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error handling request to {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An unexpected error occurred in the download agent server."}
    )

app.include_router(download_router)

@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "healthy", "service": "download-agent"}
