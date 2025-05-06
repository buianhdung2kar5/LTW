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
            
            # Test user details
            username = "testuser"
            password = "password123"
            
            # Check if user already exists
            existing_user = db.users.find_one({'username': username})
            if existing_user:
                return jsonify({
                    'message': 'Test user already exists',
                    'username': username,
                    'password': password,
                    'user_id': str(existing_user['_id'])
                })
            
            # Create test user
            hashed_password = generate_password_hash(password)
            new_user = {
                'username': username,
                'password': hashed_password,
                'role': 'user',
                'status': 'active',
                'avatar': '/static/images/avatar_user.png',
                'registerDate': datetime.now()
            }
            
            result = db.users.insert_one(new_user)
            
            # Also create a test admin user
            admin_username = "admin"
            admin_password = "admin123"
            existing_admin = db.users.find_one({'username': admin_username})
            
            if not existing_admin:
                hashed_admin_password = generate_password_hash(admin_password)
                admin_user = {
                    'username': admin_username,
                    'password': hashed_admin_password,
                    'role': 'admin',
                    'status': 'active',
                    'avatar': '/static/images/avatar_user.png',
                    'registerDate': datetime.now()
                }
                db.users.insert_one(admin_user)
            
            # Also create a user with plain text password for testing
            plain_username = "plainuser"
            plain_password = "pass123"
            existing_plain = db.users.find_one({'username': plain_username})
            
            if not existing_plain:
                plain_user = {
                    'username': plain_username,
                    'password': plain_password,  # Deliberately not hashed for testing
                    'role': 'user',
                    'status': 'active',
                    'avatar': '/static/images/avatar_user.png',
                    'registerDate': datetime.now()
                }
                db.users.insert_one(plain_user)
            
            return jsonify({
                'message': 'Test users created successfully',
                'test_user': {
                    'username': username,
                    'password': password,
                    'user_id': str(result.inserted_id)
                },
                'admin_user': {
                    'username': admin_username,
                    'password': admin_password
                },
                'plain_text_user': {
                    'username': plain_username,
                    'password': plain_password
                }
            })
            
        except Exception as e:
            logger.error(f"Error creating test user: {str(e)}")
            return jsonify({'error': str(e)})
        finally:
            if 'client' in locals():
                client.close()
