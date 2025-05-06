import os
import shutil
import logging

logger = logging.getLogger(__name__)

def create_static_files():
    """Initialize necessary static files for the application"""
    # Ensure static directories exist
    directories = [
        'static/css',
        'static/js',
        'static/images',
        'static/uploads'
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        logger.info(f"Ensured directory exists: {directory}")
    
    # Copy default avatar if it doesn't exist
    default_avatar = 'static/images/avatar_default.png'
    if not os.path.exists(default_avatar):
        # Create a simple placeholder image or copy from resources
        try:
            # This is a placeholder. In a real implementation, you'd have a default avatar image
            with open(default_avatar, 'w') as f:
                f.write("placeholder for avatar")
            logger.info(f"Created placeholder avatar at {default_avatar}")
        except Exception as e:
            logger.error(f"Failed to create default avatar: {str(e)}")
