"""
File service for handling static file operations.
"""
from pathlib import Path
from typing import Tuple, Optional
from config import FRONTEND_DIR


def get_content_type(filename: str) -> str:
    """
    Determine the content type based on file extension.
    
    Args:
        filename: The name of the file
        
    Returns:
        The MIME type string
    """
    if filename.endswith('.js'):
        return 'application/javascript'
    elif filename.endswith('.css'):
        return 'text/css'
    elif filename.endswith('.html'):
        return 'text/html'
    elif filename.endswith('.png'):
        return 'image/png'
    elif filename.endswith('.jpg') or filename.endswith('.jpeg'):
        return 'image/jpeg'
    elif filename.endswith('.gif'):
        return 'image/gif'
    elif filename.endswith('.svg'):
        return 'image/svg+xml'
    else:
        return 'text/plain'


def get_static_file_content(filename: str) -> Optional[Tuple[bytes, str]]:
    """
    Read static file content from the frontend directory.
    
    Args:
        filename: The relative path to the file from frontend directory
        
    Returns:
        Tuple of (content, media_type) or None if file not found
    """
    file_path = FRONTEND_DIR / filename
    
    if not file_path.exists() or not file_path.is_file():
        return None
    
    media_type = get_content_type(filename)
    
    # Determine read mode based on file type
    if filename.endswith(('.png', '.jpg', '.jpeg', '.gif')):
        mode = 'rb'
    else:
        mode = 'r'
    
    with open(file_path, mode) as f:
        content = f.read()
    
    # Convert text to bytes if needed
    if isinstance(content, str):
        content = content.encode('utf-8')
    
    return content, media_type


def get_index_html() -> str:
    """
    Read and return the index.html file content.
    
    Returns:
        The HTML content as a string
    """
    index_path = FRONTEND_DIR / "index.html"
    with open(index_path, 'r') as f:
        return f.read()