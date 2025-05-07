import os
from pathlib import Path
import logging

def create_static_dirs():
    """
    Tạo các thư mục cần thiết cho static files nếu chưa tồn tại.
    
    Chức năng:
    - Kiểm tra và tạo thư mục uploads cho việc tải lên tệp
    - Kiểm tra và tạo thư mục temp cho các tệp tạm thời
    - Kiểm tra và tạo thư mục logs cho nhật ký ứng dụng
    - Sử dụng Path để xử lý đường dẫn an toàn đa nền tảng
    """
    static_dirs = ['static/uploads', 'static/temp', 'logs']

    for directory in static_dirs:
        path = Path(directory)
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            logging.info(f"Đã tạo thư mục: {directory}")
        else:
            logging.debug(f"Thư mục đã tồn tại: {directory}")
