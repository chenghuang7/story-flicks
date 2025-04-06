from fastapi import FastAPI, APIRouter
from fastapi.staticfiles import StaticFiles

from fastapi.middleware.cors import CORSMiddleware
from app.api import api_router
import os

from app.database.session import with_session
from app.database.base import engine
from app.schemas.user import User
from app.api.login import user_router

from app.config import settings

app = FastAPI(
    title="StoryFlicks Backend API",
    description="Backend API for StoryFlicks application",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    # allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],  # In production, replace with specific origins
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if not os.path.exists('tasks'):
    os.makedirs('tasks')

app.mount("/tasks", StaticFiles(directory=os.path.abspath("tasks")), name="tasks")
# Include API router
app.include_router(api_router)

@app.get("/")
async def root():
    return {
        "app_name": "StoryFlicks Backend API",
        "docs_url": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=int(settings.backend_port), reload=True)
