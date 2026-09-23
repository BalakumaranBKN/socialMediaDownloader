import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from .routers import media

app = FastAPI(
    title="BKN Social Platform Downloader API",
    description="High-speed media extraction API for Twitter/X, Instagram, Threads, TikTok, Reddit, YouTube Shorts, etc.",
    version="2.0.0"
)

# Configure CORS for local development and production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(media.router)

# Detect production frontend build
FRONTEND_DIST = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../frontend/dist/frontend/browser"))
if not os.path.exists(FRONTEND_DIST):
    FRONTEND_DIST = "/app/frontend/dist/frontend/browser"

if os.path.exists(FRONTEND_DIST):
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        if full_path.startswith("api") or full_path.startswith("docs") or full_path == "openapi.json":
            return None
        file_path = os.path.join(FRONTEND_DIST, full_path)
        if full_path and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(FRONTEND_DIST, "index.html"))
else:
    @app.get("/")
    def root():
        return {
            "status": "online",
            "service": "BKN Social Platform Downloader API",
            "version": "2.0.0",
            "supported_platforms": ["Twitter / X", "Instagram", "Threads", "TikTok", "Reddit", "YouTube Shorts", "Pinterest"]
        }


