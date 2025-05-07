from flask import jsonify
from werkzeug.security import generate_password_hash
import os
from pymongo import MongoClient
from datetime import datetime
import logging

# Set up logging
logger = logging.getLogger(__name__)

def register_debug_routes(app):
    """Register debug routes with the Flask application (only for development)"""
    
    @app.route('/debug/create-test-user')
    def create_test_user():
        """Create a test user for login testing"""
        if app.config.get('ENV') != 'development':
            return jsonify({'error': 'This route is only available in development mode'})
            
        try:
            # Connect to MongoDB
            uri = os.environ.get('MONGO_URI', "mongodb+srv://kiwi:trang%402005@film-users.10h2w59.mongodb.net/?retryWrites=true&w=majority")
            dbname = os.environ.get('MONGO_DBNAME', "film-users")
            client = MongoClient(uri)
            db = client[dbname]
            
            # Create and check test users
            results = {}
            
            def create_test_user_if_not_exists(username, password, role='user', hash_password=True):
                existing_user = db.users.find_one({'username': username})
                if existing_user:
                    return False, {
                        'username': username,
                        'password': password,
                        'user_id': str(existing_user['_id'])
                    }
                
                user_data = {
                    'username': username,
                    'password': generate_password_hash(password) if hash_password else password,
                    'role': role,
                    'status': 'active',
                    'avatar': '/static/images/avatar_user.png',
                    'registerDate': datetime.now()
                }
                result = db.users.insert_one(user_data)
                return True, {
                    'username': username,
                    'password': password,
                    'user_id': str(result.inserted_id)
                }
            
            # Create regular test user
            is_new, user_data = create_test_user_if_not_exists("testuser", "password123")
            if not is_new:
                return jsonify({
                    'message': 'Test user already exists',
                    **user_data
                })
            results['test_user'] = user_data
            
            # Create admin test user
            _, admin_data = create_test_user_if_not_exists("admin", "admin123", "admin")
            results['admin_user'] = admin_data
            
            # Create plain text password user
            _, plain_data = create_test_user_if_not_exists("plainuser", "pass123", "user", False)
            results['plain_text_user'] = plain_data
            
            return jsonify({
                'message': 'Test users created successfully',
                **results
            })
            
        except Exception as e:
            logger.error(f"Error creating test user: {str(e)}")
            return jsonify({'error': str(e)})
        finally:
            if 'client' in locals():
                client.close()
