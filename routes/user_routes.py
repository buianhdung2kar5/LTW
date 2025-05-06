from flask import Blueprint, render_template, request, session, jsonify, redirect, url_for, flash
from bson.objectid import ObjectId
from functools import wraps
import os
from datetime import datetime

# Try to import models
try:
    from models.models import Favorite, Film
except ImportError:
    # Fallback if models aren't available
    Favorite = None
    Film = None

# Create a blueprint
user_bp = Blueprint('user', __name__, url_prefix='/user')

# MongoDB connection function (reusing from admin routes)
def get_db():
    """Get MongoDB database connection"""
    try:
        from pymongo import MongoClient
        uri = os.environ.get('MONGO_URI', "mongodb+srv://kiwi:trang%402005@film-users.10h2w59.mongodb.net/?retryWrites=true&w=majority")
        dbname = os.environ.get('MONGO_DBNAME', "film-users")
        
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

# Authentication decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({"error": "Authentication required"}), 401
        return f(*args, **kwargs)
    return decorated_function

# User profile page
@user_bp.route('/account')
def profile():
    if 'user_id' not in session:
        flash('Vui lòng đăng nhập để xem trang này', 'error')
        return redirect(url_for('auth.login'))
    
    client, db = get_db()
    favorites = []
    
    try:
        user_id = session.get('user_id')
        
        # Use Favorite model if available, otherwise direct DB access
        if Favorite:
            favorites_data = Favorite.get_user_favorites(str(user_id))
            film_ids = [fav.get('film_id') for fav in favorites_data]
            
            for film_id in film_ids:
                film = Film.get_by_id(film_id)
                if film:
                    favorites.append(film)
        else:
            # Direct database access
            user_favorites = list(db.favorites.find({"user_id": user_id}))
            film_ids = [fav.get('film_id') for fav in user_favorites]
            
            for film_id in film_ids:
                try:
                    # Try different formats of ID
                    film = None
                    try:
                        film = db.films.find_one({"id": int(film_id)})
                    except:
                        try:
                            film = db.films.find_one({"_id": ObjectId(film_id)})
                        except:
                            film = db.films.find_one({"id": film_id})
                    
                    if film:
                        if '_id' in film:
                            film['_id'] = str(film['_id'])
                        favorites.append(film)
                except Exception as e:
                    print(f"Error getting film {film_id}: {str(e)}")
    except Exception as e:
        print(f"Error getting favorites: {str(e)}")
    finally:
        if client:
            client.close()
    
    return render_template('account.html', favorites=favorites)

# User profile data API
@user_bp.route('/profile/data')
@login_required
def profile_data():
    client, db = get_db()
    if db is None:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        # Try to find user by ID
        user_id = session.get('user_id')
        
        # Try to find by ObjectId first
        try:
            user = db.users.find_one({'_id': ObjectId(user_id)})
        except:
            # If not a valid ObjectId, try as a numeric ID
            try:
                user_id_int = int(user_id)
                user = db.users.find_one({'id': user_id_int})
            except:
                return jsonify({'error': 'User not found'}), 404
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Convert ObjectId to string for JSON serialization
        if '_id' in user:
            user['_id'] = str(user['_id'])
        
        # Remove sensitive information
        if 'password' in user:
            del user['password']
        
        return jsonify(user)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if client:
            client.close()

# Update user profile
@user_bp.route('/account/update', methods=['POST'])
@login_required
def update_profile():
    client, db = get_db()
    if db is None:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        # Get request data
        data = request.json
        email = data.get('email', '').strip()
        full_name = data.get('fullName', '').strip()
        
        # Get user from session
        user_id = session.get('user_id')
        
        # Try to find and update user
        update_data = {'updatedAt': datetime.utcnow()}
        if email:
            update_data['email'] = email
        if full_name:
            update_data['fullName'] = full_name
        
        # Try to update by ObjectId first
        try:
            result = db.users.update_one(
                {'_id': ObjectId(user_id)},
                {'$set': update_data}
            )
        except:
            # If not a valid ObjectId, try as a numeric ID
            try:
                user_id_int = int(user_id)
                result = db.users.update_one(
                    {'id': user_id_int},
                    {'$set': update_data}
                )
            except:
                return jsonify({'message': 'User not found'}), 404
        
        if result.matched_count == 0:
            return jsonify({'message': 'User not found'}), 404
        
        return jsonify({'message': 'Profile updated successfully'})
    except Exception as e:
        return jsonify({'message': str(e)}), 500
    finally:
        if client:
            client.close()

# Change password
@user_bp.route('/password/change', methods=['POST'])
@login_required
def change_password():
    client, db = get_db()
    if db is None:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        # Get request data
        data = request.json
        current_password = data.get('currentPassword', '').strip()
        new_password = data.get('newPassword', '').strip()
        
        if not current_password or not new_password:
            return jsonify({'message': 'Mật khẩu không được để trống'}), 400
        
        # Get user from session
        user_id = session.get('user_id')
        
        # Find user
        try:
            user = db.users.find_one({'_id': ObjectId(user_id)})
        except:
            try:
                user_id_int = int(user_id)
                user = db.users.find_one({'id': user_id_int})
            except:
                return jsonify({'message': 'Người dùng không tồn tại'}), 404
        
        if not user:
            return jsonify({'message': 'Người dùng không tồn tại'}), 404
        
        # Verify current password with improved handling
        stored_password = user.get('password', '')
        print(f"Debug - Password check: User ID {user_id}, Input length {len(current_password)}, Stored length {len(stored_password)}")
        
        # Compare passwords with normalization
        if stored_password.strip() != current_password:
            return jsonify({'message': 'Mật khẩu hiện tại không đúng'}), 400
        
        # Update password
        update_result = None
        try:
            update_result = db.users.update_one(
                {'_id': ObjectId(user_id)},
                {'$set': {'password': new_password, 'updatedAt': datetime.utcnow()}}
            )
        except:
            try:
                user_id_int = int(user_id)
                update_result = db.users.update_one(
                    {'id': user_id_int},
                    {'$set': {'password': new_password, 'updatedAt': datetime.utcnow()}}
                )
            except:
                return jsonify({'message': 'Lỗi khi cập nhật mật khẩu'}), 500
        
        if update_result and update_result.matched_count > 0:
            return jsonify({'message': 'Mật khẩu đã được cập nhật thành công'})
        else:
            return jsonify({'message': 'Lỗi khi cập nhật mật khẩu'}), 500
            
    except Exception as e:
        return jsonify({'message': str(e)}), 500
    finally:
        if client:
            client.close()

# Get user favorites
@user_bp.route('/favorites')
@login_required
def get_favorites():
    client, db = get_db()
    if db is None:
        return jsonify([])
    
    try:
        # Get user from session
        user_id = session.get('user_id')
        
        # Use Favorite model if available, otherwise use direct database access
        if Favorite:
            # Use the model
            user_id_str = str(user_id)
            favorites_data = Favorite.get_user_favorites(user_id_str)
            
            film_ids = [fav.get('film_id') for fav in favorites_data]
            
            # Get film details for each favorite
            films = []
            for film_id in film_ids:
                film = Film.get_by_id(film_id)
                if film:
                    films.append(film)
            
            return jsonify(films)
        else:
            # Direct database access (legacy code)
            # Find favorites for this user
            favorites = list(db.favorites.find({"user_id": user_id}))
            
            if not favorites:
                return jsonify([])
            
            # Get film IDs from favorites
            film_ids = [fav.get('film_id') for fav in favorites]
            
            # Fetch films by those IDs
            films = []
            for film_id in film_ids:
                try:
                    # Try numerical ID first
                    try:
                        film_id_int = int(film_id)
                        film = db.films.find_one({"id": film_id_int})
                    except:
                        # Then try ObjectId
                        try:
                            film = db.films.find_one({"_id": ObjectId(film_id)})
                        except:
                            continue
                    
                    if film:
                        # Convert ObjectId to string
                        if '_id' in film:
                            film['_id'] = str(film['_id'])
                        films.append(film)
                except Exception as e:
                    print(f"Error getting film {film_id}: {str(e)}")
                    continue
            
            return jsonify(films)
    except Exception as e:
        print(f"Error getting favorites: {str(e)}")
        return jsonify([])
    finally:
        if client:
            client.close()

# Check if a film is in favorites
@user_bp.route('/favorites/check/<film_id>')
@login_required
def check_favorite(film_id):
    client, db = get_db()
    if db is None:
        return jsonify({"isFavorite": False})
    
    try:
        user_id = session.get('user_id')
        
        # Use either model or direct DB access
        if Favorite:
            user_id_str = str(user_id)
            is_favorite = Favorite.is_favorite(user_id_str, film_id)
            return jsonify({"isFavorite": is_favorite})
        else:
            # Convert ObjectId if needed
            try:
                user_id_obj = ObjectId(user_id)
            except:
                user_id_obj = user_id
                
            # Try to find a favorite with this user and film
            favorite = db.favorites.find_one({
                "user_id": user_id_obj,
                "film_id": film_id
            })
            
            return jsonify({"isFavorite": favorite is not None})
    except Exception as e:
        print(f"Error checking favorite: {str(e)}")
        return jsonify({"isFavorite": False})
    finally:
        if client:
            client.close()

# Toggle favorite film
@user_bp.route('/favorites/toggle/<film_id>', methods=['POST'])
@login_required
def toggle_favorite(film_id):
    client, db = get_db()
    if db is None:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        # Get user from session
        user_id = session.get('user_id')
        
        # Check if film exists
        film = None
        try:
            # Try numeric ID first
            try:
                film_id_int = int(film_id)
                film = db.films.find_one({'id': film_id_int})
                if film:
                    film_id = film_id_int  # Use numeric ID if found
            except:
                # Then try ObjectId
                try:
                    film = db.films.find_one({'_id': ObjectId(film_id)})
                    if film:
                        film_id = str(film['_id'])  # Use string ID if found
                except:
                    pass
        except Exception as e:
            print(f"Error checking film {film_id}: {str(e)}")
        
        if not film:
            return jsonify({'message': 'Phim không tồn tại'}), 404
            
        # Check if this film is already in favorites
        try:
            user_id_obj = ObjectId(user_id)
        except:
            user_id_obj = user_id
            
        favorite = db.favorites.find_one({
            "user_id": user_id_obj,
            "film_id": film_id
        })
        
        # If it exists, remove it
        if favorite:
            db.favorites.delete_one({"_id": favorite["_id"]})
            action = 'removed'
        else:
            # If not, add it
            db.favorites.insert_one({
                "user_id": user_id_obj,
                "film_id": film_id,
                "added_at": datetime.now()
            })
            action = 'added'
        
        return jsonify({'message': f'Phim đã được {action}', 'action': action})
            
    except Exception as e:
        return jsonify({'message': str(e)}), 500
    finally:
        if client:
            client.close()

@user_bp.route('/profile/data')
@login_required
def get_profile_data():
    """Get user profile data as JSON"""
    client, db = get_db()
    if db is None:
        return jsonify({
            'username': session.get('username', 'User'),
            'error': 'Database connection failed'
        })
    
    try:
        user_id = session.get('user_id')
        
        # Find user by ID
        try:
            # Try as ObjectId first
            user = db.users.find_one({'_id': ObjectId(user_id)})
        except:
            try:
                # Try as numeric ID
                user_id_int = int(user_id)
                user = db.users.find_one({'id': user_id_int})
            except:
                user = None
        
        if not user:
            return jsonify({
                'username': session.get('username', 'User'),
                'error': 'User not found'
            })
        
        # Format register date
        register_date = user.get('registerDate')
        if register_date:
            if isinstance(register_date, str):
                try:
                    register_date = datetime.fromisoformat(register_date)
                except ValueError:
                    try:
                        register_date = datetime.strptime(register_date, '%Y-%m-%dT%H:%M:%S.%fZ')
                    except ValueError:
                        pass
        
        # Return user data
        return jsonify({
            'username': user.get('username', 'User'),
            'email': user.get('email', ''),
            'fullName': user.get('fullName', ''),
            'registerDate': register_date.isoformat() if isinstance(register_date, datetime) else str(register_date) if register_date else None
        })
    except Exception as e:
        print(f"Error getting user profile: {str(e)}")
        return jsonify({
            'username': session.get('username', 'User'),
            'error': str(e)
        })
    finally:
        if client:
            client.close()

def register_user_routes(app):
    """Register user routes with the Flask application"""
    app.register_blueprint(user_bp)

