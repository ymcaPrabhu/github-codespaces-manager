#!/usr/bin/env python3
"""
Simple web server for testing the GitHub Codespaces Manager web interface
"""

import os
import sys
import http.server
import socketserver
import webbrowser
from pathlib import Path

# Configuration
PORT = 3000
FRONTEND_DIR = Path(__file__).parent / "frontend"

class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Custom handler to serve from frontend directory"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(FRONTEND_DIR), **kwargs)

    def end_headers(self):
        # Add CORS headers
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        super().end_headers()

def main():
    """Start the simple web server"""

    # Check if frontend directory exists
    if not FRONTEND_DIR.exists():
        print(f"❌ Frontend directory not found: {FRONTEND_DIR}")
        sys.exit(1)

    # Change to frontend directory
    os.chdir(FRONTEND_DIR)

    try:
        # Create server
        with socketserver.TCPServer(("", PORT), CustomHTTPRequestHandler) as httpd:
            print("🚀 GitHub Codespaces Manager - Simple Web Server")
            print("=" * 60)
            print(f"🌐 Server running at: http://localhost:{PORT}")
            print(f"📁 Serving from: {FRONTEND_DIR}")
            print(f"📄 Main page: http://localhost:{PORT}/index.html")
            print("\n💡 This is a demo version with mock data")
            print("💡 For full functionality, start the FastAPI backend")
            print("\n🛑 Press Ctrl+C to stop the server")
            print("=" * 60)

            # Try to open browser
            try:
                webbrowser.open(f'http://localhost:{PORT}')
                print("🌐 Opening web browser...")
            except:
                print("⚠️ Could not open browser automatically")

            # Start serving
            httpd.serve_forever()

    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except OSError as e:
        if "Address already in use" in str(e):
            print(f"❌ Port {PORT} is already in use")
            print("💡 Try stopping other servers or use a different port")
        else:
            print(f"❌ Server error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()