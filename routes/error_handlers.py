from flask import render_template, request
import logging

# Create a logger
logger = logging.getLogger(__name__)

def register_error_handlers(app):
    """Register all error handlers with the app"""
    
    @app.errorhandler(404)
    def page_not_found(e):
        """Handle 404 errors"""
        logger.info(f"404 error: {request.path}")
        return render_template('errors/error.html', 
                              message="Page not found"), 404

    @app.errorhandler(500)
    def server_error(e):
        """Handle 500 errors"""
        logger.error(f"500 error: {str(e)}")
        return render_template('errors/error.html', 
                              message="Internal server error"), 500
                              
    @app.errorhandler(403)
    def forbidden(e):
        """Handle 403 errors"""
        logger.warning(f"403 error: {request.path}")
        return render_template('errors/error.html', 
                              message="Access forbidden"), 403

    @app.errorhandler(400)
    def bad_request(e):
        """Handle 400 errors"""
        logger.warning(f"400 error: {request.path}")
        return render_template('errors/error.html', 
                              message="Yêu cầu không hợp lệ"), 400

    @app.errorhandler(401)
    def unauthorized(e):
        """Handle 401 errors"""
        logger.warning(f"401 error: {request.path}")
        return render_template('errors/error.html', 
                              message="Unauthorized access"), 401
