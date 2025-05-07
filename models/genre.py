from bson.objectid import ObjectId
from functools import lru_cache
from . import genres_collection, serialize_id

class Genre:
    @staticmethod
    @lru_cache(maxsize=100)
    def get_all():
        """Lấy tất cả thể loại phim với caching
        
        Chức năng:
        - Sử dụng lru_cache để lưu trữ kết quả và tối ưu hiệu suất
        - Xử lý lỗi và trả về danh sách trống nếu có vấn đề
        - Chuyển đổi ObjectId sang string thông qua serialize_id
        
        Returns:
            list: Danh sách tất cả thể loại phim đã được serialize
        """
        try:
            results = list(genres_collection.find())
            return [serialize_id(genre) for genre in results]
        except Exception as e:
            print(f"Lỗi trong Genre.get_all(): {str(e)}")
            return []
    
    @staticmethod
    @lru_cache(maxsize=256)
    def get_by_id(genre_id):
        """Lấy thể loại phim theo ID với caching
        
        Chức năng:
        - Sử dụng lru_cache để lưu trữ kết quả và tăng tốc truy vấn
        - Hỗ trợ tìm kiếm theo ID số hoặc ObjectId
        - Xử lý lỗi và trả về None nếu không tìm thấy
        
        Args:
            genre_id: ID của thể loại (số nguyên hoặc chuỗi)
            
        Returns:
            dict: Thông tin thể loại đã được serialize, hoặc None nếu không tìm thấy
        """
        try:
            if isinstance(genre_id, int):
                genre = genres_collection.find_one({"id": genre_id})
            else:
                try:
                    genre = genres_collection.find_one({"_id": ObjectId(genre_id)})
                except:
                    genre = None
            return serialize_id(genre) if genre else None
        except Exception as e:
            print(f"Lỗi trong Genre.get_by_id(): {str(e)}")
            return None
    
    @staticmethod
    @lru_cache(maxsize=256)
    def get_by_slug(slug):
        """Lấy thể loại phim theo slug với caching
        
        Chức năng:
        - Sử dụng lru_cache để lưu trữ kết quả và tăng tốc truy vấn
        - Tìm kiếm thể loại dựa trên trường slug (URL-friendly name)
        - Xử lý lỗi và trả về None nếu không tìm thấy
        
        Args:
            slug (str): Slug của thể loại
            
        Returns:
            dict: Thông tin thể loại đã được serialize, hoặc None nếu không tìm thấy
        """
        try:
            genre = genres_collection.find_one({"slug": slug})
            return serialize_id(genre) if genre else None
        except Exception as e:
            print(f"Lỗi trong Genre.get_by_slug(): {str(e)}")
            return None
    
    @staticmethod
    def get_by_name(name):
        """Lấy thể loại phim theo tên
        
        Chức năng:
        - Tìm kiếm thể loại dựa trên tên đầy đủ
        - Xử lý lỗi và trả về None nếu không tìm thấy
        
        Args:
            name (str): Tên của thể loại
            
        Returns:
            dict: Thông tin thể loại đã được serialize, hoặc None nếu không tìm thấy
        """
        try:
            genre = genres_collection.find_one({"name": name})
            return serialize_id(genre) if genre else None
        except Exception as e:
            print(f"Lỗi trong Genre.get_by_name(): {str(e)}")
            return None
    
    @staticmethod
    def create(data):
        """Tạo thể loại phim mới với ID tự động tăng
        
        Chức năng:
        - Tự động tạo ID nếu không được cung cấp
        - Tìm ID lớn nhất hiện có và tăng thêm 1 để tạo ID mới
        - Lưu thể loại vào database và trả về thể loại đã được tạo với ID
        
        Args:
            data (dict): Dữ liệu thể loại cần tạo
            
        Returns:
            dict: Thể loại đã được tạo với ID và _id đã serialize
        """
        if 'id' not in data:
            max_id = genres_collection.find_one(sort=[("id", -1)])
            data['id'] = 1 if max_id is None else max_id.get('id', 0) + 1
        result = genres_collection.insert_one(data)
        return serialize_id({**data, "_id": result.inserted_id})
    
    @staticmethod
    def get_films(genre_id):
        """Lấy danh sách phim theo ID thể loại
        
        Chức năng:
        - Sử dụng Film.get_by_genre để lấy danh sách phim
        - Import Film từ module film để tránh import vòng tròn
        
        Args:
            genre_id: ID của thể loại
            
        Returns:
            list: Danh sách phim thuộc thể loại
        """
        from .film import Film
        return Film.get_by_genre(genre_id)
    
    @staticmethod
    def load_genres_from_database():
        """Lấy thể loại phim trực tiếp từ cơ sở dữ liệu film-users
        
        Chức năng:
        - Kiểm tra xem thể loại đã tồn tại trong cơ sở dữ liệu hay chưa
        - Nếu không có thể loại nào, tạo các thể loại mặc định
        
        Returns:
            bool: True nếu thành công, False nếu có lỗi
        """
        try:
            genres_count = genres_collection.count_documents({})
            if genres_count > 0:
                print(f"Đã tìm thấy {genres_count} thể loại trong cơ sở dữ liệu film-users.")
                return True
                
            print("Không tìm thấy thể loại nào trong cơ sở dữ liệu film-users. Đang tạo các thể loại mặc định...")
            return Genre.create_default_genres()
        except Exception as e:
            print(f"Lỗi khi tải thể loại từ cơ sở dữ liệu: {str(e)}")
            return False
    
    @staticmethod
    def create_default_genres():
        """Tạo các thể loại mặc định nếu không tồn tại trong cơ sở dữ liệu
        
        Chức năng:
        - Tạo danh sách các thể loại mặc định
        - Lưu các thể loại vào cơ sở dữ liệu
        - Tạo index cho slug và name
        
        Returns:
            bool: True nếu thành công, False nếu có lỗi
        """
        try:
            default_genres = [
                {"name": "Hành động", "slug": "hanh-dong", "description": "Phim hành động"},
                {"name": "Tình cảm", "slug": "tinh-cam", "description": "Phim tình cảm"},
                {"name": "Kinh dị", "slug": "kinh-di", "description": "Phim kinh dị"},
                {"name": "Hài hước", "slug": "hai-huoc", "description": "Phim hài hước"},
                {"name": "Anime", "slug": "anime", "description": "Phim hoạt hình Nhật Bản"},
                {"name": "Viễn tưởng", "slug": "vien-tuong", "description": "Phim viễn tưởng"},
                {"name": "Tâm lý", "slug": "tam-ly", "description": "Phim tâm lý"},
                {"name": "Lịch sử", "slug": "lich-su", "description": "Phim lịch sử"},
                {"name": "Chiến tranh", "slug": "chien-tranh", "description": "Phim chiến tranh"},
                {"name": "Võ thuật", "slug": "vo-thuat", "description": "Phim võ thuật"},
                {"name": "Cổ trang", "slug": "co-trang", "description": "Phim cổ trang"},
                {"name": "Thần thoại", "slug": "than-thoai", "description": "Phim thần thoại"},
                {"name": "Phiêu lưu", "slug": "phieu-luu", "description": "Phim phiêu lưu"},
                {"name": "Gia đình", "slug": "gia-dinh", "description": "Phim gia đình"},
                {"name": "Hình sự", "slug": "hinh-su", "description": "Phim hình sự"},
                {"name": "Trinh thám", "slug": "trinh-tham", "description": "Phim trinh thám"}
            ]
            
            for i, genre in enumerate(default_genres, 1):
                genre["id"] = i
                genres_collection.insert_one(genre)
                
            genres_collection.create_index("slug", unique=True)
            genres_collection.create_index("name")
            
            print(f"[THÀNH CÔNG] Đã tạo {len(default_genres)} thể loại mặc định trong cơ sở dữ liệu film-users")
            return True
        except Exception as e:
            print(f"Lỗi khi tạo các thể loại mặc định: {str(e)}")
            return False
    
    @staticmethod
    def find_duplicate_ids():
        """Tìm các thể loại có ID trùng lặp
        
        Chức năng:
        - Sử dụng pipeline để nhóm các thể loại theo ID
        - Tìm các ID có số lượng lớn hơn 1
        - Sắp xếp theo số lượng giảm dần
        
        Returns:
            list: Danh sách các ID trùng lặp với thông tin chi tiết
        """
        try:
            pipeline = [
                {"$group": {"_id": "$id", "count": {"$sum": 1}, "names": {"$push": "$name"}}},
                {"$match": {"count": {"$gt": 1}}},
                {"$sort": {"count": -1}}
            ]
            
            duplicate_ids = list(genres_collection.aggregate(pipeline))
            return duplicate_ids
        except Exception as e:
            print(f"Lỗi khi tìm các ID thể loại trùng lặp: {str(e)}")
            return []
