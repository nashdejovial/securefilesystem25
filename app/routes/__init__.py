# routes/__init__.py
"""
This module initializes and registers all blueprints for the application.
Each blueprint is registered with its own URL prefix for proper routing organization.
"""

from flask import Blueprint
from .auth import auth_bp
from .user_routes import user_bp
from .file_routes import file_bp
from .main import main_bp

def register_blueprints(app):
    """Register all blueprints with the application."""
    
    # Main routes - handles index page
    app.register_blueprint(main_bp)
    
    # Auth routes - handles login, registration, password reset
    app.register_blueprint(auth_bp, url_prefix='/auth')
    
    # User routes - handles user profile and settings
    app.register_blueprint(user_bp, url_prefix='/users')
    
    # File routes - handles file upload, download, and sharing
    app.register_blueprint(file_bp, url_prefix='/files')

# Export blueprints for use in other modules
__all__ = ['register_blueprints']
