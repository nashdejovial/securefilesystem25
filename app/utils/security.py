"""
Security utilities for the file sharing application.
"""

import os
import hashlib
import secrets
from functools import wraps
from flask import request, jsonify, current_app
from flask_login import current_user

def generate_secure_filename(original_filename):
    """Generate a secure filename with timestamp and random component."""
    from datetime import datetime
    
    # Extract file extension
    name, ext = os.path.splitext(original_filename)
    
    # Create secure base name
    secure_name = "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).rstrip()
    secure_name = secure_name[:50]  # Limit length
    
    # Add timestamp and random component
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    random_component = secrets.token_hex(4)
    
    return f"{timestamp}_{random_component}_{secure_name}{ext}"

def validate_file_type(filename, allowed_extensions=None):
    """Validate file type based on extension and magic numbers."""
    if allowed_extensions is None:
        allowed_extensions = current_app.config.get('ALLOWED_EXTENSIONS', set())
    
    # Check extension
    if '.' not in filename:
        return False, "File must have an extension"
    
    ext = filename.rsplit('.', 1)[1].lower()
    if ext not in allowed_extensions:
        return False, f"File type '{ext}' not allowed"
    
    return True, "Valid file type"

def validate_file_size(file_size, max_size=None):
    """Validate file size."""
    if max_size is None:
        max_size = current_app.config.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024)
    
    if file_size > max_size:
        return False, f"File size exceeds maximum allowed size of {max_size // (1024*1024)}MB"
    
    return True, "Valid file size"

def sanitize_path(path):
    """Sanitize file path to prevent directory traversal."""
    # Remove any path traversal attempts
    path = path.replace('..', '').replace('/', '').replace('\\', '')
    return path

def calculate_file_hash(file_path):
    """Calculate SHA-256 hash of a file."""
    hash_sha256 = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    except Exception:
        return None

def require_file_access(f):
    """Decorator to check if user has access to a file."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        file_id = kwargs.get('file_id')
        if not file_id:
            return jsonify({'error': 'File ID required'}), 400
        
        from app.models import File
        file = File.query.get(file_id)
        if not file:
            return jsonify({'error': 'File not found'}), 404
        
        if not file.can_access(current_user):
            return jsonify({'error': 'Access denied'}), 403
        
        return f(*args, **kwargs)
    return decorated_function

def require_file_ownership(f):
    """Decorator to check if user owns a file."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        file_id = kwargs.get('file_id')
        if not file_id:
            return jsonify({'error': 'File ID required'}), 400
        
        from app.models import File
        file = File.query.get(file_id)
        if not file:
            return jsonify({'error': 'File not found'}), 404
        
        if file.owner_id != current_user.id:
            return jsonify({'error': 'Access denied - ownership required'}), 403
        
        return f(*args, **kwargs)
    return decorated_function

def log_security_event(event_type, details, user_id=None):
    """Log security-related events."""
    if user_id is None and current_user.is_authenticated:
        user_id = current_user.id
    
    current_app.logger.warning(
        f"SECURITY EVENT: {event_type} - User: {user_id} - Details: {details} - IP: {request.remote_addr}"
    )

class SecurityHeaders:
    """Security headers middleware."""
    
    @staticmethod
    def init_app(app):
        @app.after_request
        def set_security_headers(response):
            headers = app.config.get('SECURITY_HEADERS', {})
            for header, value in headers.items():
                response.headers[header] = value
            return response

