"""
Logging configuration for SocialPulse
"""

import os
import logging
import logging.handlers
from pathlib import Path


def setup_logging():
    """Setup application logging"""
    
    # Create logs directory
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Get log level from environment
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, log_level, logging.INFO),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            # Console handler
            logging.StreamHandler(),
            
            # File handler with rotation
            logging.handlers.RotatingFileHandler(
                log_dir / "socialpulse.log",
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5
            )
        ]
    )
    
    # Set specific logger levels
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("fastapi").setLevel(logging.INFO)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("boto3").setLevel(logging.WARNING)
    logging.getLogger("botocore").setLevel(logging.WARNING)
    
    # Disable httpx debug logs
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the given name"""
    return logging.getLogger(name)


def log_analysis_start(analysis_id: str, logger: logging.Logger):
    """Log analysis start"""
    logger.info(f"Analysis {analysis_id}: Started")


def log_analysis_step(analysis_id: str, step: str, logger: logging.Logger):
    """Log analysis step"""
    logger.info(f"Analysis {analysis_id}: {step}")


def log_analysis_complete(analysis_id: str, duration: float, logger: logging.Logger):
    """Log analysis completion"""
    logger.info(f"Analysis {analysis_id}: Completed in {duration:.2f}s")


def log_analysis_error(analysis_id: str, error: str, logger: logging.Logger):
    """Log analysis error"""
    logger.error(f"Analysis {analysis_id}: Error - {error}")


def sanitize_for_logging(text: str, max_length: int = 100) -> str:
    """Sanitize text for logging (remove sensitive info, truncate)"""
    if not text:
        return "N/A"
    
    # Remove potential sensitive information
    sanitized = text.replace('\n', ' ').replace('\r', ' ')
    
    # Truncate if too long
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length] + "..."
    
    return sanitized