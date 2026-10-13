"""
SocialPulse Backend - Main FastAPI Application
"""

import os
import sys
import logging
from datetime import datetime
from typing import Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

# Import API routers
from api.analyze import router as analyze_router
from api.reports import router as reports_router

# Import utilities
from utils.logging import setup_logging

# Load environment variables
load_dotenv()

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("Starting SocialPulse backend...")
    
    # Startup
    yield
    
    # Shutdown
    logger.info("Shutting down SocialPulse backend...")

# Create FastAPI app
app = FastAPI(
    title="SocialPulse API",
    description="AI-Powered Social Media Intelligence & Content Verification Platform",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/api/health")
async def health_check() -> Dict[str, Any]:
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "demo_mode": os.getenv("DEMO_MODE", "false").lower() == "true"
    }

# Include API routers
app.include_router(analyze_router, prefix="/api")
app.include_router(reports_router, prefix="/api")

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "type": "server_error"
        }
    )

# Startup message
@app.on_event("startup")
async def startup_event():
    """Log startup information"""
    demo_mode = os.getenv("DEMO_MODE", "false").lower() == "true"
    
    logger.info(f"SocialPulse API started")
    logger.info(f"Demo mode: {demo_mode}")
    
    # Check required environment variables
    required_vars = []
    if not demo_mode:
        if not os.getenv("GEMINI_API_KEY"):
            logger.warning("GEMINI_API_KEY not set - AI features may not work")
    
    # Check optional environment variables
    optional_vars = {
        "AWS_ACCESS_KEY_ID": "S3 storage",
        "SEARCH_API_KEY": "Web research",
        "LANGSMITH_API_KEY": "LangSmith monitoring"
    }
    
    for var, feature in optional_vars.items():
        if not os.getenv(var):
            logger.info(f"{var} not set - {feature} will use fallback")

if __name__ == "__main__":
    import uvicorn
    
    # Get configuration from environment
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    reload = os.getenv("RELOAD", "true").lower() == "true"
    
    logger.info(f"Starting server on {host}:{port}")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )