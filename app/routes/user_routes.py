"""
User-related routes for profile management and user settings.
"""

from flask import Blueprint, request, jsonify, current_app, render_template, flash, redirect, url_for
from flask_jwt_extended import jwt_required
from flask_login import current_user, login_required, logout_user
from werkzeug.security import generate_password_hash
from datetime import datetime
import os

from app.extensions import db
from app.models import User, File

# Initialize blueprint
user_bp = Blueprint('user', __name__, url_prefix='/users')

@user_bp.route('/profile', methods=['GET'])
@login_required
def profile():
    """Display user profile page."""
    return render_template('user/profile.html')

@user_bp.route('/profile', methods=['GET'])
@login_required
def get_profile():
    """Get current user's profile information (API endpoint)."""
    return jsonify({
        'id': current_user.id,
        'email': current_user.email,
        'name': current_user.name,
        'created_at': current_user.created_at.isoformat(),
        'is_verified': current_user.is_verified,
        'role': current_user.role.value,
        'is_active': current_user.is_active
    }), 200

@user_bp.route('/profile', methods=['PUT', 'POST'])
@login_required
def update_profile():
    """Update current user's profile information."""
    # Handle both JSON and form data
    if request.is_json:
        data = request.get_json()
    else:
        data = request.form.to_dict()
    
    if not data:
        if request.is_json:
            return jsonify({'error': 'No data provided'}), 400
        flash('No data provided', 'error')
        return redirect(url_for('user.profile'))

    try:
        updated = False
        
        if 'name' in data and data['name'].strip():
            if current_user.name != data['name'].strip():
                current_user.name = data['name'].strip()
                updated = True
            
        if 'email' in data and data['email'].strip():
            new_email = data['email'].strip().lower()
            if current_user.email != new_email:
                # Check if email is already in use
                existing_user = User.query.filter_by(email=new_email).first()
                if existing_user and existing_user.id != current_user.id:
                    if request.is_json:
                        return jsonify({'error': 'Email already in use'}), 400
                    flash('Email already in use', 'error')
                    return redirect(url_for('user.profile'))
                
                current_user.email = new_email
                current_user.is_verified = False
                updated = True
                # TODO: Send verification email
        
        if updated:
            current_user.updated_at = datetime.utcnow()
            db.session.commit()
            
            if request.is_json:
                return jsonify({
                    'message': 'Profile updated successfully',
                    'user': {
                        'id': current_user.id,
                        'email': current_user.email,
                        'name': current_user.name,
                        'is_verified': current_user.is_verified
                    }
                }), 200
            else:
                flash('Profile updated successfully', 'success')
                return redirect(url_for('user.profile'))
        else:
            if request.is_json:
                return jsonify({'message': 'No changes made'}), 200
            flash('No changes made', 'info')
            return redirect(url_for('user.profile'))
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error updating profile: {str(e)}')
        if request.is_json:
            return jsonify({'error': 'An error occurred while updating profile'}), 500
        flash('An error occurred while updating profile', 'error')
        return redirect(url_for('user.profile'))

@user_bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    """Change current user's password."""
    # Handle both JSON and form data
    if request.is_json:
        data = request.get_json()
    else:
        data = request.form.to_dict()
    
    if not data or not all(k in data for k in ('current_password', 'new_password')):
        if request.is_json:
            return jsonify({'error': 'Missing required fields'}), 400
        flash('Missing required fields', 'error')
        return redirect(url_for('user.profile'))
    
    # Validate current password using User model method
    if not current_user.check_password(data['current_password']):
        if request.is_json:
            return jsonify({'error': 'Current password is incorrect'}), 400
        flash('Current password is incorrect', 'error')
        return redirect(url_for('user.profile'))
    
    # Validate new password
    if len(data['new_password']) < 6:
        if request.is_json:
            return jsonify({'error': 'New password must be at least 6 characters long'}), 400
        flash('New password must be at least 6 characters long', 'error')
        return redirect(url_for('user.profile'))
        
    try:
        # Use User model method to set password
        current_user.set_password(data['new_password'])
        current_user.updated_at = datetime.utcnow()
        db.session.commit()
        
        if request.is_json:
            return jsonify({'message': 'Password updated successfully'}), 200
        flash('Password updated successfully', 'success')
        return redirect(url_for('user.profile'))
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error changing password: {str(e)}')
        if request.is_json:
            return jsonify({'error': 'An error occurred while changing password'}), 500
        flash('An error occurred while changing password', 'error')
        return redirect(url_for('user.profile'))

@user_bp.route('/delete-account', methods=['DELETE', 'POST'])
@login_required
def delete_account():
    """Delete current user's account."""
    # Handle both JSON and form data
    if request.is_json:
        data = request.get_json()
    else:
        data = request.form.to_dict()
    
    # Verify password for account deletion
    if 'password' in data:
        if not current_user.check_password(data['password']):
            if request.is_json:
                return jsonify({'error': 'Password verification failed'}), 400
            flash('Password verification failed', 'error')
            return redirect(url_for('user.profile'))
    
    try:
        user_id = current_user.id
        
        # Delete user's files first
        for file in current_user.owned_files:
            try:
                if os.path.exists(file.path):
                    os.remove(file.path)
            except OSError:
                current_app.logger.warning(f'Could not delete file: {file.path}')
            db.session.delete(file)
            
        # Delete the user
        db.session.delete(current_user)
        db.session.commit()
        
        # Logout the user
        logout_user()
        
        if request.is_json:
            return jsonify({'message': 'Account deleted successfully'}), 200
        flash('Account deleted successfully', 'success')
        return redirect(url_for('auth.login'))
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error deleting account: {str(e)}')
        if request.is_json:
            return jsonify({'error': 'An error occurred while deleting account'}), 500
        flash('An error occurred while deleting account', 'error')
        return redirect(url_for('user.profile'))

@user_bp.route('/settings', methods=['GET'])
@login_required
def settings():
    """Display user settings page."""
    return render_template('user/settings.html')

@user_bp.route('/files', methods=['GET'])
@login_required
def user_files():
    """Get current user's files."""
    try:
        # Get user's own files
        owned_files = current_user.owned_files.filter_by(is_deleted=False).all()
        
        # Get files shared with user
        shared_files = current_user.shared_files.filter_by(is_deleted=False).all()
        
        files_data = {
            'owned_files': [file.to_dict() for file in owned_files],
            'shared_files': [file.to_dict() for file in shared_files]
        }
        
        if request.is_json:
            return jsonify(files_data), 200
        
        return render_template('files/list.html', 
                             owned_files=owned_files, 
                             shared_files=shared_files)
        
    except Exception as e:
        current_app.logger.error(f'Error retrieving user files: {str(e)}')
        if request.is_json:
            return jsonify({'error': 'An error occurred while retrieving files'}), 500
        flash('An error occurred while retrieving files', 'error')
        return redirect(url_for('main.index'))

@user_bp.route('/stats', methods=['GET'])
@login_required
def user_stats():
    """Get current user's statistics."""
    try:
        owned_files_count = current_user.owned_files.filter_by(is_deleted=False).count()
        shared_files_count = current_user.shared_files.filter_by(is_deleted=False).count()
        
        # Calculate total storage used
        total_storage = sum(file.size for file in current_user.owned_files.filter_by(is_deleted=False))
        
        stats = {
            'owned_files_count': owned_files_count,
            'shared_files_count': shared_files_count,
            'total_storage_bytes': total_storage,
            'total_storage_mb': round(total_storage / (1024 * 1024), 2),
            'account_created': current_user.created_at.isoformat(),
            'last_login': current_user.last_login_at.isoformat() if current_user.last_login_at else None
        }
        
        return jsonify(stats), 200
        
    except Exception as e:
        current_app.logger.error(f'Error retrieving user stats: {str(e)}')
        return jsonify({'error': 'An error occurred while retrieving statistics'}), 500

