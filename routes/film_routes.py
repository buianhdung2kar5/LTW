import logging
from flask import render_template, request, redirect, url_for, current_app, session
from pymongo import MongoClient
import os
from bson import ObjectId  # Thêm dòng này ở đầu file nếu chưa có

logger = logging.getLogger(__name__)

# MongoDB connection settings
uri = os.environ.get('MONGO_URI', "mongodb+srv://kiwi:trang%402005@film-users.10h2w59.mongodb.net/?retryWrites=true&w=majority")
dbname = os.environ.get('MONGO_DBNAME', "film-users")

def get_db():
    """Get MongoDB database connection"""
    try:
        client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        db = client[dbname]
        return client, db
    except Exception as e:
        logger.error(f"Database connection error: {str(e)}")
        return None, None

def get_genres():
    """Get all genres from database"""
    client, db = get_db()
    if db is None:
        return []
    
    try:
        genres = list(db.genres.find().sort("name", 1))
        return genres
    except Exception as e:
        logger.error(f"Error retrieving genres: {str(e)}")
        return []
    finally:
        if client:
            client.close()

def register_film_routes(app):
    """Register film-related routes with the Flask application"""
    
    @app.context_processor
    def inject_common_data():
        """Inject common data into all templates"""
        return {
            'genres': get_genres(),
            'session': request.cookies.to_dict()  # Simplified session handling
        }
    
    @app.route('/')
    def home():
        """Homepage route"""
        client, db = get_db()
        if db is None:
            return render_template('homepage.html', new_films=[], all_films=[], top_films=[])
        
        try:
            # Get featured/new films (latest 12)
            new_films = list(db.films.find().sort("_id", -1).limit(12))
            
            # Get all films for collection section (limit to 16)
            all_films = list(db.films.find().limit(16))
            
            # Get top films by rating
            top_films = list(db.films.find().sort("rating", -1).limit(10))
            
            return render_template('homepage.html', 
                                  new_films=new_films, 
                                  all_films=all_films, 
                                  top_films=top_films)
        except Exception as e:
            logger.error(f"Error loading homepage: {str(e)}")
            return render_template('error.html', message="Error loading homepage")
        finally:
            if client:
                client.close()
    
    @app.route('/film/<int:film_id>')
    def film_details(film_id):
        """Show details for a specific film"""
        client, db = get_db()
        
        # Lấy user_id từ session
        user_id = session.get('user_id')
        is_favorited = False  # Mặc định là chưa yêu thích

        if db is None:
            return render_template('film_details.html', film=None, related_films=[], top_films=[], user_id=user_id)

        try:
            # Get the film by ID
            film = db.films.find_one({"id": film_id})
            
            if not film:
                return render_template('error.html', message="Film not found"), 404
            
            # Kiểm tra xem người dùng đã yêu thích phim này chưa
            if user_id:
                favorite = db.favorites.find_one({
                    "user_id": ObjectId(user_id),
                    "film_id": film_id
                })
                is_favorited = favorite is not None
            
            # Get related films (same genre)
            related_films = []
            if film.get("genre_ids"):
                related_films = list(db.films.find({
                    "genre_ids": {"$in": film.get("genre_ids", [])},
                    "id": {"$ne": film_id}  # Exclude current film
                }).limit(8))
            
            # Get top films
            top_films = list(db.films.find().sort("rating", -1).limit(5))
            
            return render_template('film_details.html', 
                                film=film, 
                                related_films=related_films,
                                top_films=top_films,
                                user_id=user_id,
                                is_favorited=is_favorited)  # Truyền thêm biến này vào template
        except Exception as e:
            logger.error(f"Error loading film details for ID {film_id}: {str(e)}")
            return render_template('error.html', message="Error loading film details")
        finally:
            if client:
                client.close()
    @app.route('/watch/<int:film_id>')
    def watch_film(film_id):
        """Watch a specific film"""
        client, db = get_db()
        if db is None:
            return render_template('play_film.html', film=None, related_films=[], top_films=[])
        
        try:
            # Get the film
            film = db.films.find_one({"id": film_id})
            
            if not film:
                return render_template('error.html', message="Film not found"), 404
            
            # Get related films (same genre)
            related_films = []
            if film.get("genre_ids"):
                related_films = list(db.films.find({
                    "genre_ids": {"$in": film.get("genre_ids", [])},
                    "id": {"$ne": film_id}  # Exclude current film
                }).limit(8))
            
            # Get top films
            top_films = list(db.films.find().sort("rating", -1).limit(5))
            
            return render_template('play_film.html', 
                                  film=film, 
                                  related_films=related_films,
                                  top_films=top_films)
        except Exception as e:
            logger.error(f"Error loading play film page for ID {film_id}: {str(e)}")
            return render_template('error.html', message="Error loading film player")
        finally:
            if client:
                client.close()
    
    @app.route('/collection')
    def collection():
        """Show the film collection"""
        page = request.args.get('page', 1, type=int)
        per_page = 16  # Films per page
        
        client, db = get_db()
        if db is None:
            return render_template('collection.html', films=[], top_films=[], 
                                  current_page=1, total_pages=1)
        
        try:
            # Calculate skip value for pagination
            skip = (page - 1) * per_page
            
            # Get films for current page
            films = list(db.films.find().skip(skip).limit(per_page))
            
            # Get total count for pagination
            total_films = db.films.count_documents({})
            total_pages = (total_films + per_page - 1) // per_page  # Ceiling division
            
            # Get top films for sidebar
            top_films = list(db.films.find().sort("rating", -1).limit(10))
            
            return render_template('collection.html', 
                                  films=films,
                                  top_films=top_films,
                                  current_page=page,
                                  total_pages=total_pages)
        except Exception as e:
            logger.error(f"Error loading collection page: {str(e)}")
            return render_template('error.html', message="Error loading film collection")
        finally:
            if client:
                client.close()
        
    @app.route('/genre/<string:genre_slug>')
    def genre(genre_slug):
        """Show films in a specific genre"""
        page = request.args.get('page', 1, type=int)
        per_page = 12  # Films per page
        
        client, db = get_db()
        if db is None:
            return render_template('film_genres.html', genre_movies=[], top_movies=[],
                                  genre="", genre_slug="", current_page=1, total_pages=1)
        
        try:
            # Get genre by slug
            genre_doc = db.genres.find_one({"slug": genre_slug})
            
            if not genre_doc:
                return render_template('error.html', message="Genre not found"), 404
            
            # Calculate skip value for pagination
            skip = (page - 1) * per_page
            
            # Get films in this genre
            genre_movies = list(db.films.find({
                "genre_ids": genre_doc["id"]
            }).skip(skip).limit(per_page))
            
            # Get total count for pagination
            total_films = db.films.count_documents({"genre_ids": genre_doc["id"]})
            total_pages = (total_films + per_page - 1) // per_page  # Ceiling division
            
            # Get top films for sidebar
            top_movies = list(db.films.find().sort("rating", -1).limit(7))
            
            return render_template('film_genres.html',
                                  genre_movies=genre_movies,
                                  top_movies=top_movies,
                                  genre=genre_doc["name"],
                                  genre_slug=genre_slug,
                                  current_page=page,
                                  total_pages=total_pages)
        except Exception as e:
            logger.error(f"Error loading genre page for {genre_slug}: {str(e)}")
            return render_template('error.html', message="Error loading genre page")
        finally:
            if client:
                client.close()
    
    @app.route('/search')
    def search():
        """Search for films"""
        query = request.args.get('query', '')
        page = request.args.get('page', 1, type=int)
        per_page = 12  # Results per page
        
        if not query:
            return redirect(url_for('home'))
        
        client, db = get_db()
        if db is None:
            return render_template('search_result.html', results=[], suggested_films=[],
                                query=query, current_page=1, total_pages=1, top_films=[])
        
        try:
            # Calculate skip value for pagination
            skip = (page - 1) * per_page
            
            # Perform search (case-insensitive)
            results = list(db.films.find({
                "$or": [
                    {"title": {"$regex": query, "$options": "i"}},
                    {"description": {"$regex": query, "$options": "i"}},
                    {"overview": {"$regex": query, "$options": "i"}}
                ]
            }).skip(skip).limit(per_page))
            
            # Get total count for pagination
            total_results = db.films.count_documents({
                "$or": [
                    {"title": {"$regex": query, "$options": "i"}},
                    {"description": {"$regex": query, "$options": "i"}},
                    {"overview": {"$regex": query, "$options": "i"}}
                ]
            })
            total_pages = (total_results + per_page - 1) // per_page  # Ceiling division
            
            # Get suggested films (random selection)
            suggested_films = list(db.films.aggregate([{"$sample": {"size": 8}}]))
            
            # Get top films for sidebar
            top_films = list(db.films.find().sort("rating", -1).limit(5))
            
            return render_template('search_result.html',
                                results=results,
                                suggested_films=suggested_films,
                                top_films=top_films,  # Thêm top_films vào đây
                                query=query,
                                current_page=page,
                                total_pages=total_pages)
            
        except Exception as e:
            logger.error(f"Error searching for '{query}': {str(e)}")
            return render_template('error.html', message="Error performing search")
        finally:
            if client:
                client.close()
