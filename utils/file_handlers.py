import os
from pathlib import Path
import logging

def create_static_dirs():
    """
    Tạo các thư mục cần thiết cho static files nếu chưa tồn tại.
    """
    static_dirs = ['static/uploads', 'static/temp', 'logs']

    for directory in static_dirs:
        path = Path(directory)
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            logging.info(f"Đã tạo thư mục: {directory}")
        else:
            logging.debug(f"Thư mục đã tồn tại: {directory}")
