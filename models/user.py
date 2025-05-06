from datetime import datetime
from . import users_collection, serialize_id

class User:
    @staticmethod
    def get_by_username(username):
        user = users_collection.find_one({"username": username})
        return serialize_id(user) if user else None
    
    @staticmethod
    def create(data):
        data['created_at'] = datetime.now()
        result = users_collection.insert_one(data)
        return serialize_id({**data, "_id": result.inserted_id})
    
    @staticmethod
    def authenticate(username, password):
        user = User.get_by_username(username)
        if user and user.get('password') == password:
            return user
        return None
