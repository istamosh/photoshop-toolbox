"""Utility functions for image processing and other common operations."""

import os
from pathlib import Path
from datetime import datetime


def get_image_files(directory):
    """Get all image files in a directory recursively."""
    image_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".gif"}
    for path in Path(directory).rglob("*"):
        if path.suffix.lower() in image_extensions:
            yield path


def format_file_size(size_in_bytes):
    """Format file size in human readable format."""
    for unit in ["B", "KB", "MB", "GB"]:
        if size_in_bytes < 1024.0:
            return f"{size_in_bytes:.2f} {unit}"
        size_in_bytes /= 1024.0
    return f"{size_in_bytes:.2f} TB"


def get_modified_date(file_path):
    """Get file modification date in a formatted string."""
    timestamp = os.path.getmtime(file_path)
    return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
