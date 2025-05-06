from bson.objectid import ObjectId
from . import films_collection, serialize_id

class Film:
    @staticmethod
    def get_all():
        try:
            # Handle possible generator/iterator errors
            results = list(films_collection.find())
            return [serialize_id(film) for film in results]
        except Exception as e:
            print(f"Error in Film.get_all(): {str(e)}")
            return []  # Return empty list on error
    
    @staticmethod
    def get_by_id(film_id):
        if isinstance(film_id, int):
            film = films_collection.find_one({"id": film_id})
        else:
            try:
                film = films_collection.find_one({"_id": ObjectId(film_id)})
            except:
                film = None
        return serialize_id(film) if film else None
    
    @staticmethod
    def get_by_genre(genre_id):
        try:
            films = films_collection.find({"genre_ids": genre_id})
            return [serialize_id(film) for film in films]
        except Exception as e:
            print(f"Error in Film.get_by_genre(): {str(e)}")
            return []
    
    @staticmethod
    def create(data):
        # Generate a new id if not provided
        if 'id' not in data:
            max_id = films_collection.find_one(sort=[("id", -1)])
            data['id'] = 1 if max_id is None else max_id.get('id', 0) + 1
            
        result = films_collection.insert_one(data)
        return serialize_id({**data, "_id": result.inserted_id})
    
    @staticmethod
    def update(film_id, data):
        if isinstance(film_id, int):
            films_collection.update_one({"id": film_id}, {"$set": data})
            return Film.get_by_id(film_id)
        else:
            try:
                films_collection.update_one({"_id": ObjectId(film_id)}, {"$set": data})
                return Film.get_by_id(film_id)
            except:
                return None
    
    @staticmethod
    def delete(film_id):
        if isinstance(film_id, int):
            films_collection.delete_one({"id": film_id})
        else:
            try:
                films_collection.delete_one({"_id": ObjectId(film_id)})
            except:
                pass
    
    @staticmethod
    def search(query):
        try:
            films = films_collection.find({"title": {"$regex": query, "$options": "i"}})
            return [serialize_id(film) for film in films]
        except Exception as e:
            print(f"Error in Film.search(): {str(e)}")
            return []
    
    @staticmethod
    def get_featured():
        try:
            # Handle possible generator/iterator errors
            results = list(films_collection.find({"featured": True}))
            return [serialize_id(film) for film in results]
        except Exception as e:
            print(f"Error in Film.get_featured(): {str(e)}")
            return []  # Return empty list on error
    
    @staticmethod
    def get_top_rated(limit=10):
        try:
            # Handle possible generator/iterator errors
            results = list(films_collection.find().sort("rating", -1).limit(limit))
            return [serialize_id(film) for film in results]
        except Exception as e:
            print(f"Error in Film.get_top_rated(): {str(e)}")
            return []  # Return empty list on error
    
    @staticmethod
    def paginate(page=1, per_page=10, filters=None):
        try:
            skip = (page - 1) * per_page
            
            # Apply filters if provided
            query = filters if filters else {}
            
            # Get total count for pagination
            total_count = films_collection.count_documents(query)
            total_pages = (total_count + per_page - 1) // per_page
            
            # Get paginated results
            films = films_collection.find(query).skip(skip).limit(per_page)
            
            return {
                "films": [serialize_id(film) for film in films],
                "total_pages": total_pages,
                "total_count": total_count,
                "current_page": page
            }
        except Exception as e:
            print(f"Error in Film.paginate(): {str(e)}")
            return {
                "films": [],
                "total_pages": 1,
                "total_count": 0,
                "current_page": page
            }
    
    @staticmethod
    def load_films_from_database():
        """Get films directly from MongoDB film-users database"""
        try:
            # Check if films exist in the database
            films_count = films_collection.count_documents({})
            if films_count > 0:
                print(f"Found {films_count} films in film-users database.")
                return True
                
            print("No films found in film-users database. Please populate the database.")
            return False
        except Exception as e:
            print(f"Error loading films from database: {str(e)}")
            return False
    
    @staticmethod
    def create_indexes():
        """Create necessary indexes for films collection"""
        try:
            films_collection.create_index("id", unique=True)
            films_collection.create_index("title")
            films_collection.create_index([("title", "text"), ("description", "text")])
            print("[SUCCESS] Film indexes created successfully")
            return True
        except Exception as e:
            print(f"[ERROR] Error creating film indexes: {str(e)}")
            return False
            
    @staticmethod
    def find_duplicate_ids():
        """Find films with duplicate IDs"""
        try:
            pipeline = [
                {"$group": {"_id": "$id", "count": {"$sum": 1}, "titles": {"$push": "$title"}}},
                {"$match": {"count": {"$gt": 1}}},
                {"$sort": {"count": -1}}
            ]
            
            duplicate_ids = list(films_collection.aggregate(pipeline))
            return duplicate_ids
        except Exception as e:
            print(f"Error finding duplicate IDs: {str(e)}")
            return []
    
    @staticmethod
    def fix_duplicate_ids():
        """Fix films with duplicate IDs by assigning new IDs to duplicates"""
        try:
            duplicate_ids = Film.find_duplicate_ids()
            changes_made = 0
            
            for dup in duplicate_ids:
                dup_id = dup['_id']
                films = list(films_collection.find({"id": dup_id}))
                
                # Keep first film, update others with new IDs
                for i, film in enumerate(films[1:], 1):
                    highest_id_doc = films_collection.find_one(sort=[("id", -1)])
                    new_id = highest_id_doc['id'] + 1 if highest_id_doc else 1
                    
                    films_collection.update_one({"_id": film['_id']}, {"$set": {"id": new_id}})
                    changes_made += 1
            
            return {"success": True, "duplicates_fixed": changes_made}
        except Exception as e:
            return {"success": False, "error": str(e)}
