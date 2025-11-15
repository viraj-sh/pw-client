from core.logging import setup_logging
from api.system import router as system_router
from api.auth import router as auth_router
from api.content import router as content_router
from fastapi import FastAPI
import logging
import os


logger = setup_logging(name="app", level="INFO")

app = FastAPI(title="Unofficial PW API")

origins = ["*"]


logger.info("Application startup complete")

# Include routers
app.include_router(system_router, prefix="/api")
app.include_router(auth_router, prefix="/api")
app.include_router(content_router, prefix="/api")


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
