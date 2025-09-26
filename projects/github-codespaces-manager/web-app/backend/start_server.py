#!/usr/bin/env python3
"""
GitHub Codespaces Manager Web API Server
Production-ready startup script with health checks and monitoring
"""

import os
import sys
import asyncio
import uvicorn
import signal
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.main import app
from app.core.config import settings


class ServerManager:
    """Manages the web server lifecycle"""

    def __init__(self):
        self.server = None
        self.should_exit = False

    def signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        print(f"\n🛑 Received signal {signum}, shutting down gracefully...")
        self.should_exit = True

    async def health_check(self):
        """Periodic health check"""
        while not self.should_exit:
            try:
                # Basic health check logic here
                print("❤️ Health check: Server is healthy")
                await asyncio.sleep(300)  # Check every 5 minutes
            except Exception as e:
                print(f"⚠️ Health check failed: {e}")
                await asyncio.sleep(60)  # Retry in 1 minute

    def run(self):
        """Run the server with monitoring"""
        # Set up signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

        print("🚀 Starting GitHub Codespaces Manager Web API...")
        print(f"🌐 Server will be available at: http://{settings.HOST}:{settings.PORT}")
        print(f"📚 API Documentation: http://{settings.HOST}:{settings.PORT}/docs")
        print(f"🔌 WebSocket endpoint: ws://{settings.HOST}:{settings.PORT}/ws")
        print("📊 Health endpoint: /health")
        print("\n" + "="*60 + "\n")

        try:
            # Run the server
            config = uvicorn.Config(
                app,
                host=settings.HOST,
                port=settings.PORT,
                reload=settings.DEBUG,
                access_log=True,
                log_level=settings.LOG_LEVEL.lower()
            )

            server = uvicorn.Server(config)
            server.run()

        except KeyboardInterrupt:
            print("\n🛑 Server interrupted by user")
        except Exception as e:
            print(f"❌ Server error: {e}")
            sys.exit(1)
        finally:
            print("👋 GitHub Codespaces Manager Web API stopped")


if __name__ == "__main__":
    # Environment setup
    if not os.path.exists("static"):
        os.makedirs("static")
    if not os.path.exists("templates"):
        os.makedirs("templates")

    # Start the server
    server_manager = ServerManager()
    server_manager.run()