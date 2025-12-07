import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_mcp import FastApiMCP
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from api.v1.system import router as system_router
from api.v1.auth import router as auth_router
from api.v1.lecture_content import router as lec_content_router
from api.v1.dpp_content import router as dpp_content_router
from api.v1.dashboard import router as dashboard_router
from api.v1.announcement import router as announcement_router
from core.logging import setup_logging
from core.utils import frontend_path

logger = setup_logging(name="app", level="INFO")

app = FastAPI(title="Unofficial PW API")

origins = [
    "http://127.0.0.1:8000",
    "http://localhost:8000",
    "*",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

static_dir = frontend_path()

app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/", include_in_schema=False)
def serve_frontend():
    return FileResponse(os.path.join(static_dir, "index.html"))


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse(os.path.join(static_dir, "assets", "favicon.ico"))


logger.info("Application startup complete")

# Include routers
app.include_router(system_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")
app.include_router(lec_content_router, prefix="/api/v1")
app.include_router(dpp_content_router, prefix="/api/v1")
app.include_router(dashboard_router, prefix="/api/v1")
app.include_router(announcement_router, prefix="/api/v1")

# MCP Tools
mcp = FastApiMCP(
    app,
    include_operations=[
        "get_system_info",
        "check_system_health",
        "list_countries",
        "send_otp_v1",
        "verify_user_otp",
        "verifyTokenAuthCheck",
        "logout_user_operation",
        "getUserBatches",
        "get_batch_subjects",
        "getChaptersForBatch",
        "fetch_chapter_content",
        "get_dpp_tests",
        "fetchDPPTestSolution",
        "fetchAnnouncements",
        "get_lecture_overview",
        "getLectureSubjectStats",
        "get_quiz_overview",
        "getQuizSubjectStats",
    ],
)
mcp.mount_http()

if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
