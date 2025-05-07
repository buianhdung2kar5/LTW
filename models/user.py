from datetime import datetime
from functools import lru_cache
from . import users_collection, serialize_id

class User:
    @staticmethod
    @lru_cache(maxsize=128)
    def get_by_username(username):
        """Get user by username with caching for frequently accessed users"""
        user = users_collection.find_one({"username": username})
        return serialize_id(user) if user else None
    
    @staticmethod
    def create(data):
        """Create a new user with optimized fields"""
        # Set created_at timestamp in one operation
        data['created_at'] = data['registerDate'] = datetime.now()
        result = users_collection.insert_one(data)
        return serialize_id({**data, "_id": result.inserted_id})
    
    @staticmethod
    def authenticate(username, password):
        """Authenticate user with optimized checks"""
        user = User.get_by_username(username)
        return user if user and user.get('password') == password else None
