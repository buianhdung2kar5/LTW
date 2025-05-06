from flask import render_template, redirect, url_for, request, flash, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from bson.objectid import ObjectId
import os
from pymongo import MongoClient
import logging
from datetime import datetime

# Set up logging
logger = logging.getLogger(__name__)

def register_auth_routes(app):
    """Register authentication routes with the Flask application"""
    
    # Connect to MongoDB
    def get_db_connection():
        uri = os.environ.get('MONGO_URI', "mongodb+srv://kiwi:trang%402005@film-users.10h2w59.mongodb.net/?retryWrites=true&w=majority")
        dbname = os.environ.get('MONGO_DBNAME', "film-users")
        client = MongoClient(uri)
        db = client[dbname]
        return client, db
    
    @app.route('/auth/login', methods=['GET', 'POST'])
    def login():
        """Login route"""
        if request.method == 'POST':
            # Check if it's an AJAX request
            is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
            
            username = request.form.get('username')
            password = request.form.get('password')
            
            # Debug info
            logger.info(f"Login attempt for username: {username}")
            
            # Validate input
            if not username or not password:
                if is_ajax:
                    return jsonify({'success': False, 'message': 'Vui lòng nhập đầy đủ thông tin'})
                flash('Vui lòng nhập đầy đủ thông tin')
                return render_template('login.html')
            
            try:
                # Connect to DB
                client, db = get_db_connection()
                
                # Find user
                user = db.users.find_one({'username': username})
                
                if not user:
                    logger.info(f"User not found: {username}")
                    if is_ajax:
                        return jsonify({'success': False, 'message': 'Tên đăng nhập hoặc mật khẩu không đúng'})
                    flash('Tên đăng nhập hoặc mật khẩu không đúng')
                    return render_template('login.html')
                
                # Check if it's a plain text password in development database
                stored_password = user.get('password', '')
                password_match = False
                
                # Try direct comparison first (for plain text passwords in dev)
                if password == stored_password:
                    password_match = True
                    logger.info("Login with plain text password")
                # Then try hashed password verification
                elif check_password_hash(stored_password, password):
                    password_match = True
                    logger.info("Login with hashed password")
                
                if password_match:
                    # Login successful
                    session['user_id'] = str(user['_id'])
                    session['username'] = user['username']
                    session['role'] = user.get('role', 'user')
                    
                    logger.info(f"Login successful for user: {username}")
                    
                    if is_ajax:
                        return jsonify({
                            'success': True, 
                            'message': 'Đăng nhập thành công!',
                            'username': user['username']
                        })
                    
                    # Redirect to appropriate page based on role
                    if user.get('role') in ['admin', 'moderator']:
                        return redirect(url_for('films_manager'))
                    return redirect(url_for('home'))
                else:
                    # Login failed - password doesn't match
                    logger.info(f"Password mismatch for user: {username}")
                    if is_ajax:
                        return jsonify({'success': False, 'message': 'Tên đăng nhập hoặc mật khẩu không đúng'})
                    flash('Tên đăng nhập hoặc mật khẩu không đúng')
            except Exception as e:
                logger.error(f"Login error: {str(e)}")
                if is_ajax:
                    return jsonify({'success': False, 'message': 'Lỗi đăng nhập. Vui lòng thử lại sau.'})
                flash('Lỗi đăng nhập. Vui lòng thử lại sau.')
            finally:
                if 'client' in locals():
                    client.close()
                    
        return render_template('login.html')
        
    @app.route('/auth/register', methods=['GET', 'POST'])
    def register():
        """Register route"""
        if request.method == 'POST':
            # Check if it's an AJAX request
            is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
            
            username = request.form.get('username')
            password = request.form.get('password')
            confirm_password = request.form.get('confirm-password')
            
            # Validate input
            if not username or not password or not confirm_password:
                if is_ajax:
                    return jsonify({'success': False, 'message': 'Vui lòng nhập đầy đủ thông tin'})
                flash('Vui lòng nhập đầy đủ thông tin')
                return render_template('register.html')
                
            if password != confirm_password:
                if is_ajax:
                    return jsonify({'success': False, 'message': 'Mật khẩu không khớp'})
                flash('Mật khẩu không khớp')
                return render_template('register.html')
            
            try:
                # Connect to DB
                client, db = get_db_connection()
                
                # Check if username already exists
                existing_user = db.users.find_one({'username': username})
                if existing_user:
                    if is_ajax:
                        return jsonify({'success': False, 'message': 'Tên đăng nhập đã tồn tại'})
                    flash('Tên đăng nhập đã tồn tại')
                    return render_template('register.html')
                
                # Create new user
                new_user = {
                    'username': username,
                    'password': generate_password_hash(password),
                    'role': 'user',
                    'status': 'active',
                    'avatar': '/static/images/avatar_user.png',  # Default avatar
                    'registerDate': datetime.now()
                }
                
                result = db.users.insert_one(new_user)
                user_id = str(result.inserted_id)
                
                # Auto login after registration
                session['user_id'] = user_id
                session['username'] = username
                session['role'] = 'user'
                
                if is_ajax:
                    return jsonify({
                        'success': True, 
                        'message': 'Đăng ký thành công!',
                        'username': username
                    })
                    
                return redirect(url_for('home'))
                
            except Exception as e:
                logger.error(f"Registration error: {str(e)}")
                if is_ajax:
                    return jsonify({'success': False, 'message': 'Lỗi đăng ký. Vui lòng thử lại sau.'})
                flash('Lỗi đăng ký. Vui lòng thử lại sau.')
            finally:
                if 'client' in locals():
                    client.close()
                    
        return render_template('register.html')
        
    @app.route('/auth/logout')
    def logout():
        """Logout route"""
        session.clear()
        return jsonify({'success': True}) if request.headers.get('X-Requested-With') == 'XMLHttpRequest' else redirect(url_for('home'))
    
    @app.route('/auth/user-info')
    def user_info():
        """API endpoint to check if user is logged in"""
        if 'user_id' in session and 'username' in session:
            return jsonify({
                'isLoggedIn': True,
                'username': session['username'],
                'role': session.get('role', 'user')
            })
        return jsonify({'isLoggedIn': False})
        
    # Add route to handle 404 errors for Chrome DevTools
    @app.route('/.well-known/appspecific/com.chrome.devtools.json')
    def handle_chrome_devtools():
        return jsonify({'status': 'ok'})
