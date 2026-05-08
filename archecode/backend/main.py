"""
ArcheCode - AI Code Archaeology Platform
Main FastAPI application entry point.
"""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from core.config import settings
from routers import projects, analysis, chat


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management."""
    # Startup
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs(settings.TEMP_DIR, exist_ok=True)
    os.makedirs("data", exist_ok=True)

    print(f"""
    ╔══════════════════════════════════════════════╗
    ║          ArcheCode v{settings.APP_VERSION}                  ║
    ║     AI Code Archaeology Platform             ║
    ║                                              ║
    ║  Server: http://{settings.HOST}:{settings.PORT}               ║
    ║  AI: {'Enabled' if settings.OPENAI_API_KEY else 'Disabled (set OPENAI_API_KEY)'}              ║
    ╚══════════════════════════════════════════════╝
    """)

    yield

    # Shutdown
    print("Shutting down ArcheCode...")


app = FastAPI(
    title="ArcheCode API",
    description="AI-powered code archaeology platform for rapid project onboarding",
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(projects.router)
app.include_router(analysis.router)
app.include_router(chat.router)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "name": "ArcheCode API",
        "version": settings.APP_VERSION,
        "status": "running",
        "ai_enabled": bool(settings.OPENAI_API_KEY),
    }


@app.get("/health")
async def health():
    """Detailed health check."""
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "ai_configured": bool(settings.OPENAI_API_KEY),
        "upload_dir": os.path.abspath(settings.UPLOAD_DIR),
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
