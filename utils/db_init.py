from utils.db_utils import get_mongo_client
import logging

logger = logging.getLogger(__name__)

def init_mongo_indexes():
    """Initialize all MongoDB indexes properly"""
    client = get_mongo_client()
    if client is None:
        logger.error("Cannot initialize MongoDB indexes: client is None")
        return False
        
    db = client["film-users"]
    
    try:
        # Create all indexes in a single block
        # Film indexes
        db.films.create_index("id", unique=True)
        db.films.create_index([("title", 1), ("title", "text"), ("description", "text")])
        
        # Genre indexes - combined
        db.genres.create_index([("slug", 1), ("id", 1), ("name", 1)], 
                              unique=True, name="genre_combined_idx")
        
        # User indexes - sparse index for optional fields
        db.users.create_index("username", unique=True)
        db.users.create_index("id", unique=True, sparse=True)
        
        # Favorites indexes - compound index for efficient lookups
        db.favorites.create_index([("user_id", 1), ("film_id", 1)], unique=True)
        db.favorites.create_index([("user_id", 1), ("added_at", -1)])
        
        logger.info("All MongoDB indexes created successfully")
        return True
    except Exception as e:
        logger.error(f"Error creating MongoDB indexes: {str(e)}")
        return False
