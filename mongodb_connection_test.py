import os
import sys
import json
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime

def serialize_id(obj):
    """Convert MongoDB ObjectId to string for display"""
    if isinstance(obj, dict) and '_id' in obj and isinstance(obj['_id'], ObjectId):
        obj['_id'] = str(obj['_id'])
    return obj

def test_mongodb_connection():
    """Test connection to MongoDB and print status"""
    print("Testing MongoDB Connection...")
    
    uri = os.environ.get('MONGO_URI', "mongodb+srv://kiwi:trang%402005@film-users.10h2w59.mongodb.net/?retryWrites=true&w=majority")
    dbname = os.environ.get('MONGO_DBNAME', "film-users")
    
    try:
        client = MongoClient(
            uri,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000,
            socketTimeoutMS=10000,
            maxPoolSize=50,
            retryWrites=True
        )
        
        client.admin.command('ping')
        print("✅ MongoDB connection successful!")
        
        db = client[dbname]
        films_collection = db.films
        genres_collection = db.genres
        users_collection = db.users
        
        print(f"Collections in database '{dbname}':")
        print(f"- Films: {films_collection.count_documents({})} documents")
        print(f"- Genres: {genres_collection.count_documents({})} documents")
        print(f"- Users: {users_collection.count_documents({})} documents")
        
        return client, db
    except Exception as e:
        print(f"❌ MongoDB connection error: {str(e)}")
        return None, None

def analyze_film_collection(db):
    """Analyze the film collection to understand why there are more films than expected"""
    if db is None:
        print("Cannot analyze film collection without database connection")
        return
    
    films_collection = db.films
    
    print("\n=== Analyzing Film Collection ===")
    
    total_films = films_collection.count_documents({})
    print(f"Total films in database: {total_films}")
    
    try:
        pipeline = [
            {"$group": {"_id": "$title", "count": {"$sum": 1}}},
            {"$match": {"count": {"$gt": 1}}},
            {"$sort": {"count": -1}}
        ]
        
        duplicate_titles = list(films_collection.aggregate(pipeline))
        if duplicate_titles:
            print(f"\n⚠️ Found {len(duplicate_titles)} duplicate film titles:")
            for dup in duplicate_titles[:10]:
                print(f"  '{dup['_id']}' appears {dup['count']} times")
                if dup['count'] > 2:
                    films = list(films_collection.find({"title": dup['_id']}))
                    for i, film in enumerate(films[:3], 1):
                        print(f"    {i}. ID: {film.get('id')}, MongoDB _id: {film.get('_id')}")
            
            total_duplicates = sum(dup['count'] - 1 for dup in duplicate_titles)
            print(f"\nTotal duplicate films: {total_duplicates}")
            print(f"Unique films (adjusted): {total_films - total_duplicates}")
        else:
            print("✅ No duplicate film titles found")
    except Exception as e:
        print(f"❌ Error checking for duplicate film titles: {str(e)}")
    
    print("\nAnalyzing potential import sources:")
    
    try:
        poster_patterns = [
            "placeholder.jpg",
            "http://",
            "https://",
            "/static/images/"
        ]
        
        for pattern in poster_patterns:
            count = films_collection.count_documents({"poster_path": {"$regex": pattern, "$options": "i"}})
            if count > 0:
                print(f"- Films with poster path containing '{pattern}': {count}")
        
        print("\nAnalyzing film data completeness:")
        fields_to_check = ["release_year", "length", "rating", "featured", "genre_ids", "genres"]
        
        for field in fields_to_check:
            exists_count = films_collection.count_documents({field: {"$exists": True}})
            missing_count = films_collection.count_documents({field: {"$exists": False}})
            print(f"- Field '{field}': {exists_count} present, {missing_count} missing")
            
        print("\nMost recently added films (based on _id timestamp):")
        recent_films = list(films_collection.find().sort("_id", -1).limit(5))
        for i, film in enumerate(recent_films, 1):
            film = serialize_id(film)
            print(f"  {i}. '{film.get('title')}' (ID: {film.get('id')}, MongoDB _id: {film.get('_id')})")
            
    except Exception as e:
        print(f"❌ Error analyzing film sources: {str(e)}")
        
    print("\nSample of films in database:")
    try:
        sample_size = min(5, total_films)
        sample_films = list(films_collection.aggregate([{"$sample": {"size": sample_size}}]))
        
        for i, film in enumerate(sample_films, 1):
            film = serialize_id(film)
            print(f"\n  Film {i}: '{film.get('title')}' (ID: {film.get('id')})")
            print(f"  - MongoDB _id: {film.get('_id')}")
            print(f"  - Release year: {film.get('release_year')}")
            print(f"  - Rating: {film.get('rating')}")
            genres_str = ', '.join(film.get('genres', [])) if film.get('genres') else 'None'
            print(f"  - Genres: {genres_str}")
    except Exception as e:
        print(f"❌ Error listing sample films: {str(e)}")

def test_film_operations(db):
    """Test film retrieval and operations"""
    if db is None:
        print("Cannot test film operations without database connection")
        return
    
    films_collection = db.films
    
    print("\n=== Testing Film Operations ===")
    
    print("\nTest 1: Retrieving film by ID")
    try:
        film = films_collection.find_one({"id": 1})
        if film:
            print(f"✅ Found film with ID 1: '{film.get('title')}'")
            print(f"   Release year: {film.get('release_year')}")
            print(f"   Genres: {', '.join(film.get('genres', []))}")
        else:
            film = films_collection.find_one()
            if film:
                print(f"✅ Found film: '{film.get('title')}' (ID: {film.get('id')})")
            else:
                print("❌ No films found in database")
    except Exception as e:
        print(f"❌ Error retrieving film: {str(e)}")
    
    print("\nTest 2: Retrieving featured films")
    try:
        featured_films = list(films_collection.find({"featured": True}).limit(5))
        if featured_films:
            print(f"✅ Found {len(featured_films)} featured films:")
            for i, film in enumerate(featured_films[:3], 1):
                print(f"   {i}. '{film.get('title')}' (ID: {film.get('id')})")
            if len(featured_films) > 3:
                print(f"   ... and {len(featured_films) - 3} more")
        else:
            print("❓ No featured films found")
    except Exception as e:
        print(f"❌ Error retrieving featured films: {str(e)}")
    
    print("\nTest 3: Searching films")
    try:
        search_term = "the"
        search_results = list(films_collection.find({"title": {"$regex": search_term, "$options": "i"}}).limit(5))
        if search_results:
            print(f"✅ Found {len(search_results)} films matching '{search_term}':")
            for i, film in enumerate(search_results[:3], 1):
                print(f"   {i}. '{film.get('title')}' (ID: {film.get('id')})")
            if len(search_results) > 3:
                print(f"   ... and {len(search_results) - 3} more")
        else:
            print(f"❓ No films found matching '{search_term}'")
    except Exception as e:
        print(f"❌ Error searching films: {str(e)}")
    
    print("\nTest 4: Retrieving top rated films")
    try:
        top_films = list(films_collection.find().sort("rating", -1).limit(5))
        if top_films:
            print(f"✅ Found {len(top_films)} top rated films:")
            for i, film in enumerate(top_films, 1):
                print(f"   {i}. '{film.get('title')}' - Rating: {film.get('rating')} (ID: {film.get('id')})")
        else:
            print("❓ No films found for rating sort")
    except Exception as e:
        print(f"❌ Error retrieving top rated films: {str(e)}")

def inspect_database_indexes(db):
    """Check and display MongoDB indexes"""
    if db is None:
        print("Cannot inspect indexes without database connection")
        return
        
    print("\n=== Database Indexes ===")
    
    try:
        film_indexes = list(db.films.list_indexes())
        print(f"\nFilm collection has {len(film_indexes)} indexes:")
        for idx, index in enumerate(film_indexes, 1):
            print(f"  {idx}. {index['name']}: {json.dumps(index['key'])}")
            
        id_index_exists = any(idx.get('name') == 'id_1' for idx in film_indexes)
        if id_index_exists:
            print("✅ 'id' field index exists, which is good for lookups by ID")
        else:
            print("⚠️ No index on 'id' field - this could slow down lookups by ID")
    except Exception as e:
        print(f"❌ Error checking film indexes: {str(e)}")
        
    try:
        genre_indexes = list(db.genres.list_indexes())
        print(f"\nGenre collection has {len(genre_indexes)} indexes:")
        for idx, index in enumerate(genre_indexes, 1):
            print(f"  {idx}. {index['name']}: {json.dumps(index['key'])}")
    except Exception as e:
        print(f"❌ Error checking genre indexes: {str(e)}")

def test_duplicate_keys(db):
    """Check for duplicate keys in the collections"""
    if db is None:
        print("Cannot check for duplicates without database connection")
        return
        
    print("\n=== Checking for Duplicate Keys ===")
    
    try:
        pipeline = [
            {"$group": {"_id": "$id", "count": {"$sum": 1}}},
            {"$match": {"count": {"$gt": 1}}},
            {"$sort": {"count": -1}}
        ]
        
        duplicate_ids = list(db.films.aggregate(pipeline))
        if duplicate_ids:
            print(f"⚠️ Found {len(duplicate_ids)} duplicate film IDs:")
            for dup in duplicate_ids:
                print(f"  ID {dup['_id']} appears {dup['count']} times")
                films = list(db.films.find({"id": dup['_id']}))
                for i, film in enumerate(films, 1):
                    print(f"    {i}. '{film.get('title')}' (MongoDB _id: {film.get('_id')})")
        else:
            print("✅ No duplicate film IDs found")
    except Exception as e:
        print(f"❌ Error checking for duplicate film IDs: {str(e)}")
    
    try:
        pipeline = [
            {"$group": {"_id": "$id", "count": {"$sum": 1}}},
            {"$match": {"count": {"$gt": 1}}},
            {"$sort": {"count": -1}}
        ]
        
        duplicate_ids = list(db.genres.aggregate(pipeline))
        if duplicate_ids:
            print(f"⚠️ Found {len(duplicate_ids)} duplicate genre IDs:")
            for dup in duplicate_ids:
                print(f"  ID {dup['_id']} appears {dup['count']} times")
        else:
            print("✅ No duplicate genre IDs found")
    except Exception as e:
        print(f"❌ Error checking for duplicate genre IDs: {str(e)}")

def fix_duplicate_issues(db):
    """Provide options to fix duplicate IDs if found"""
    if db is None:
        print("Cannot fix issues without database connection")
        return
        
    print("\n=== Options to Fix Duplicate Issues ===")
    
    pipeline = [
        {"$group": {"_id": "$id", "count": {"$sum": 1}}},
        {"$match": {"count": {"$gt": 1}}},
        {"$sort": {"count": -1}}
    ]
    
    duplicate_ids = list(db.films.aggregate(pipeline))
    
    if not duplicate_ids:
        print("✅ No duplicate IDs to fix!")
        return
        
    print(f"Found {len(duplicate_ids)} IDs with duplicates")
    print("\nOptions for fixing duplicates:")
    print("1. Reassign IDs to keep only one document per ID (keeps the first found)")
    print("2. Show MongoDB commands to manually delete specific duplicates")
    print("3. Generate a fixing script")
    
    try:
        choice = input("\nEnter option (1-3, or 'q' to quit): ")
        
        if choice == 'q':
            return
            
        if choice == '1':
            print("\nThis will update duplicate IDs to new unique IDs.")
            confirm = input("Proceed? (y/n): ")
            
            if confirm.lower() != 'y':
                print("Operation cancelled.")
                return
                
            films_collection = db.films
            
            for dup in duplicate_ids:
                dup_id = dup['_id']
                films = list(films_collection.find({"id": dup_id}))
                
                print(f"\nFixing duplicates for ID {dup_id} ({len(films)} instances):")
                
                for i, film in enumerate(films[1:], 1):
                    highest_id_doc = films_collection.find_one(sort=[("id", -1)])
                    new_id = highest_id_doc['id'] + 1 if highest_id_doc else 1
                    
                    print(f"  Changing '{film.get('title')}' from ID {dup_id} to {new_id}")
                    films_collection.update_one({"_id": film['_id']}, {"$set": {"id": new_id}})
            
            print("\n✅ Duplicate IDs have been fixed!")
                
        elif choice == '2':
            print("\nMongoDB commands to delete specific duplicates:")
            films_collection = db.films
            
            for dup in duplicate_ids:
                dup_id = dup['_id']
                films = list(films_collection.find({"id": dup_id}))
                
                print(f"\n# Commands for ID {dup_id} ({len(films)} instances):")
                print(f"# First document (to keep):")
                print(f"# Title: '{films[0].get('title')}', MongoDB _id: {films[0].get('_id')}")
                
                for i, film in enumerate(films[1:], 1):
                    film_id = serialize_id(film)['_id']
                    print(f"db.films.deleteOne({{ \"_id\": ObjectId(\"{film_id}\") }}) # Title: '{film.get('title')}'")
                    
        elif choice == '3':
            script_path = 'fix_duplicate_ids.py'
            with open(script_path, 'w') as f:
                f.write("""
# Fix duplicate IDs in MongoDB film collection
from pymongo import MongoClient
from bson.objectid import ObjectId
import os

uri = os.environ.get('MONGO_URI', "mongodb+srv://kiwi:trang%402005@film-users.10h2w59.mongodb.net/?retryWrites=true&w=majority")
dbname = os.environ.get('MONGO_DBNAME', "film_users")

def fix_duplicate_ids():
    client = MongoClient(uri, serverSelectionTimeoutMS=5000)
    db = client[dbname]
    films_collection = db.films
    
    pipeline = [
        {"$group": {"_id": "$id", "count": {"$sum": 1}}},
        {"$match": {"count": {"$gt": 1}}},
        {"$sort": {"count": -1}}
    ]
    
    duplicate_ids = list(films_collection.aggregate(pipeline))
    print(f"Found {len(duplicate_ids)} IDs with duplicates")
    
    for dup in duplicate_ids:
        dup_id = dup['_id']
        films = list(films_collection.find({"id": dup_id}))
        
        print(f"Fixing duplicates for ID {dup_id} ({len(films)} instances):")
        
        for i, film in enumerate(films[1:], 1):
            highest_id_doc = films_collection.find_one(sort=[("id", -1)])
            new_id = highest_id_doc['id'] + 1 if highest_id_doc else 1
            
            print(f"  Changing '{film.get('title')}' from ID {dup_id} to {new_id}")
            films_collection.update_one({"_id": film['_id']}, {"$set": {"id": new_id}})
    
    print("Duplicate IDs have been fixed!")
    client.close()

if __name__ == "__main__":
    print("Starting duplicate ID fix...")
    fix_duplicate_ids()
    print("Process completed!")
""")
            print(f"\n✅ Fix script generated at '{script_path}'")
            print(f"Run with: python {script_path}")
            
        else:
            print("Invalid option selected.")
    except Exception as e:
        print(f"❌ Error in fix_duplicate_issues: {str(e)}")

if __name__ == "__main__":
    print("=== MongoDB Connection and Film Database Test ===")
    print(f"Date/Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    client, db = test_mongodb_connection()
    
    if db is not None:
        test_film_operations(db)
        inspect_database_indexes(db)
        test_duplicate_keys(db)
        analyze_film_collection(db)
        
        if input("\nWould you like to attempt to fix duplicate issues? (y/n): ").lower() == 'y':
            fix_duplicate_issues(db)
        
        if client is not None:
            client.close()
            print("\nMongoDB connection closed.")
    
    print("\nTest completed.")
