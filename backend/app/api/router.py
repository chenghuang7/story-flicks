from fastapi import APIRouter
from app.api import voice, video, llm, login

router = APIRouter(prefix="/api")
router.include_router(voice.router, prefix="/voice", tags=["voice"])
router.include_router(video.router, prefix="/video", tags=["video"])
router.include_router(llm.router, prefix="/llm", tags=["llm"])
router.include_router(login.user_router, prefix="/login", tags=["login"])
