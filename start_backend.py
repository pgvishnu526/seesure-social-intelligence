#!/usr/bin/env python3
"""
Startup script for SocialPulse backend
"""

import os
import sys
import subprocess
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("Error: Python 3.8 or higher is required")
        sys.exit(1)
    print(f"✓ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")

def check_env_file():
    """Check if .env file exists"""
    if not Path(".env").exists():
        print("Warning: .env file not found")
        print("Please copy .env.example to .env and configure your API keys")
        
        # Check for required environment variables
        required_vars = ["GEMINI_API_KEY"]
        missing_vars = []
        
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            print(f"Missing required environment variables: {', '.join(missing_vars)}")
            print("The application will run in DEMO mode")
            os.environ["DEMO_MODE"] = "true"
        
        return False
    
    print("✓ .env file found")
    return True

def install_dependencies():
    """Install Python dependencies"""
    try:
        print("Installing dependencies...")
        subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ], check=True, capture_output=True)
        print("✓ Dependencies installed")
    except subprocess.CalledProcessError as e:
        print(f"Error installing dependencies: {e}")
        print("Please run: pip install -r requirements.txt")
        return False
    return True

def create_data_directory():
    """Create data directory for local storage"""
    data_dir = Path("backend/data")
    data_dir.mkdir(parents=True, exist_ok=True)
    print("✓ Data directory created")

def start_server():
    """Start the FastAPI server"""
    print("\nStarting SocialPulse backend server...")
    print("Server will be available at: http://localhost:8000")
    print("API documentation at: http://localhost:8000/docs")
    print("\nPress Ctrl+C to stop the server\n")
    
    os.chdir("backend")
    
    try:
        subprocess.run([
            sys.executable, "main.py"
        ])
    except KeyboardInterrupt:
        print("\n\nServer stopped.")
    except Exception as e:
        print(f"Error starting server: {e}")

def main():
    """Main startup routine"""
    print("SocialPulse Backend Startup")
    print("=" * 30)
    
    # Check requirements
    check_python_version()
    check_env_file()
    create_data_directory()
    
    # Ask user about dependency installation
    try:
        import fastapi
        import uvicorn
        print("✓ Core dependencies available")
    except ImportError:
        print("Installing missing dependencies...")
        if not install_dependencies():
            sys.exit(1)
    
    # Start server
    start_server()

if __name__ == "__main__":
    main()