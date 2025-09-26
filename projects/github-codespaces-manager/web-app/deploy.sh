#!/bin/bash
"""
GitHub Codespaces Manager - Web Application Deployment Script
Automated deployment for Termux/Android environments
"""

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
WEB_APP_DIR="$(pwd)"
BACKEND_DIR="$WEB_APP_DIR/backend"
FRONTEND_DIR="$WEB_APP_DIR/frontend"
BACKEND_PORT=8000
FRONTEND_PORT=3000

echo -e "${PURPLE}🚀 GitHub Codespaces Manager - Web Deployment${NC}"
echo "=================================================================="

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check prerequisites
check_prerequisites() {
    print_info "Checking prerequisites..."

    # Check Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is required but not installed"
        exit 1
    fi
    print_status "Python 3 found: $(python3 --version)"

    # Check pip
    if ! command -v pip &> /dev/null && ! command -v pip3 &> /dev/null; then
        print_error "pip is required but not installed"
        exit 1
    fi
    print_status "pip found"

    # Check GitHub CLI
    if ! command -v gh &> /dev/null; then
        print_warning "GitHub CLI (gh) not found - some features may not work"
    else
        print_status "GitHub CLI found: $(gh --version | head -1)"
    fi
}

# Install backend dependencies
install_backend_deps() {
    print_info "Installing backend dependencies..."

    cd "$BACKEND_DIR"

    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        print_info "Creating Python virtual environment..."
        python3 -m venv venv
    fi

    # Activate virtual environment
    source venv/bin/activate

    # Upgrade pip
    pip install --upgrade pip

    # Install requirements
    if [ -f "requirements.txt" ]; then
        print_info "Installing Python packages..."
        pip install -r requirements.txt
        print_status "Backend dependencies installed"
    else
        print_warning "requirements.txt not found, installing minimal dependencies..."
        pip install fastapi uvicorn websockets aiosqlite pydantic-settings psutil
    fi
}

# Setup database
setup_database() {
    print_info "Setting up database..."
    cd "$BACKEND_DIR"

    # Initialize database (will be created automatically when app starts)
    print_status "Database setup complete"
}

# Start backend server
start_backend() {
    print_info "Starting backend server..."
    cd "$BACKEND_DIR"

    # Activate virtual environment
    source venv/bin/activate

    # Start the server in background
    print_info "Backend starting on port $BACKEND_PORT..."
    python start_server.py &
    BACKEND_PID=$!

    # Wait for server to start
    sleep 5

    # Check if server is running
    if curl -s "http://localhost:$BACKEND_PORT/health" > /dev/null 2>&1; then
        print_status "Backend server started successfully (PID: $BACKEND_PID)"
        echo "$BACKEND_PID" > backend.pid
    else
        print_error "Backend server failed to start"
        return 1
    fi
}

# Start frontend server
start_frontend() {
    print_info "Starting frontend server..."
    cd "$WEB_APP_DIR"

    # Start frontend server in background
    print_info "Frontend starting on port $FRONTEND_PORT..."
    python simple_server.py &
    FRONTEND_PID=$!

    # Wait for server to start
    sleep 3

    # Check if server is running
    if curl -s "http://localhost:$FRONTEND_PORT" > /dev/null 2>&1; then
        print_status "Frontend server started successfully (PID: $FRONTEND_PID)"
        echo "$FRONTEND_PID" > frontend.pid
    else
        print_error "Frontend server failed to start"
        return 1
    fi
}

# Create systemd-style service files for Termux
create_service_files() {
    print_info "Creating service management scripts..."

    # Backend service script
    cat > start_backend.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")/backend"
source venv/bin/activate
python start_server.py
EOF
    chmod +x start_backend.sh

    # Frontend service script
    cat > start_frontend.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
python simple_server.py
EOF
    chmod +x start_frontend.sh

    # Combined startup script
    cat > start_web_app.sh << 'EOF'
#!/bin/bash
# GitHub Codespaces Manager - Web Application Startup

echo "🚀 Starting GitHub Codespaces Manager Web Application..."

# Start backend
echo "📡 Starting backend API server..."
./start_backend.sh &
BACKEND_PID=$!
echo "Backend PID: $BACKEND_PID"

# Wait a moment
sleep 5

# Start frontend
echo "🌐 Starting frontend web server..."
./start_frontend.sh &
FRONTEND_PID=$!
echo "Frontend PID: $FRONTEND_PID"

# Save PIDs
echo "$BACKEND_PID" > backend.pid
echo "$FRONTEND_PID" > frontend.pid

echo ""
echo "✅ GitHub Codespaces Manager is now running!"
echo "🌐 Web Interface: http://localhost:3000"
echo "📡 API Documentation: http://localhost:8000/docs"
echo "🔌 WebSocket: ws://localhost:8000/ws"
echo ""
echo "📝 To stop the services:"
echo "   kill $(cat backend.pid) $(cat frontend.pid)"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for interrupt
trap 'echo "Stopping services..."; kill $BACKEND_PID $FRONTEND_PID; exit 0' INT
wait
EOF
    chmod +x start_web_app.sh

    # Stop script
    cat > stop_web_app.sh << 'EOF'
#!/bin/bash
echo "🛑 Stopping GitHub Codespaces Manager Web Application..."

if [ -f backend.pid ]; then
    BACKEND_PID=$(cat backend.pid)
    kill $BACKEND_PID 2>/dev/null && echo "✅ Backend stopped" || echo "⚠️ Backend was not running"
    rm -f backend.pid
fi

if [ -f frontend.pid ]; then
    FRONTEND_PID=$(cat frontend.pid)
    kill $FRONTEND_PID 2>/dev/null && echo "✅ Frontend stopped" || echo "⚠️ Frontend was not running"
    rm -f frontend.pid
fi

echo "🏁 All services stopped"
EOF
    chmod +x stop_web_app.sh

    print_status "Service scripts created"
}

# Print deployment summary
print_summary() {
    echo ""
    echo -e "${PURPLE}=================================================================="
    echo -e "🎉 DEPLOYMENT COMPLETE!"
    echo -e "==================================================================${NC}"
    echo ""
    echo -e "${GREEN}🌐 Web Interface:${NC}     http://localhost:$FRONTEND_PORT"
    echo -e "${GREEN}📡 API Backend:${NC}       http://localhost:$BACKEND_PORT"
    echo -e "${GREEN}📚 API Documentation:${NC} http://localhost:$BACKEND_PORT/docs"
    echo -e "${GREEN}🔌 WebSocket Endpoint:${NC} ws://localhost:$BACKEND_PORT/ws"
    echo ""
    echo -e "${BLUE}📋 Management Commands:${NC}"
    echo -e "${YELLOW}   Start All Services:${NC}  ./start_web_app.sh"
    echo -e "${YELLOW}   Stop All Services:${NC}   ./stop_web_app.sh"
    echo -e "${YELLOW}   Backend Only:${NC}        ./start_backend.sh"
    echo -e "${YELLOW}   Frontend Only:${NC}       ./start_frontend.sh"
    echo ""
    echo -e "${CYAN}🚀 Features Available:${NC}"
    echo "   ✅ Codespace Management (Create, Start, Stop, Delete)"
    echo "   ✅ Language & Environment Setup (8 languages + AI agents)"
    echo "   ✅ Real-time Updates via WebSocket"
    echo "   ✅ Metrics & Cost Tracking"
    echo "   ✅ System Monitoring"
    echo "   ✅ Mobile-responsive Interface"
    echo ""
    echo -e "${GREEN}Ready for production use!${NC}"
    echo "=================================================================="
}

# Cleanup function
cleanup() {
    if [ -f backend.pid ]; then
        kill $(cat backend.pid) 2>/dev/null
        rm -f backend.pid
    fi
    if [ -f frontend.pid ]; then
        kill $(cat frontend.pid) 2>/dev/null
        rm -f frontend.pid
    fi
}

# Main deployment process
main() {
    # Set trap for cleanup
    trap cleanup EXIT

    check_prerequisites
    install_backend_deps
    setup_database
    create_service_files

    print_info "Deployment completed successfully!"
    print_info "Use ./start_web_app.sh to start the application"

    # Ask if user wants to start now
    echo ""
    read -p "🚀 Would you like to start the web application now? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        start_backend
        start_frontend
        print_summary

        # Keep script running to maintain services
        echo "Press Ctrl+C to stop all services..."
        wait
    else
        print_info "Use './start_web_app.sh' when ready to start the application"
    fi
}

# Run main function
main "$@"