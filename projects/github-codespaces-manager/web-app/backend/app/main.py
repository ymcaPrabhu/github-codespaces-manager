#!/usr/bin/env python3
"""
GitHub Codespaces Manager - Web Application Backend
FastAPI-based REST API with WebSocket support for real-time operations
"""

import os
import sys
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from contextlib import asynccontextmanager

# Add parent directory to path to import existing modules
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../'))

from app.core.config import settings
from app.core.websockets import WebSocketManager
from app.api import codespaces, languages, metrics, system
from app.models.database import init_database


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    await init_database()
    print("🚀 GitHub Codespaces Manager Web API started")
    print(f"📡 WebSocket endpoint: ws://localhost:{settings.PORT}/ws")
    print(f"🌐 API documentation: http://localhost:{settings.PORT}/docs")

    yield

    # Shutdown
    print("🛑 GitHub Codespaces Manager Web API shutting down")


# Create FastAPI application
app = FastAPI(
    title="GitHub Codespaces Manager API",
    description="Web API for managing GitHub Codespaces with real-time updates",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket manager for real-time updates
websocket_manager = WebSocketManager()

# Include API routers
app.include_router(codespaces.router, prefix="/api/codespaces", tags=["codespaces"])
app.include_router(languages.router, prefix="/api/languages", tags=["languages"])
app.include_router(metrics.router, prefix="/api/metrics", tags=["metrics"])
app.include_router(system.router, prefix="/api/system", tags=["system"])

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main application"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>GitHub Codespaces Manager</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; margin: 0; padding: 2rem; }
            .container { max-width: 800px; margin: 0 auto; text-align: center; }
            .status { background: #10b981; color: white; padding: 1rem; border-radius: 8px; margin: 1rem 0; }
            .links { display: flex; gap: 1rem; justify-content: center; margin: 2rem 0; }
            .link { background: #3b82f6; color: white; padding: 0.75rem 1.5rem; border-radius: 6px; text-decoration: none; }
            .link:hover { background: #2563eb; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚀 GitHub Codespaces Manager</h1>
            <div class="status">✅ Web API is running successfully!</div>
            <p>Manage your GitHub Codespaces with a modern web interface</p>
            <div class="links">
                <a href="/docs" class="link">📚 API Documentation</a>
                <a href="/redoc" class="link">📖 ReDoc</a>
                <a href="http://localhost:3000" class="link">🌐 Web Interface</a>
            </div>
            <p><strong>Version:</strong> 2.0.0 | <strong>Status:</strong> Active</p>
        </div>
    </body>
    </html>
    """


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await websocket_manager.connect(websocket)
    try:
        while True:
            # Keep connection alive and handle incoming messages
            data = await websocket.receive_text()
            # Echo back for testing
            await websocket_manager.send_personal_message(f"Echo: {data}", websocket)
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "GitHub Codespaces Manager API",
        "version": "2.0.0"
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        access_log=True
    )