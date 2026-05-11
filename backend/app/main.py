from fastapi import FastAPI, status
from fastapi.responses import JSONResponse

from app.routes import auth
from app.core.config import settings

app = FastAPI(
    title="unofficial pw-client api",
    description="download notes, dpps, and quizzes from pw.live; includes mcp server for llm integration.",
    version=settings.VERSION,
)

app.include_router(router=auth.router)


@app.get("/", status_code=status.HTTP_200_OK, tags=["system"])
def read_root():
    return JSONResponse(
        {
            "name": "pw-client-api",
            "version": settings.VERSION,
            "docs_url": "https://github.com/viraj-sh/pw-client",
        }
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=5001, reload=True)
