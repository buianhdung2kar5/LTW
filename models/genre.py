from bson.objectid import ObjectId
from . import genres_collection, serialize_id

class Genre:
    @staticmethod
    def get_all():
        try:
            # Handle possible generator/iterator errors
            results = list(genres_collection.find())
            return [serialize_id(genre) for genre in results]
        except Exception as e:
            print(f"Error in Genre.get_all(): {str(e)}")
            return []  # Return empty list on error
    
    @staticmethod
    def get_by_id(genre_id):
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
            print(f"Error in Genre.get_by_id(): {str(e)}")
            return None
    
    @staticmethod
    def get_by_slug(slug):
        try:
            genre = genres_collection.find_one({"slug": slug})
            return serialize_id(genre) if genre else None
        except Exception as e:
            print(f"Error in Genre.get_by_slug(): {str(e)}")
            return None
    
    @staticmethod
    def get_by_name(name):
        try:
            genre = genres_collection.find_one({"name": name})
            return serialize_id(genre) if genre else None
        except Exception as e:
            print(f"Error in Genre.get_by_name(): {str(e)}")
            return None
    
    @staticmethod
    def create(data):
        # Generate a new id if not provided
        if 'id' not in data:
            max_id = genres_collection.find_one(sort=[("id", -1)])
            data['id'] = 1 if max_id is None else max_id.get('id', 0) + 1
            
        result = genres_collection.insert_one(data)
        return serialize_id({**data, "_id": result.inserted_id})
    
    @staticmethod
    def get_films(genre_id):
        from .film import Film
        return Film.get_by_genre(genre_id)
    
    @staticmethod
    def load_genres_from_database():
        """Get genres directly from MongoDB film-users database"""
        try:
            # Check if genres exist in the database
            genres_count = genres_collection.count_documents({})
            if genres_count > 0:
                print(f"Found {genres_count} genres in film-users database.")
                return True
                
            print("No genres found in film-users database. Creating default genres...")
            # Create some default genres if none exist
            return Genre.create_default_genres()
        except Exception as e:
            print(f"Error loading genres from database: {str(e)}")
            return False
    
    @staticmethod
    def create_default_genres():
        """Create default genres if none exist in the database"""
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
            
            print(f"[SUCCESS] Created {len(default_genres)} default genres in film-users database")
            return True
        except Exception as e:
            print(f"Error creating default genres: {str(e)}")
            return False
    
    @staticmethod
    def find_duplicate_ids():
        """Find genres with duplicate IDs"""
        try:
            pipeline = [
                {"$group": {"_id": "$id", "count": {"$sum": 1}, "names": {"$push": "$name"}}},
                {"$match": {"count": {"$gt": 1}}},
                {"$sort": {"count": -1}}
            ]
            
            duplicate_ids = list(genres_collection.aggregate(pipeline))
            return duplicate_ids
        except Exception as e:
            print(f"Error finding duplicate genre IDs: {str(e)}")
            return []
