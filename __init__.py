# File khởi tạo trống để biến thư mục thành một gói Python đúng cách
from .models import Film, Genre, User

# Xuất các lớp cần thiết để có thể import từ gói
__all__ = ['Film', 'Genre', 'User']
