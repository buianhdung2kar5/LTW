from pymongo import MongoClient
from bson.objectid import ObjectId
import os
import ssl

# Connect directly to MongoDB Atlas film-users database
try:
    # Use only MongoDB Atlas with simplified connection
    uri = os.environ.get('MONGO_URI', "mongodb+srv://kiwi:trang%402005@film-users.10h2w59.mongodb.net/?retryWrites=true&w=majority")
    dbname = "film-users"  # Explicitly use film-users database
    
    # Create MongoDB client with improved connection settings and explicit SSL context
    mongo_client = MongoClient(
        uri,
        serverSelectionTimeoutMS=5000,
        connectTimeoutMS=5000,
        socketTimeoutMS=10000,
        maxPoolSize=50,
        retryWrites=True,
        ssl=True,
        tlsAllowInvalidCertificates=True  # Updated from ssl_cert_reqs=ssl.CERT_NONE
    )
    
    # Test connection immediately
    mongo_client.admin.command('ping')
    print("[SUCCESS] MongoDB Atlas connection successful!")
except Exception as e:
    print(f"[ERROR] MongoDB Atlas connection error: {str(e)}")
    # Create dummy collections to prevent errors
    class DummyCollection:
        def find_one(self, *args, **kwargs): 
            return None
            
        def find(self, *args, **kwargs): 
            class DummyCursor:
                def __init__(self):
                    self.data = []
                    
                def sort(self, *args): 
                    return self
                    
                def limit(self, *args): 
                    return self
                    
                def skip(self, *args): 
                    return self
                    
                # Make cursor iterable
                def __iter__(self):
                    return iter(self.data)
                    
                # Make cursor list-like
                def __getitem__(self, key):
                    return self.data[key] if 0 <= key < len(self.data) else None
                    
                # Add length method
                def __len__(self):
                    return 0
            
            return DummyCursor()
            
        def count_documents(self, *args, **kwargs): 
            return 0
            
        def insert_one(self, *args, **kwargs): 
            class DummyResult:
                @property
                def inserted_id(self):
                    return 'dummy_id'
            return DummyResult()
            
        def update_one(self, *args, **kwargs): 
            return None
            
        def delete_one(self, *args, **kwargs): 
            return None
            
        def create_index(self, *args, **kwargs): 
            return None
            
        def aggregate(self, *args, **kwargs):
            return []
    
    # Create empty dummy client and db
    mongo_client = None
    db = None
    films_collection = DummyCollection()
    genres_collection = DummyCollection()
    users_collection = DummyCollection()

# Get database and collections
try:
    # Get film-users database
    db = mongo_client["film-users"]
    
    # Define collections
    films_collection = db.films
    genres_collection = db.genres
    users_collection = db.users
    
    print(f"[INFO] Connected to collections: films ({films_collection.count_documents({})} documents), "
          f"genres ({genres_collection.count_documents({})} documents)")
except Exception as e:
    print(f"[ERROR] Failed to access MongoDB collections: {str(e)}")
    # Create dummy instances
    db = None
    films_collection = DummyCollection()
    genres_collection = DummyCollection()
    users_collection = DummyCollection()

# Helper function to serialize ObjectId to string
def serialize_id(obj):
    if isinstance(obj, dict) and '_id' in obj and isinstance(obj['_id'], ObjectId):
        obj['_id'] = str(obj['_id'])
    return obj

# Import models to make them available from models package
from .film import Film
from .genre import Genre
from .user import User
from .database import init_database, create_api_app, create_web_app

# Export all models
__all__ = ['Film', 'Genre', 'User', 'init_database', 'create_api_app', 'create_web_app', 
           'db', 'films_collection', 'genres_collection', 'users_collection', 'serialize_id']
