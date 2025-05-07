"""
Centralized MongoDB connection manager using connection pooling
"""
from pymongo import MongoClient
import os
import threading
import logging

logger = logging.getLogger(__name__)

# Global connection pool
_mongo_client = None
_client_lock = threading.Lock()

def get_mongo_client():
    """Get or create MongoDB client singleton with optimized settings"""
    global _mongo_client
    
    # Return existing client if already connected
    if _mongo_client is not None:
        return _mongo_client
    
    # Lock to prevent race conditions when initializing the client
    with _client_lock:
        # Double-check to avoid race condition
        if _mongo_client is not None:
            return _mongo_client
            
        uri = os.environ.get('MONGO_URI', "mongodb+srv://kiwi:trang%402005@film-users.10h2w59.mongodb.net/?retryWrites=true&w=majority")
        
        try:
            _mongo_client = MongoClient(
                uri,
                serverSelectionTimeoutMS=3000,
                connectTimeoutMS=3000,
                socketTimeoutMS=10000,
                maxPoolSize=20,                 # Optimal pool size
                minPoolSize=5,                  # Keep minimum connections alive
                maxIdleTimeMS=60000,            # Close idle connections after 60s
                retryWrites=True,
                ssl=True,
                tlsAllowInvalidCertificates=True,
                appname="phim-neu-app",
                waitQueueTimeoutMS=1000         # Fast failure if queue wait is too long
            )
            
            # Verify connection is alive
            _mongo_client.admin.command('ping', serverSelectionTimeoutMS=2000)
            logger.info("MongoDB connection established successfully")
            return _mongo_client
        except Exception as e:
            logger.error(f"MongoDB connection error: {str(e)}")
            return None

def get_db_connection():
    """Get MongoDB database connection with error handling"""
    client = get_mongo_client()
    if client is None:
        return None, None
        
    db_name = os.environ.get('MONGO_DBNAME', "film-users")
    return client, client[db_name]
