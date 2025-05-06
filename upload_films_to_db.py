import os
import json
import re
from datetime import datetime
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, DuplicateKeyError

# MongoDB connection settings
uri = os.environ.get('MONGO_URI', "mongodb+srv://kiwi:trang%402005@film-users.10h2w59.mongodb.net/?retryWrites=true&w=majority")
dbname = os.environ.get('MONGO_DBNAME', "film-users")  # Changed back to film-users with hyphen

# Path to films.json file
script_dir = os.path.dirname(os.path.abspath(__file__))
films_json_path = os.path.join(script_dir, 'films.json')

def upload_films_to_db():
    """Upload films from JSON file to MongoDB with sequential _id values"""
    print("Starting film upload to MongoDB...")
    
    # Create MongoDB client
    client = MongoClient(
        uri,
        serverSelectionTimeoutMS=5000,
        connectTimeoutMS=5000,
        socketTimeoutMS=10000,
        maxPoolSize=50,
        retryWrites=True
    )
    
    try:
        # Test connection
        client.admin.command('ping')
        print("✅ MongoDB connection successful!")
        
        # Get database and collections
        db = client[dbname]
        films_collection = db.films
        
        # Read films from JSON file
        print(f"Reading films from {films_json_path}...")
        with open(films_json_path, 'r', encoding='utf-8') as file:
            films_data = json.load(file)
        print(f"Found {len(films_data)} films in JSON file.")
        
        # Delete existing films
        print("Deleting all existing films from database...")
        films_collection.delete_many({})
        print("✅ All existing films deleted.")
        
        # Prepare films with sequential _id values
        films_to_insert = []
        for index, film in enumerate(films_data, start=1):
            # Parse episode count
            episode_count = film.get("episode_count", 1)
            if isinstance(episode_count, str):
                if episode_count.isdigit():
                    episode_count = int(episode_count)
                else:
                    episode_count = 1
            
            # Extract year from release date
            release_date = film.get("Release_date", "")
            release_year = datetime.now().year  # Default to current year
            if release_date:
                year_match = re.search(r'\d{4}', release_date)
                if year_match:
                    release_year = int(year_match.group(0))
            
            # Create film object with proper structure
            film_obj = {
                "_id": index,  # Set explicit _id value (1, 2, 3, ...)
                "id": index,   # Keep backward compatibility with old id
                "title": film.get("Title", f"Untitled Film {index}"),
                "description": film.get("Overview", "No description available"),
                "overview": film.get("Overview", "No description available"),
                "release_date": film.get("Release_date", ""),
                "release_year": release_year,
                "episode_count": episode_count,
                "poster_path": film.get("Poster_path", "/static/images/placeholder.jpg"),
                "status": film.get("Status", "Released"),
                "source_film": film.get("Source_Film", ""),
                "video_path": film.get("Source_Film", ""),
                "genres": film.get("Thể loại", []),
                "genre_ids": [],  # Will be updated if genres are created
                "rating": film.get("Rating", 7.5),
                "length": film.get("Length", 90),
                "featured": film.get("Featured", False)
            }
            
            films_to_insert.append(film_obj)
        
        # Insert films into database
        if films_to_insert:
            print(f"Inserting {len(films_to_insert)} films into database...")
            result = films_collection.insert_many(films_to_insert, ordered=True)
            print(f"✅ Successfully inserted {len(result.inserted_ids)} films!")
            
            # Create an index on the 'id' field
            films_collection.create_index("id", unique=True)
            print("✅ Created unique index on id field")
            
            # Create some default genres based on the films
            create_default_genres(db, films_to_insert)
        else:
            print("No films to insert.")
        
        print("Film upload completed!")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    finally:
        # Close connection
        client.close()
        print("MongoDB connection closed.")

def create_default_genres(db, films):
    """Create default genres and update film genre_ids"""
    genres_collection = db.genres
    
    # Delete existing genres
    print("Clearing existing genres...")
    genres_collection.delete_many({})
    
    # Extract unique genres from all films
    all_genres = set()
    for film in films:
        for genre in film.get("genres", []):
            all_genres.add(genre.strip().title())  # Normalize genre names
    
    # Create genre objects
    genre_objects = []
    genre_map = {}  # Map genre names to IDs for updating films
    
    for idx, genre_name in enumerate(sorted(all_genres), start=1):
        genre_obj = {
            "_id": idx,
            "id": idx,
            "name": genre_name,
            "slug": genre_name.lower().replace(" ", "-"),
            "description": f"Films in the {genre_name} genre"
        }
        genre_objects.append(genre_obj)
        genre_map[genre_name.lower()] = idx
    
    # Insert genres
    if genre_objects:
        print(f"Inserting {len(genre_objects)} genres...")
        genres_collection.insert_many(genre_objects)
        print("✅ Genres created successfully")
        
        # Create index on genre name and slug
        genres_collection.create_index("name")
        genres_collection.create_index("slug", unique=True)
        
        # Update film genre_ids
        print("Updating film genre IDs...")
        films_collection = db.films
        for film in films:
            film_id = film["id"]
            genre_ids = []
            
            for genre in film.get("genres", []):
                genre_key = genre.strip().lower()
                if genre_key in genre_map:
                    genre_ids.append(genre_map[genre_key])
            
            if genre_ids:
                films_collection.update_one(
                    {"id": film_id},
                    {"$set": {"genre_ids": genre_ids}}
                )
        
        print("✅ Film genre IDs updated")

if __name__ == "__main__":
    upload_films_to_db()
