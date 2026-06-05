#!/bin/bash
# Get It Done - Setup Script
# Run this script to set up the project for development

set -e

echo "Get It Done - Setup Script"
echo "=========================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check Python
echo -e "${YELLOW}Checking Python installation...${NC}"
if command -v python3 &> /dev/null; then
    echo -e "${GREEN}OK $(python3 --version)${NC}"
else
    echo -e "${RED}Python 3.12+ is required${NC}"
    exit 1
fi

# Check Node.js
echo -e "${YELLOW}Checking Node.js installation...${NC}"
if command -v node &> /dev/null; then
    echo -e "${GREEN}OK Node.js $(node --version)${NC}"
else
    echo -e "${RED}Node.js 18+ is required${NC}"
    exit 1
fi

# Check npm
if command -v npm &> /dev/null; then
    echo -e "${GREEN}OK npm found${NC}"
else
    echo -e "${RED}npm is required${NC}"
    exit 1
fi

echo ""

# Python virtual environment
echo -e "${YELLOW}Setting up Python virtual environment...${NC}"
cd backend
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q
echo -e "${GREEN}OK Python dependencies installed${NC}"

# Playwright browsers (optional)
echo -e "${YELLOW}Installing Playwright browsers...${NC}"
playwright install chromium 2>/dev/null && echo -e "${GREEN}OK Playwright installed${NC}" || echo -e "${YELLOW}SKIP Playwright install skipped (optional)${NC}"
cd ..

# Frontend
echo -e "${YELLOW}Setting up frontend...${NC}"
cd frontend
npm install --silent
echo -e "${GREEN}OK Frontend dependencies installed${NC}"
cd ..

# Backend environment file
echo -e "${YELLOW}Setting up backend environment variables...${NC}"
if [ ! -f "backend/.env" ]; then
    cp backend/.env.example backend/.env
    echo -e "${YELLOW}INFO backend/.env created from .env.example - update with your credentials${NC}"
else
    echo -e "${GREEN}OK backend/.env exists${NC}"
fi

# Frontend environment file
if [ ! -f "frontend/.env.local" ]; then
    cp frontend/.env.example frontend/.env.local
    echo -e "${YELLOW}INFO frontend/.env.local created from .env.example${NC}"
else
    echo -e "${GREEN}OK frontend/.env.local exists${NC}"
fi

echo ""
echo "=========================="
echo -e "${GREEN}Setup complete${NC}"
echo ""
echo "To start development:"
echo ""
echo "  Terminal 1 - Backend:"
echo "    cd backend && source venv/bin/activate && uvicorn main:app --reload --port 8000"
echo ""
echo "  Terminal 2 - Frontend:"
echo "    cd frontend && npm run dev"
echo ""
echo "  Terminal 3 - Convex (if using Convex DB):"
echo "    npx convex dev"
echo ""
echo "Or use Docker:"
echo "    docker compose up"
echo ""
echo "After setup:"
echo "  1. Update backend/.env with your Amazon affiliate tag"
echo "  2. Add your Pinterest API token"
echo "  3. Configure publishing preferences in Settings"
echo ""
