#!/bin/bash

# Roof Design Validation System - Startup Script
# This script starts both backend and frontend services

set -e

echo "🏗️  Roof Design Validation System"
echo "=================================="
echo

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}$1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if we're in the right directory
if [[ ! -d "backend" ]] || [[ ! -d "frontend" ]]; then
    print_error "Please run this script from the MAS project root directory"
    exit 1
fi

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
print_status "Checking prerequisites..."

if ! command_exists python3; then
    print_error "Python 3 is required but not installed"
    exit 1
fi

if ! command_exists node; then
    print_error "Node.js is required but not installed"
    exit 1
fi

if ! command_exists npm; then
    print_error "npm is required but not installed"
    exit 1
fi

print_success "All prerequisites are installed"
echo

# Check environment files
print_status "Checking environment configuration..."

BACKEND_ENV="backend/.env"
FRONTEND_ENV="frontend/.env.local"

if [[ ! -f "$BACKEND_ENV" ]]; then
    print_warning "Backend .env file not found"
    echo "Creating template .env file..."
    cat > "$BACKEND_ENV" << 'EOF'
# OpenAI API Configuration
OPENAI_API_KEY=your_api_key_here

# Server Configuration  
HOST=127.0.0.1
PORT=8000
DEBUG=true
ENVIRONMENT=development

# CORS Configuration
ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# Cost Tracking
TRACK_API_COSTS=true
LOG_LEVEL=INFO
EOF
    print_warning "Please edit backend/.env and add your OpenAI API key"
fi

if [[ ! -f "$FRONTEND_ENV" ]]; then
    print_warning "Frontend .env.local file not found"
    echo "Creating template .env.local file..."
    cat > "$FRONTEND_ENV" << 'EOF'
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
EOF
    print_success "Created frontend/.env.local file"
fi

echo

# Install dependencies
print_status "Installing dependencies..."

echo "📦 Installing backend dependencies..."
cd backend
if python3 -m pip install -r requirements.txt > /dev/null 2>&1; then
    print_success "Backend dependencies installed"
else
    print_error "Failed to install backend dependencies"
    exit 1
fi
cd ..

echo "📦 Installing frontend dependencies..."
cd frontend
if npm install > /dev/null 2>&1; then
    print_success "Frontend dependencies installed"
else
    print_error "Failed to install frontend dependencies"
    exit 1
fi
cd ..

echo

# Check if API key is set
if grep -q "your_api_key_here" "$BACKEND_ENV"; then
    print_error "Please set your OpenAI API key in backend/.env before starting"
    echo "Edit the file and replace 'your_api_key_here' with your actual API key"
    exit 1
fi

print_success "Environment configuration complete"
echo

# Ask user how to start
echo "How would you like to start the services?"
echo "1) Start both backend and frontend (recommended)"
echo "2) Start backend only"
echo "3) Start frontend only"
echo "4) Exit"
echo

read -p "Choose an option (1-4): " choice

case $choice in
    1)
        print_status "Starting both services..."
        echo
        print_status "🚀 Starting backend server..."
        echo "   Backend will be available at: http://localhost:8000"
        echo "   API docs at: http://localhost:8000/docs"
        echo
        print_status "🎨 Starting frontend server..."
        echo "   Frontend will be available at: http://localhost:3000"
        echo
        print_warning "Both servers will start in separate terminal windows"
        echo "Press Ctrl+C in each window to stop the servers"
        echo
        
        # Start backend in new terminal
        if command_exists gnome-terminal; then
            gnome-terminal -- bash -c "cd backend && python3 start.py; read -p 'Press Enter to close...'"
        elif command_exists osascript; then
            osascript -e "tell application \"Terminal\" to do script \"cd $(pwd)/backend && python3 start.py\""
        else
            echo "Starting backend in background..."
            cd backend && python3 start.py &
            BACKEND_PID=$!
            cd ..
        fi
        
        sleep 3
        
        # Start frontend in new terminal
        if command_exists gnome-terminal; then
            gnome-terminal -- bash -c "cd frontend && node start.js; read -p 'Press Enter to close...'"
        elif command_exists osascript; then
            osascript -e "tell application \"Terminal\" to do script \"cd $(pwd)/frontend && node start.js\""
        else
            echo "Starting frontend..."
            cd frontend && node start.js
        fi
        ;;
    2)
        print_status "Starting backend only..."
        cd backend && python3 start.py
        ;;
    3)
        print_status "Starting frontend only..."
        cd frontend && node start.js
        ;;
    4)
        print_status "Goodbye!"
        exit 0
        ;;
    *)
        print_error "Invalid option. Please choose 1-4."
        exit 1
        ;;
esac