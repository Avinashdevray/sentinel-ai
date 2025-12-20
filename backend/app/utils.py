import base64
from io import BytesIO
from PIL import Image
from typing import Optional


def encode_image_to_base64(image_bytes: bytes) -> str:
    """
    Encode image bytes to base64 string
    
    Args:
        image_bytes: Raw image bytes
        
    Returns:
        Base64 encoded string
    """
    return base64.b64encode(image_bytes).decode('utf-8')


def decode_base64_to_image(base64_string: str) -> Image.Image:
    """
    Decode base64 string to PIL Image
    
    Args:
        base64_string: Base64 encoded image string
        
    Returns:
        PIL Image object
    """
    image_bytes = base64.b64decode(base64_string)
    return Image.open(BytesIO(image_bytes))


def resize_image_if_needed(image_bytes: bytes, max_size: int = 1024) -> bytes:
    """
    Resize image if it's too large to reduce API costs
    
    Args:
        image_bytes: Raw image bytes
        max_size: Maximum dimension (width or height)
        
    Returns:
        Resized image bytes
    """
    img = Image.open(BytesIO(image_bytes))
    
    # Check if resize is needed
    if max(img.size) <= max_size:
        return image_bytes
    
    # Calculate new size maintaining aspect ratio
    ratio = max_size / max(img.size)
    new_size = tuple(int(dim * ratio) for dim in img.size)
    
    # Resize and save
    img = img.resize(new_size, Image.Resampling.LANCZOS)
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    return buffer.getvalue()


def format_log_message(level: str, message: str, details: Optional[dict] = None) -> dict:
    """
    Format a log message for WebSocket transmission
    
    Args:
        level: Log level (INFO, WARNING, ERROR, etc.)
        message: Log message
        details: Optional additional details
        
    Returns:
        Formatted log dictionary
    """
    log = {
        "level": level,
        "message": message,
    }
    if details:
        log["details"] = details
    return log
