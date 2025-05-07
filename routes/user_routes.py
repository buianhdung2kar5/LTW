from flask import Blueprint, render_template, request, session, jsonify, redirect, url_for, flash
from bson.objectid import ObjectId
from functools import wraps
import os
from datetime import datetime
from werkzeug.security import check_password_hash

# Import Favorite model từ module favorite
from models.favorite import Favorite

# Tạo Blueprint
user_bp = Blueprint('user', __name__, url_prefix='/user')

# MongoDB connection function
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

# Helper function to find user by ID
def find_user_by_id(db, user_id):
    try:
        # Try to find by ObjectId first
        user = db.users.find_one({'_id': ObjectId(user_id)})
        if user:
            return user
            
        # Try numeric ID if ObjectId fails
        user_id_int = int(user_id)
        return db.users.find_one({'id': user_id_int})
    except:
        return None

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
        
        # Sử dụng Favorite model đã import
        favorites_data = Favorite.get_user_favorites(user_id)
        films = Favorite.get_user_favorite_films(user_id)
        
        if films:
            favorites = films
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
        user = find_user_by_id(db, user_id)
        
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
        full_name = data.get('fullName', '').strip()
        
        # Get user from session
        user_id = session.get('user_id')
        
        # Try to find and update user
        update_data = {'updatedAt': datetime.utcnow()}
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
        user = find_user_by_id(db, user_id)
        
        if not user:
            return jsonify({'message': 'Người dùng không tồn tại'}), 404
        
        # Verify current password with improved handling
        stored_password = user.get('password', '')
        
        # Check password - try both direct comparison (for plain text) and hash verification
        password_match = False
        
        # Try direct comparison first (for plain text passwords in development)
        if current_password == stored_password:
            password_match = True
        # Then try hashed password verification
        elif check_password_hash(stored_password, current_password):
            password_match = True
            
        if not password_match:
            return jsonify({'message': 'Mật khẩu hiện tại không đúng'}), 400
        
        # Update password
        update_result = None
        try:
            if isinstance(user['_id'], ObjectId):
                update_result = db.users.update_one(
                    {'_id': user['_id']},
                    {'$set': {'password': new_password, 'updatedAt': datetime.utcnow()}}
                )
            else:
                update_result = db.users.update_one(
                    {'id': user.get('id')},
                    {'$set': {'password': new_password, 'updatedAt': datetime.utcnow()}}
                )
        except Exception as e:
            return jsonify({'message': f'Lỗi khi cập nhật mật khẩu: {str(e)}'}), 500
        
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
    user_id = session.get('user_id')
    films = Favorite.get_user_favorite_films(user_id)
    return jsonify(films)

# Check if a film is in favorites
@user_bp.route('/favorites/check/<film_id>')
@login_required
def check_favorite(film_id):
    user_id = session.get('user_id')
    is_favorite = Favorite.is_favorite(user_id, film_id)
    return jsonify({"isFavorite": is_favorite})

# Toggle favorite film
@user_bp.route('/favorites/toggle/<film_id>', methods=['POST'])
@login_required
def toggle_favorite(film_id):
    user_id = session.get('user_id')
    result, status_code = Favorite.toggle_favorite(user_id, film_id)
    return jsonify(result), status_code

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
        user = find_user_by_id(db, user_id)
        
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

