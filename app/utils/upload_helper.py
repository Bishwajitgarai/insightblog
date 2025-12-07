import os
from pathlib import Path
from typing import Optional


def get_user_post_upload_path(user_id: int, post_id: int, filename: str) -> tuple[str, str]:
    """
    Get the file path and URL for a post upload.
    
    Args:
        user_id: The user's ID
        post_id: The post's ID
        filename: The original filename with extension
        
    Returns:
        tuple: (file_path, url_path)
    """
    # Create directory structure: user_{id}/post/{post_id}/objects
    upload_dir = Path("static") / "uploads" / f"user_{user_id}" / "post" / str(post_id) / "objects"
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = upload_dir / filename
    url_path = f"/static/uploads/user_{user_id}/post/{post_id}/objects/{filename}"
    
    return str(file_path), url_path


def get_user_profile_upload_path(user_id: int, filename: str) -> tuple[str, str]:
    """
    Get the file path and URL for a profile upload.
    
    Args:
        user_id: The user's ID
        filename: The original filename with extension
        
    Returns:
        tuple: (file_path, url_path)
    """
    # Create directory structure: user_{id}/profile/objects
    upload_dir = Path("static") / "uploads" / f"user_{user_id}" / "profile" / "objects"
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = upload_dir / filename
    url_path = f"/static/uploads/user_{user_id}/profile/objects/{filename}"
    
    return str(file_path), url_path


def ensure_upload_directories():
    """
    Ensure the base uploads directory exists.
    """
    upload_dir = Path("static") / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
