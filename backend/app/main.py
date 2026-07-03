from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.http import http_state
from app.routes import ann, auth, batch, dashboard, quiz


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    http_state.client = httpx.AsyncClient(
        timeout=httpx.Timeout(
            connect=5.0,
            read=10.0,
            write=10.0,
            pool=5.0,
        ),
        limits=httpx.Limits(
            max_connections=100,
            max_keepalive_connections=20,
        ),
        follow_redirects=True,
    )

    yield

    # Shutdown
    await http_state.client.aclose()


app = FastAPI(
    title="unofficial pw-client api",
    description="download notes, dpps, and quizzes from pw.live; includes mcp server for llm integration.",
    version=settings.VERSION,
    lifespan=lifespan,
)

app.add_middleware(
    middleware_class=CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", status_code=status.HTTP_200_OK, tags=["system"])
def read_root():
    return JSONResponse({
        "name": "pw-client-api",
        "version": settings.VERSION,
        "docs_url": "https://github.com/viraj-sh/pw-client",
    })


app.include_router(router=auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(router=batch.router, prefix="/api/v1/batch", tags=["batch"])
app.include_router(
    router=ann.router, prefix="/api/v1/announcement", tags=["announcement"]
)
app.include_router(router=quiz.router, prefix="/api/v1/quiz", tags=["quiz"])
app.include_router(
    router=dashboard.router, prefix="/api/v1/dashboard", tags=["dashboard"]
)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=5001, reload=True)
