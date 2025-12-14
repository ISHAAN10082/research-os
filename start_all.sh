#!/bin/bash

# ResearchOS Unified Startup Script
# Starts backend and frontend with proper health checks and graceful shutdown

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BACKEND_PORT=8000
FRONTEND_PORT=5173
MAX_HEALTH_CHECKS=60  # Increased from 30 to 60 for model loading
HEALTH_CHECK_INTERVAL=2  # Check every 2 seconds

echo -e "${BLUE}🚀 Starting ResearchOS...${NC}\n"

# Cleanup function for graceful shutdown
cleanup() {
    echo -e "\n${YELLOW}🛑 Shutting down all services...${NC}"
    
    if [ ! -z "$BACKEND_PID" ]; then
        echo "  Stopping backend (PID: $BACKEND_PID)..."
        kill $BACKEND_PID 2>/dev/null || true
    fi
    
    if [ ! -z "$FRONTEND_PID" ]; then
        echo "  Stopping frontend (PID: $FRONTEND_PID)..."
        kill $FRONTEND_PID 2>/dev/null || true
    fi
    
    echo -e "${GREEN}✅ All services stopped${NC}"
    exit 0
}

# Register cleanup on exit
trap cleanup INT TERM EXIT

# Check if ports are available
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo -e "${RED}❌ Port $port is already in use${NC}"
        echo "   Kill the process using: lsof -ti:$port | xargs kill"
        exit 1
    fi
}

echo "📡 Checking ports..."
check_port $BACKEND_PORT
check_port $FRONTEND_PORT
echo -e "${GREEN}✅ Ports available${NC}\n"

# Start backend
echo "🔧 Starting backend on port $BACKEND_PORT..."
python research_os/web/server.py > backend.log 2>&1 &
BACKEND_PID=$!

if [ -z "$BACKEND_PID" ]; then
    echo -e "${RED}❌ Failed to start backend${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Backend started (PID: $BACKEND_PID)${NC}"

# Wait for backend health check
echo "⏳ Waiting for backend to be ready..."
HEALTH_CHECKS=0

while [ $HEALTH_CHECKS -lt $MAX_HEALTH_CHECKS ]; do
    if curl -s http://localhost:$BACKEND_PORT/api/health > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Backend healthy and ready${NC}\n"
        break
    fi
    
    HEALTH_CHECKS=$((HEALTH_CHECKS + 1))
    
    # Check if backend process died
    if ! kill -0 $BACKEND_PID 2>/dev/null; then
        echo -e "${RED}❌ Backend process died${NC}"
        echo "Check backend.log for errors:"
        tail -20 backend.log
        exit 1
    fi
    
    sleep $HEALTH_CHECK_INTERVAL
    echo -n "."
done

if [ $HEALTH_CHECKS -eq $MAX_HEALTH_CHECKS ]; then
    echo -e "\n${RED}❌ Backend failed to become healthy${NC}"
    echo "Check backend.log for errors:"
    tail -20 backend.log
    exit 1
fi

# Start frontend
echo "🎨 Starting frontend on port $FRONTEND_PORT..."
cd research_os/web/ui && npm run dev > ../../../frontend.log 2>&1 &
FRONTEND_PID=$!

if [ -z "$FRONTEND_PID" ]; then
    echo -e "${RED}❌ Failed to start frontend${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Frontend started (PID: $FRONTEND_PID)${NC}\n"

# Wait a moment for Vite to start
sleep 3

# Display status
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ ResearchOS is running!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "  📡 Backend:  ${BLUE}http://localhost:$BACKEND_PORT${NC}"
echo -e "  🎨 Frontend: ${BLUE}http://localhost:$FRONTEND_PORT${NC}"
echo -e "  📊 Health:   ${BLUE}http://localhost:$BACKEND_PORT/api/health${NC}"
echo ""
echo -e "  📝 Backend logs:  ${YELLOW}backend.log${NC}"
echo -e "  📝 Frontend logs: ${YELLOW}frontend.log${NC}"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop all services${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"

# Keep script running and show live logs
tail -f backend.log frontend.log 2>/dev/null &
TAIL_PID=$!

# Wait for any process to exit
wait $BACKEND_PID $FRONTEND_PID
