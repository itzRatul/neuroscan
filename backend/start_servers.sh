#!/bin/bash

# --- NEUROSCAN STARTUP SCRIPT ---
# This script starts the Photo Scan Backend, the AI Chat Backend, and the WebApp frontend simultaneously.

# ANSI color codes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}=======================================${NC}"
echo -e "${BLUE}    🚀 Starting NeuroScan Services     ${NC}"
echo -e "${BLUE}=======================================${NC}"

# 1. Setup Virtual Environment and Install Dependencies
cd "$(dirname "$0")" || exit

if [ ! -d ".venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv .venv
fi

echo -e "${YELLOW}Activating virtual environment...${NC}"
source .venv/bin/activate

echo -e "${YELLOW}Installing dependencies...${NC}"
pip install -r requirements.txt -q

# 2. Check for .env file in chat_backend
if [ ! -f "../chat_backend/.env" ]; then
    echo -e "${RED}WARNING: .env file not found in chat_backend directory!${NC}"
    echo -e "${RED}Copying .env.example to .env in chat_backend. Please update it with your GROK API keys.${NC}"
    cp ../chat_backend/.env.example ../chat_backend/.env
fi

# 3. Start the Photo Scan Backend (Port 8000)
echo -e "\n${GREEN}Starting Photo Scan Backend (Port 8000)...${NC}"
uvicorn app:app --host 0.0.0.0 --port 8000 --reload > photo_scan_backend.log 2>&1 &
BACKEND_PID=$!
echo "Photo Scan Backend running with PID: $BACKEND_PID"

# 4. Start the AI Chat Backend (Port 8001)
echo -e "${GREEN}Starting AI Chat Backend (Port 8001)...${NC}"
cd ../chat_backend || exit
uvicorn app:app --host 0.0.0.0 --port 8001 --reload > ../backend/ai_chat_backend.log 2>&1 &
CHAT_PID=$!
echo "AI Chat Backend running with PID: $CHAT_PID"
cd ../backend || exit

# 5. Start the WebApp Frontend (Port 8080)
echo -e "${GREEN}Starting WebApp Frontend (Port 8080)...${NC}"
cd ../webapp || exit
python3 -m http.server 8080 > ../backend/webapp.log 2>&1 &
FRONTEND_PID=$!
echo "WebApp Frontend running with PID: $FRONTEND_PID"
cd ../backend || exit

echo -e "\n${BLUE}=======================================${NC}"
echo -e "${GREEN}✅ All services started successfully!${NC}"
echo -e "Photo Scan Backend: http://localhost:8000"
echo -e "AI Chat Backend:    http://localhost:8001"
echo -e "WebApp Frontend:    http://localhost:8080"
echo -e "Logs are being written to backend/photo_scan_backend.log, backend/ai_chat_backend.log, and backend/webapp.log"
echo -e "${YELLOW}Press Ctrl+C to stop all services.${NC}"
echo -e "${BLUE}=======================================${NC}"

# Function to handle termination
cleanup() {
    echo -e "\n${RED}Stopping all services...${NC}"
    kill $BACKEND_PID
    kill $CHAT_PID
    kill $FRONTEND_PID
    echo -e "${GREEN}All services stopped.${NC}"
    exit 0
}

# Trap SIGINT (Ctrl+C) and SIGTERM
trap cleanup SIGINT SIGTERM

# Keep script running
wait $BACKEND_PID
wait $CHAT_PID
wait $FRONTEND_PID
