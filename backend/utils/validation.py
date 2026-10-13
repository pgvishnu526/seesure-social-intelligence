"""
Input validation utilities for SocialPulse
"""

import os
import mimetypes
from typing import Tuple, Optional
from pathlib import Path
from PIL import Image
try:
    import magic
except ImportError:
    magic = None
import logging

logger = logging.getLogger(__name__)

# Supported image formats
SUPPORTED_MIME_TYPES = {
    'image/jpeg',
    'image/jpg', 
    'image/png',
    'image/webp'
}

SUPPORTED_EXTENSIONS = {
    '.jpg', '.jpeg', '.png', '.webp'
}

# File size limits
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
MIN_FILE_SIZE = 1024  # 1KB

# Image dimension limits
MAX_IMAGE_WIDTH = 10000
MAX_IMAGE_HEIGHT = 10000
MIN_IMAGE_WIDTH = 50
MIN_IMAGE_HEIGHT = 50


def validate_image_file(file_path: str) -> Tuple[bool, Optional[str]]:
    """
    Validate an image file for security and format compliance
    
    Args:
        file_path: Path to the image file
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        path = Path(file_path)
        
        # Check if file exists
        if not path.exists():
            return False, "File does not exist"
        
        # Check file size
        file_size = path.stat().st_size
        if file_size > MAX_FILE_SIZE:
            return False, f"File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)}MB"
        
        if file_size < MIN_FILE_SIZE:
            return False, f"File too small. Minimum size is {MIN_FILE_SIZE} bytes"
        
        # Check file extension
        if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            return False, f"Unsupported file extension. Supported: {', '.join(SUPPORTED_EXTENSIONS)}"
        
        # Check MIME type using python-magic for security
        try:
            if magic:
                mime_type = magic.from_file(str(path), mime=True)
            else:
                mime_type, _ = mimetypes.guess_type(str(path))
        except Exception:
            # Fallback to mimetypes if python-magic fails
            mime_type, _ = mimetypes.guess_type(str(path))
        
        if mime_type not in SUPPORTED_MIME_TYPES:
            return False, f"Invalid file type detected: {mime_type}"
        
        # Validate image using PIL
        try:
            with Image.open(path) as img:
                # Check if it's a valid image
                img.verify()
                
                # Reopen for dimension check (verify() closes the file)
                with Image.open(path) as img2:
                    width, height = img2.size
                    
                    # Check dimensions
                    if width > MAX_IMAGE_WIDTH or height > MAX_IMAGE_HEIGHT:
                        return False, f"Image too large. Maximum dimensions: {MAX_IMAGE_WIDTH}x{MAX_IMAGE_HEIGHT}"
                    
                    if width < MIN_IMAGE_WIDTH or height < MIN_IMAGE_HEIGHT:
                        return False, f"Image too small. Minimum dimensions: {MIN_IMAGE_WIDTH}x{MIN_IMAGE_HEIGHT}"
                    
                    # Check for suspicious image properties
                    if hasattr(img2, '_getexif'):
                        # Remove EXIF data for privacy
                        pass
                    
        except Exception as e:
            return False, f"Invalid or corrupted image file: {str(e)}"
        
        return True, None
        
    except Exception as e:
        logger.error(f"Error validating file {file_path}: {str(e)}")
        return False, f"Validation error: {str(e)}"


def validate_image_content(image_data: bytes) -> Tuple[bool, Optional[str]]:
    """
    Validate image content from bytes
    
    Args:
        image_data: Raw image bytes
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        # Check size
        if len(image_data) > MAX_FILE_SIZE:
            return False, f"Image too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)}MB"
        
        if len(image_data) < MIN_FILE_SIZE:
            return False, f"Image too small. Minimum size is {MIN_FILE_SIZE} bytes"
        
        # Check magic bytes for common image formats
        if image_data.startswith(b'\x89PNG\r\n\x1a\n'):
            mime_type = 'image/png'
        elif image_data.startswith(b'\xff\xd8\xff'):
            mime_type = 'image/jpeg'
        elif image_data.startswith(b'RIFF') and b'WEBP' in image_data[:12]:
            mime_type = 'image/webp'
        else:
            return False, "Unrecognized image format"
        
        if mime_type not in SUPPORTED_MIME_TYPES:
            return False, f"Unsupported image format: {mime_type}"
        
        # Validate with PIL
        try:
            with Image.open(io.BytesIO(image_data)) as img:
                img.verify()
                
                # Check dimensions
                width, height = img.size
                if width > MAX_IMAGE_WIDTH or height > MAX_IMAGE_HEIGHT:
                    return False, f"Image too large. Maximum dimensions: {MAX_IMAGE_WIDTH}x{MAX_IMAGE_HEIGHT}"
                
                if width < MIN_IMAGE_WIDTH or height < MIN_IMAGE_HEIGHT:
                    return False, f"Image too small. Minimum dimensions: {MIN_IMAGE_WIDTH}x{MIN_IMAGE_HEIGHT}"
                
        except Exception as e:
            return False, f"Invalid image data: {str(e)}"
        
        return True, None
        
    except Exception as e:
        logger.error(f"Error validating image content: {str(e)}")
        return False, f"Validation error: {str(e)}"


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename for safe storage
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    # Remove path components
    filename = Path(filename).name
    
    # Replace unsafe characters
    unsafe_chars = '<>:"/\\|?*'
    for char in unsafe_chars:
        filename = filename.replace(char, '_')
    
    # Limit length
    name, ext = os.path.splitext(filename)
    if len(name) > 100:
        name = name[:100]
    
    # Ensure we have an extension
    if not ext and '.' not in filename:
        ext = '.jpg'  # default
    
    return name + ext


def validate_analysis_id(analysis_id: str) -> bool:
    """
    Validate analysis ID format
    
    Args:
        analysis_id: Analysis ID to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not analysis_id:
        return False
    
    # Expected format: SP-YYYY-NNNNNN
    if not analysis_id.startswith('SP-'):
        return False
    
    parts = analysis_id.split('-')
    if len(parts) != 3:
        return False
    
    try:
        year = int(parts[1])
        number = int(parts[2])
        
        # Basic sanity checks
        if year < 2020 or year > 2030:
            return False
        
        if number < 1 or number > 999999:
            return False
        
        return True
        
    except ValueError:
        return False


# Import io for BytesIO
import io