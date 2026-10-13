#!/usr/bin/env python3
"""
Test script to verify SocialPulse installation
"""

import os
import sys
import asyncio
from pathlib import Path

def test_python_version():
    """Test Python version"""
    print("Testing Python version...")
    if sys.version_info >= (3, 8):
        print(f"✓ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
        return True
    else:
        print(f"✗ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro} (requires 3.8+)")
        return False

def test_dependencies():
    """Test core dependencies"""
    print("Testing dependencies...")
    
    dependencies = {
        "fastapi": "FastAPI web framework",
        "uvicorn": "ASGI server",
        "pydantic": "Data validation",
        "python-dotenv": "Environment variables",
        "PIL": "Image processing",
        "google.generativeai": "Gemini AI (optional)",
        "langgraph": "LangGraph workflow",
        "httpx": "HTTP client",
        "boto3": "AWS SDK (optional)"
    }
    
    results = {}
    for module, description in dependencies.items():
        try:
            __import__(module)
            print(f"✓ {module} - {description}")
            results[module] = True
        except ImportError:
            print(f"✗ {module} - {description} (MISSING)")
            results[module] = False
    
    return results

def test_environment():
    """Test environment configuration"""
    print("Testing environment configuration...")
    
    # Check for .env file
    if Path(".env").exists():
        print("✓ .env file exists")
        
        # Load environment variables
        try:
            from dotenv import load_dotenv
            load_dotenv()
        except:
            pass
        
        # Check key variables
        env_vars = {
            "GEMINI_API_KEY": "Google Gemini API (required for full functionality)",
            "AWS_ACCESS_KEY_ID": "AWS access (optional - uses local storage)",
            "SEARCH_API_KEY": "Web search API (optional - uses demo data)",
            "DEMO_MODE": "Demo mode setting"
        }
        
        for var, description in env_vars.items():
            value = os.getenv(var)
            if value:
                masked_value = f"{value[:8]}..." if len(value) > 8 else "***"
                print(f"✓ {var} = {masked_value} - {description}")
            else:
                print(f"○ {var} - {description} (not set)")
    else:
        print("○ .env file not found (will use defaults)")

def test_file_structure():
    """Test file structure"""
    print("Testing file structure...")
    
    required_files = [
        "frontend/index.html",
        "frontend/style.css", 
        "frontend/script.js",
        "backend/main.py",
        "backend/models/schemas.py",
        "backend/api/analyze.py",
        "backend/api/reports.py",
        "requirements.txt"
    ]
    
    missing_files = []
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"✓ {file_path}")
        else:
            print(f"✗ {file_path} (MISSING)")
            missing_files.append(file_path)
    
    return len(missing_files) == 0

async def test_backend_startup():
    """Test backend can start (basic import test)"""
    print("Testing backend startup...")
    
    try:
        sys.path.append("backend")
        
        # Test core imports
        from models.schemas import AnalysisState
        print("✓ Data models import successfully")
        
        from services.storage_service import storage_service
        print("✓ Storage service imports successfully")
        
        from agents.content_agent import content_agent
        print("✓ Analysis agents import successfully")
        
        from graph.workflow import socialpulse_workflow
        print("✓ Workflow imports successfully")
        
        # Test FastAPI app creation
        from main import app
        print("✓ FastAPI app creates successfully")
        
        return True
        
    except Exception as e:
        print(f"✗ Backend startup test failed: {e}")
        return False

def create_sample_env():
    """Create sample .env file if it doesn't exist"""
    if not Path(".env").exists():
        print("\nCreating sample .env file...")
        
        with open(".env", "w") as f:
            f.write("""# SocialPulse Environment Configuration

# Required for full AI functionality
GEMINI_API_KEY=your_gemini_api_key_here

# Optional AWS S3 Storage (uses local storage if not provided)
# AWS_ACCESS_KEY_ID=your_aws_access_key
# AWS_SECRET_ACCESS_KEY=your_aws_secret_key
# AWS_REGION=us-east-1
# S3_BUCKET_NAME=socialpulse-bucket

# Optional Search API for research
# SEARCH_API_KEY=your_search_api_key

# Demo Mode (set to true if APIs unavailable)
DEMO_MODE=true

# Application Settings
LOG_LEVEL=INFO
MAX_IMAGE_SIZE_MB=10
""")
        
        print("✓ Sample .env file created")
        print("  Please edit .env and add your API keys")

async def main():
    """Main test routine"""
    print("SocialPulse Installation Test")
    print("=" * 40)
    
    all_passed = True
    
    # Run tests
    if not test_python_version():
        all_passed = False
    
    print()
    deps = test_dependencies()
    core_deps = ["fastapi", "uvicorn", "pydantic", "python-dotenv"]
    if not all(deps.get(dep, False) for dep in core_deps):
        all_passed = False
    
    print()
    test_environment()
    
    print()
    if not test_file_structure():
        all_passed = False
    
    print()
    if not await test_backend_startup():
        all_passed = False
    
    print()
    print("=" * 40)
    
    if all_passed:
        print("✓ All tests passed! SocialPulse is ready to run.")
        print("\nTo start the application:")
        print("1. Backend:  python start_backend.py")
        print("2. Frontend: python start_frontend.py")
        print("3. Open:     http://localhost:8080")
    else:
        print("✗ Some tests failed. Please check the issues above.")
        print("\nCommon fixes:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Configure .env file with your API keys")
        print("3. Ensure Python 3.8+ is installed")
    
    print()
    create_sample_env()

if __name__ == "__main__":
    asyncio.run(main())