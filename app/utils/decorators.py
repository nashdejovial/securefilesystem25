"""
Permission decorators for role-based access control.
"""

from functools import wraps
from flask import jsonify
from flask_login import current_user
from app.models.role import has_permission

def require_permission(permission):
    """Decorator to require a specific permission for a route."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return jsonify({'error': 'Authentication required'}), 401
            
            if not has_permission(current_user, permission):
                return jsonify({'error': f'Permission denied. Required permission: {permission}'}), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def require_role(role):
    """Decorator to require a specific role for a route."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return jsonify({'error': 'Authentication required'}), 401
            
            if current_user.role != role:
                return jsonify({'error': f'Access denied. Required role: {role.value}'}), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def admin_required(f):
    """Decorator to require admin role."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({'error': 'Authentication required'}), 401
        
        if not current_user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        return f(*args, **kwargs)
    return decorated_function

