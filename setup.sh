#!/bin/bash

# AI Resume Analyzer Setup Script
# This script sets up the development environment

set -e

echo "==================================="
echo "AI Resume Analyzer Setup"
echo "==================================="
echo ""

# Check for Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.9 or higher."
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"

# Check for Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 16 or higher."
    exit 1
fi

echo "✅ Node.js found: $(node --version)"

# Check for Docker
if ! command -v docker &> /dev/null; then
    echo "⚠️  Docker is not installed. Docker is optional but recommended."
else
    echo "✅ Docker found: $(docker --version)"
fi

echo ""
echo "Setting up backend..."
cd backend

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Download spaCy model
echo "Downloading spaCy language model..."
python -m spacy download en_core_web_sm

# Copy environment file
if [ ! -f ".env" ]; then
    echo "Creating .env file from example..."
    cp .env.example .env
    echo "⚠️  Please edit backend/.env with your configuration"
fi

# Create directories
mkdir -p uploads logs

cd ..

echo ""
echo "Setting up frontend..."
cd frontend

# Install dependencies
echo "Installing Node.js dependencies..."
npm install

# Copy environment file
if [ ! -f ".env" ]; then
    echo "Creating .env file from example..."
    cp .env.example .env
    echo "⚠️  Please edit frontend/.env with your configuration"
fi

cd ..

echo ""
echo "==================================="
echo "✅ Setup complete!"
echo "==================================="
echo ""
echo "Next steps:"
echo ""
echo "1. Configure your environment files:"
echo "   - backend/.env"
echo "   - frontend/.env"
echo ""
echo "2. Start the development servers:"
echo "   Option A - Using Docker:"
echo "     docker-compose up -d"
echo ""
echo "   Option B - Manual:"
echo "     Terminal 1 (Backend):"
echo "       cd backend"
echo "       source venv/bin/activate"
echo "       uvicorn app.main:app --reload"
echo ""
echo "     Terminal 2 (Frontend):"
echo "       cd frontend"
echo "       npm start"
echo ""
echo "3. Access the application:"
echo "   Frontend: http://localhost:3000"
echo "   Backend API: http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "Happy coding! 🚀"
