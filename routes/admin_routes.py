from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, session
import os
import json
from datetime import datetime
from pymongo import MongoClient
from bson.objectid import ObjectId
from functools import wraps  # Add this import

# Create a blueprint for admin routes
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# MongoDB connection settings
uri = os.environ.get('MONGO_URI', "mongodb+srv://kiwi:trang%402005@film-users.10h2w59.mongodb.net/?retryWrites=true&w=majority")
dbname = os.environ.get('MONGO_DBNAME', "film-users")

def get_db():
    """Get MongoDB database connection"""
    try:
        client = MongoClient(
            uri,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000,
            socketTimeoutMS=10000,
            maxPoolSize=50,
            ssl=True,
            tlsAllowInvalidCertificates=True,
            retryWrites=True
        )
        db = client[dbname]
        return client, db
    except Exception as e:
        print(f"Database connection error: {str(e)}")
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
        print(f"Error retrieving genres: {str(e)}")
        return []
    finally:
        if client:
            client.close()

def get_next_user_id(db):
    """Get next available sequential user ID"""
    try:
        # Count total users to determine next ID
        total_users = db.users.count_documents({})
        
        # If database is empty
        if total_users == 0:
            return 1
            
        # Get highest ID user
        highest_user = db.users.find_one(sort=[("id", -1)])
        
        # If no user has an ID field
        if not highest_user or "id" not in highest_user:
            # Find users with ID field
            users_with_id = list(db.users.find({"id": {"$exists": True}}).sort("id", -1).limit(1))
            if users_with_id:
                return users_with_id[0].get("id", 0) + 1
            else:
                return 1
            
        # If there's a gap in the sequence, use highest+1, otherwise total+1
        if highest_user["id"] >= total_users:
            return highest_user["id"] + 1
        else:
            # Find the first unused ID in sequence
            all_ids = set(user.get("id", 0) for user in db.users.find({"id": {"$exists": True}}, {"id": 1}))
            for i in range(1, total_users + 2):  # +2 to handle edge cases
                if i not in all_ids:
                    return i
                    
            # Fallback just in case
            return total_users + 1
    except Exception as e:
        print(f"Error getting next user ID: {str(e)}")
        # Return a safe default in case of error
        try:
            # Try to count documents again as a fallback
            count = db.users.count_documents({}) + 1
            return count
        except:
            # If all else fails, return 1
            return 1

# Admin access required decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            # Chuyển hướng về trang đăng nhập nếu chưa đăng nhập
            return redirect(url_for('home'))
        
        # Kiểm tra người dùng có phải là admin không
        client, db = get_db()
        if db is None:
            # Chuyển hướng về trang chủ nếu kết nối cơ sở dữ liệu thất bại
            return redirect(url_for('home'))
        
        try:
            user_id = session.get('user_id')  # Lấy ID người dùng từ session
            
            # Thử tìm người dùng theo ObjectId trước
            try:
                user = db.users.find_one({'_id': ObjectId(user_id)})  # Tìm theo MongoDB ObjectId
            except:
                # Nếu không phải ObjectId hợp lệ, thử tìm theo ID số
                try:
                    user_id_int = int(user_id)
                    user = db.users.find_one({'id': user_id_int})  # Tìm theo ID số
                except:
                    user = None
            
            if not user or user.get('role') != 'admin':
                # Chuyển hướng về trang chủ nếu không phải admin
                return redirect(url_for('home'))
                
        except Exception as e:
            # Chuyển hướng về trang chủ nếu có lỗi
            return redirect(url_for('home'))
        finally:
            if client:
                client.close()  # Đóng kết nối cơ sở dữ liệu
        
        return f(*args, **kwargs)  # Tiếp tục thực hiện hàm nếu là admin
    return decorated_function

# API routes for account management
@admin_bp.route('/accounts/api/list')
def list_accounts():
    page = int(request.args.get('page', 1))
    role_filter = request.args.get('role', '')
    status_filter = request.args.get('status', '')
    
    client, db = get_db()
    if db is None:
        return jsonify({'error': 'Database connection failed', 'accounts': [], 'currentPage': 1, 'totalPages': 1}), 500
    
    try:
        # Build query and pagination parameters
        query = {}
        if role_filter: query['role'] = role_filter
        if status_filter: query['status'] = status_filter
        
        per_page = 8
        skip = (page - 1) * per_page
        
        # Get total count for pagination
        total_accounts = db.users.count_documents(query)
        total_pages = max(1, (total_accounts + per_page - 1) // per_page)
        
        # Fetch accounts with pagination
        accounts = []
        for account in db.users.find(query).skip(skip).limit(per_page):
            # Convert ObjectId to string and ensure ID exists
            account['_id'] = str(account['_id'])
            account['mongo_id'] = account['_id']
            
            # Ensure sequential ID exists
            if 'id' not in account or account['id'] is None:
                new_id = get_next_user_id(db)
                db.users.update_one(
                    {'_id': ObjectId(account['_id'])},
                    {'$set': {'id': new_id}}
                )
                account['id'] = new_id
                
            accounts.append(account)
            
        return jsonify({
            'accounts': accounts,
            'currentPage': page,
            'totalPages': total_pages
        })
    except Exception as e:
        print(f"Error in list_accounts: {str(e)}")
        return jsonify({
            'error': str(e),
            'accounts': [],
            'currentPage': 1,
            'totalPages': 1
        }), 500
    finally:
        if client:
            client.close()

@admin_bp.route('/accounts/api/account/<account_id>', methods=['GET'])
def get_account(account_id):
    client, db = get_db()
    if db is None:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        # Try to find by numeric ID first
        try:
            account_id_int = int(account_id)
            account = db.users.find_one({'id': account_id_int})
        except (ValueError, TypeError):
            # If not a valid integer, try as ObjectId
            account = db.users.find_one({'_id': ObjectId(account_id)})
        
        if account:
            account['_id'] = str(account['_id'])
            account['mongo_id'] = account['_id']  # For compatibility
            return jsonify(account)
        
        return jsonify({'error': 'Account not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if client:
            client.close()

@admin_bp.route('/accounts/api/account', methods=['POST'])
def create_account():
    client, db = get_db()
    if db is None:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        account_data = request.json if request.is_json else request.form.to_dict()
        
        # Set created timestamp
        account_data['registerDate'] = datetime.utcnow()
        
        # Always assign a numeric ID    
        if 'id' not in account_data or account_data['id'] is None:
            account_data['id'] = get_next_user_id(db)
        
        # Insert account into MongoDB
        result = db.users.insert_one(account_data)
        return jsonify({
            'success': True, 
            'message': 'Account created successfully',
            'id': account_data['id']
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if client:
            client.close()

@admin_bp.route('/accounts/api/account/<account_id>', methods=['PUT'])
def update_account(account_id):
    client, db = get_db()
    if db is None:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        account_data = request.json if request.is_json else request.form.to_dict()
        
        # Remove _id if present to avoid update errors
        if '_id' in account_data:
            del account_data['_id']
        
        # Try to update by numeric ID first
        try:
            account_id_int = int(account_id)
            result = db.users.update_one(
                {'id': account_id_int},
                {'$set': account_data}
            )
        except (ValueError, TypeError):
            # If not a valid integer, try as ObjectId
            result = db.users.update_one(
                {'_id': ObjectId(account_id)},
                {'$set': account_data}
            )
        
        if result.matched_count == 0:
            return jsonify({'error': 'Account not found'}), 404
        
        return jsonify({'success': True, 'message': 'Account updated successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if client:
            client.close()

@admin_bp.route('/accounts/api/account/<account_id>', methods=['DELETE'])
def delete_account(account_id):
    client, db = get_db()
    if db is None:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        # Try to delete by numeric ID first
        try:
            account_id_int = int(account_id)
            result = db.users.delete_one({'id': account_id_int})
        except (ValueError, TypeError):
            # If not a valid integer, try as ObjectId
            result = db.users.delete_one({'_id': ObjectId(account_id)})
        
        if result.deleted_count == 0:
            return jsonify({'error': 'Account not found'}), 404
        
        return jsonify({'success': True, 'message': 'Account deleted successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if client:
            client.close()

# API routes for film management
@admin_bp.route('/films/api/films', methods=['GET'])
def list_films():
    """Get all films with optional filtering"""
    client, db = get_db()
    if db is None:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        # Get query parameters for filtering
        search_query = request.args.get('title', '')
        genre_slugs = request.args.getlist('genre')
        status = request.args.get('status', '')
        
        # Build filter query
        filter_query = {}
        # Add title search if provided
        if search_query:
            filter_query['title'] = {'$regex': search_query, '$options': 'i'}
        
        # Get all films from MongoDB based on filters
        films = list(db.films.find(filter_query))
        
        # Get all genres for genre filtering
        genres = list(db.genres.find())
        
        # Create a mapping from slug to genre id for filtering
        slug_to_id = {}
        for genre in genres:
            if 'slug' in genre and 'id' in genre:
                slug_to_id[genre['slug']] = genre['id']
        
        # Add genre information to each film
        filtered_films = []
        for film in films:
            film['_id'] = str(film['_id'])  # Convert ObjectId to string
            
            # Determine film status based on episode_count
            if 'episode_count' in film:
                if isinstance(film['episode_count'], int):
                    film['status'] = 'single' if film['episode_count'] == 1 else 'series'
                else:
                    # Handle non-integer episode counts (like "Chưa xác định")
                    film['status'] = 'unknown'
            else:
                film['status'] = 'unknown'
            
            # Get genre information
            genre_ids = film.get('genre_ids', [])
            film_genres = []
            
            for genre_id in genre_ids:
                genre = next((g for g in genres if g.get('id') == genre_id), None)
                if genre:
                    film_genres.append({
                        'id': genre['id'],
                        'name': genre['name'],
                        'slug': genre.get('slug', '')
                    })
            film['genres'] = film_genres
            
            # Lọc theo trạng thái nếu được chỉ định
            if status and film['status'] != status:
                continue
            
            # Lọc theo thể loại phim nếu được chỉ định
            if genre_slugs:
                # Kiểm tra xem bất kỳ thể loại nào của phim có khớp với các thể loại đã chọn không
                film_genre_slugs = [g.get('slug', '') for g in film_genres]
                if any(slug in film_genre_slugs for slug in genre_slugs):
                    filtered_films.append(film)
            else:
                filtered_films.append(film)
        
        # Trả về danh sách phim đã lọc
        return jsonify(filtered_films)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if client:
            client.close()

@admin_bp.route('/films/api/films/<film_id>', methods=['GET'])
def get_film(film_id):
    client, db = get_db()
    if db is None:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        # Try to find by numeric ID first
        try:
            film_id_int = int(film_id)
            film = db.films.find_one({'id': film_id_int})
        except (ValueError, TypeError):
            # If not a valid integer, try as ObjectId
            film = db.films.find_one({'_id': ObjectId(film_id)})
        
        if film:
            film['_id'] = str(film['_id'])
            
            # Get genre information
            genre_ids = film.get('genre_ids', [])
            genres = []
            for genre_id in genre_ids:
                genre = db.genres.find_one({'id': genre_id})
                if genre:
                    genres.append({
                        'id': genre['id'],
                        'name': genre['name'],
                        'slug': genre.get('slug', '')
                    })
            film['genres'] = genres
            
            return jsonify(film)
        
        return jsonify({'error': 'Film not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if client:
            client.close()

@admin_bp.route('/films/api/films', methods=['POST'])
def create_film():
    client, db = get_db()
    if db is None:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        film_data = request.json if request.is_json else request.form.to_dict()
        
        # Generate a new ID if not provided
        if 'id' not in film_data or not film_data['id']:
            highest_film = db.films.find_one(sort=[("id", -1)])
            new_id = 1 if not highest_film else highest_film.get('id', 0) + 1
            film_data['id'] = new_id
        else:
            film_data['id'] = int(film_data['id'])
        
        # Handle fields that should be integers
        if 'episode_count' in film_data and film_data['episode_count']:
            try:
                film_data['episode_count'] = int(film_data['episode_count'])
            except ValueError:
                pass
        
        # Insert film into MongoDB
        result = db.films.insert_one(film_data)
        return jsonify({
            'success': True, 
            'message': 'Film created successfully',
            'id': film_data['id']
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if client:
            client.close()

@admin_bp.route('/films/api/films/<film_id>', methods=['PUT'])
def update_film(film_id):
    client, db = get_db()
    if db is None:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        film_data = request.json if request.is_json else request.form.to_dict()
        
        # Remove _id if present to avoid update errors
        if '_id' in film_data:
            del film_data['_id']
        
        # Handle fields that should be integers
        if 'id' in film_data and film_data['id']:
            film_data['id'] = int(film_data['id'])
        if 'episode_count' in film_data and film_data['episode_count']:
            try:
                film_data['episode_count'] = int(film_data['episode_count'])
            except ValueError:
                pass
        
        # Try to update by numeric ID first
        try:
            film_id_int = int(film_id)
            result = db.films.update_one(
                {'id': film_id_int},
                {'$set': film_data}
            )
        except (ValueError, TypeError):
            # If not a valid integer, try as ObjectId
            result = db.films.update_one(
                {'_id': ObjectId(film_id)},
                {'$set': film_data}
            )
        
        if result.matched_count == 0:
            return jsonify({'error': 'Film not found'}), 404
        
        return jsonify({'success': True, 'message': 'Film updated successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if client:
            client.close()

@admin_bp.route('/films/api/films/<film_id>', methods=['DELETE'])
def delete_film(film_id):
    client, db = get_db()
    if db is None:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        # Try to delete by numeric ID first
        try:
            film_id_int = int(film_id)
            result = db.films.delete_one({'id': film_id_int})
        except (ValueError, TypeError):
            # If not a valid integer, try as ObjectId
            result = db.films.delete_one({'_id': ObjectId(film_id)})
        
        if result.deleted_count == 0:
            return jsonify({'error': 'Film not found'}), 404
        
        return jsonify({'success': True, 'message': 'Film deleted successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if client:
            client.close()

def register_admin_routes(app):
    """Register admin routes with the Flask application"""
    app.register_blueprint(admin_bp)
    
    # Register standalone routes
    @app.route('/admin/films')
    @admin_required
    def films_manager():
        """Films manager page"""
        # Get all genres for the filter dropdown
        genres = get_genres()
        return render_template('films_manager.html', genres=genres)
    
    @app.route('/admin/accounts')
    @admin_required
    def accounts_manager():
        """Accounts manager page"""
        return render_template('accounts_manager.html')
    
    @app.route('/admin/')
    @admin_required
    def admin_dashboard():
        """Admin dashboard - redirects to films manager"""
        return redirect(url_for('films_manager'))
