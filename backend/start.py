#!/usr/bin/env python3
"""
Startup script for the Roof Design Validation Backend
"""

import os
import sys
import subprocess
from pathlib import Path
from dotenv import load_dotenv

def check_environment():
    """Check if environment is properly configured"""
    
    print("🔍 Checking environment configuration...")
    
    # Check if .env file exists
    env_file = Path('.env')
    if not env_file.exists():
        print(".env file not found. Creating from template...")
        
        # Create .env from template
        env_template = """# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_API_BASE=https://api.openai.com/v1
OPENAI_MAIN_MODEL=gpt-5
OPENAI_SUMMARY_MODEL=gpt-5-mini

# Server Configuration  
HOST=127.0.0.1
PORT=8000
DEBUG=true
ENVIRONMENT=development

# CORS Configuration
ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# Cost Tracking
TRACK_API_COSTS=true
LOG_LEVEL=INFO"""
        
        with open('.env', 'w') as f:
            f.write(env_template)
        
        print("Created .env file from template")
        print("Please edit .env file and add your OpenAI API key")
        return False
    
    # Check if API key is set
    load_dotenv()
    
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key or api_key == 'your_openai_api_key_here':
        print("OPENAI_API_KEY not set in .env file")
        print("Please edit the .env file and add your OpenAI API key")
        return False
    
    print("Environment configuration looks good")
    return True

def install_dependencies():
    """Install Python dependencies"""
    
    print("Installing dependencies...")
    
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], 
                      check=True, capture_output=True)
        print("Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Failed to install dependencies: {e}")
        return False

def start_server():
    """Start the FastAPI server"""
    
    print("Starting Roof Design Validation API server...")
    print("API will be available at: http://localhost:8000")
    print("API documentation: http://localhost:8000/docs")
    print("Press Ctrl+C to stop the server")
    print("-" * 50)
    
    try:
        # Import and run server
        import uvicorn
        from config import settings
        
        uvicorn.run(
            "main:app",
            host=settings.host,
            port=settings.port,
            reload=settings.debug,
            log_level=settings.log_level.lower()
        )
    except KeyboardInterrupt:
        print("\n Server stopped by user")
    except Exception as e:
        print(f"Server failed to start: {e}")

def main():
    """Main startup function"""
    
    print("Roof Design Validation Backend")
    print("=" * 40)
    
    # Change to backend directory if needed
    backend_dir = Path(__file__).parent
    os.chdir(backend_dir)
    
    # Check environment
    if not check_environment():
        sys.exit(1)
    
    # Skip automatic dependency installation for conda environments
    print("Skipping automatic dependency installation...")
    print("Make sure you have installed dependencies manually with conda/pip")
    
    # Start server
    start_server()

if __name__ == "__main__":
    main()