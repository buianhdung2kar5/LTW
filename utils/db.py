import os
from pymongo import MongoClient
import ssl

def get_db_name():
    """Get the database name from environment variables or use default"""
    # Always use the Atlas database name
    return os.environ.get('MONGO_DBNAME', "film-users")

def get_mongo_client():
    """Get MongoDB client for Atlas connection"""
    try:
        # Only use cloud connection with simplified settings
        uri = os.environ.get('MONGO_URI', 
              "mongodb+srv://kiwi:trang%402005@film-users.10h2w59.mongodb.net/?retryWrites=true&w=majority")
        
        client = MongoClient(
            uri,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000,
            socketTimeoutMS=10000,
            maxPoolSize=10,
            ssl=True,
            tlsAllowInvalidCertificates=True,  # Updated from ssl_cert_reqs=ssl.CERT_NONE
            retryWrites=True,
            appname="phim-neu-app"   # For monitoring in MongoDB Atlas
        )
        
        # Test connection
        client.admin.command('ping')
        print("Connected to MongoDB Atlas")
        return client
    except Exception as e:
        print(f"MongoDB Atlas connection error: {str(e)}")
        
        # As a fallback, create a minimal client that won't crash the application
        class MinimalClient:
            def __getitem__(self, key):
                return MinimalDB()
            def close(self):
                pass
            
        class MinimalDB:
            def __getattr__(self, name):
                return MinimalCollection()
                
        class MinimalCollection:
            def find_one(self, *args, **kwargs): return None
            def find(self, *args, **kwargs): 
                class MinimalCursor:
                    def sort(self, *args): return self
                    def limit(self, *args): return []
                    def skip(self, *args): return self
                return MinimalCursor()
            def count_documents(self, *args, **kwargs): return 0
            def insert_one(self, *args, **kwargs): return type('obj', (object,), {'inserted_id': 'dummy_id'})
            def update_one(self, *args, **kwargs): return None
            def delete_one(self, *args, **kwargs): return None
            def create_index(self, *args, **kwargs): return None
            
        return MinimalClient()

def migrate_users_without_id(db):
    """Reassign all user IDs to be sequential natural numbers (1, 2, 3, ...)"""
    try:
        # Get all users to ensure complete sequential numbering
        all_users = list(db.users.find().sort("registerDate", 1))  # Sort by registration date
        
        if not all_users:
            print("No users found in database")
            return True
            
        print(f"Reassigning sequential IDs to {len(all_users)} users...")
        
        # Reassign IDs sequentially starting from 1
        for index, user in enumerate(all_users, start=1):
            # Update each user with sequential ID (1, 2, 3, ...)
            db.users.update_one(
                {"_id": user["_id"]},
                {"$set": {"id": index}}
            )
            
        print(f"✅ Successfully reassigned IDs for {len(all_users)} users")
        return True
    except Exception as e:
        print(f"❌ Error reassigning user IDs: {str(e)}")
        return False

def init_mongo_indexes(db):
    """Initialize MongoDB indexes safely"""
    try:
        # Test if db is actually connected before creating indexes
        db.command('ping')
        
        # IMPORTANT: First migrate users without IDs
        migrate_users_without_id(db)
        
        # Create film indexes
        db.films.create_index("id", unique=True)
        db.films.create_index("title")
        db.films.create_index([("title", "text"), ("description", "text")])
        
        # Create genre indexes
        db.genres.create_index("slug", unique=True)
        db.genres.create_index("id", unique=True)
        
        # Create user indexes
        db.users.create_index("username", unique=True)
        db.users.create_index("id", unique=True)  # Now safe after migration
        
        print("✅ MongoDB indexes created successfully")
        return True
    except Exception as e:
        print(f"❌ Error creating MongoDB indexes: {str(e)}")
        return False
