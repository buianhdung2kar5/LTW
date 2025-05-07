import os
import logging

logger = logging.getLogger(__name__)

def create_static_files():
    """Khởi tạo các tệp tĩnh cần thiết cho ứng dụng
    
    Chức năng:
    - Tạo các thư mục cần thiết cho tệp tĩnh (css, js, images, uploads)
    - Tạo avatar mặc định nếu chưa tồn tại
    """
    # Tạo tất cả các thư mục cần thiết cùng lúc
    directories = ['static/css', 'static/js', 'static/images', 'static/uploads']
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        logger.info(f"Đã đảm bảo thư mục tồn tại: {directory}")
    
    # Tạo avatar mặc định nếu cần
    default_avatar = 'static/images/avatar_default.png'
    if not os.path.exists(default_avatar):
        try:
            with open(default_avatar, 'w') as f:
                f.write("placeholder for avatar")
            logger.info(f"Đã tạo avatar mặc định tại {default_avatar}")
        except Exception as e:
            logger.error(f"Lỗi khi tạo avatar mặc định: {str(e)}")
