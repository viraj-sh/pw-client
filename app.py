from core.logging import setup_logging
from api.system import router as system_router
from api.auth import router as auth_router
from api.lecture_content import router as lec_content_router
from api.dpp_content import router as dpp_content_router
from api.dashboard import router as dashboard_router
from api.announcement import router as announcement_router
from fastapi import FastAPI
import logging
import os
from fastapi_mcp import FastApiMCP

logger = setup_logging(name="app", level="INFO")

app = FastAPI(title="Unofficial PW API")

origins = ["*"]


logger.info("Application startup complete")

# Include routers
app.include_router(system_router, prefix="/api")
app.include_router(auth_router, prefix="/api")
app.include_router(lec_content_router, prefix="/api")
app.include_router(dpp_content_router, prefix="/api")
app.include_router(dashboard_router, prefix="/api")
app.include_router(announcement_router, prefix="/api")

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
