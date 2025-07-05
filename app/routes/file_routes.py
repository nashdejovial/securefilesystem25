"""
File-related routes for handling file uploads, downloads, sharing, and transfers.
"""

import os
import shutil
import zipfile
from flask import Blueprint, request, jsonify, send_file, current_app
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename
from datetime import datetime

from app.extensions import db
from app.models import File, User
from app.models.role import has_permission
from app.utils.decorators import require_permission

# Initialize blueprint
file_bp = Blueprint('file', __name__)

# Configure allowed file extensions
ALLOWED_EXTENSIONS = {
    'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 
    'xls', 'xlsx', 'ppt', 'pptx', 'zip', 'rar', '7z', 'tar', 'gz',
    'mp3', 'mp4', 'avi', 'mov', 'wav', 'csv', 'json', 'xml'
}
MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB

def allowed_file(filename):
    """Check if the file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def create_user_directory(user_id):
    """Create user-specific upload directory."""
    upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], str(user_id))
    os.makedirs(upload_dir, exist_ok=True)
    return upload_dir

@file_bp.route('/upload', methods=['POST'])
@login_required
@require_permission('upload_files')
def upload_file():
    """Handle single file upload."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    
    if not file or not file.filename:
        return jsonify({'error': 'No file selected'}), 400
    
    # Check file size before processing
    file.seek(0, 2)  # Seek to end of file
    file_size = file.tell()
    file.seek(0)  # Reset to beginning
    
    if file_size > MAX_CONTENT_LENGTH:
        return jsonify({'error': f'File size exceeds maximum allowed size of {MAX_CONTENT_LENGTH // (1024*1024)}MB'}), 400
        
    if not allowed_file(file.filename):
        return jsonify({'error': f'File type not allowed. Allowed types: {", ".join(ALLOWED_EXTENSIONS)}'}), 400

    try:
        original_filename = file.filename
        filename = secure_filename(original_filename)
        
        # Ensure filename is not empty after sanitization
        if not filename:
            return jsonify({'error': 'Invalid filename'}), 400
            
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S_')
        unique_filename = timestamp + filename
        
        # Create user directory
        upload_dir = create_user_directory(current_user.id)
        file_path = os.path.join(upload_dir, unique_filename)
        
        # Check if upload directory is writable
        if not os.access(upload_dir, os.W_OK):
            current_app.logger.error(f'Upload directory not writable: {upload_dir}')
            return jsonify({'error': 'Server configuration error: upload directory not accessible'}), 500
        
        # Save file
        file.save(file_path)
        
        # Verify file was saved successfully
        if not os.path.exists(file_path):
            current_app.logger.error(f'File was not saved successfully: {file_path}')
            return jsonify({'error': 'File upload failed: could not save file'}), 500
        
        # Create file record in database
        new_file = File(
            filename=unique_filename,
            original_filename=original_filename,
            path=os.path.relpath(file_path, current_app.config["UPLOAD_FOLDER"]).replace("\\", "/"),
            owner_id=current_user.id,
            size=os.path.getsize(file_path),
            mime_type=file.content_type
        )
        db.session.add(new_file)
        db.session.commit()        
        current_app.logger.info(f'File uploaded successfully: {unique_filename} by user {current_user.id}')
        
        return jsonify({
            'message': 'File uploaded successfully',
            'file': new_file.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error uploading file: {str(e)}')
        return jsonify({'error': 'An error occurred while uploading the file'}), 500

@file_bp.route('/upload-folder', methods=['POST'])
@login_required
@require_permission('upload_files')
def upload_folder():
    """Handle folder upload (multiple files)."""
    if 'files' not in request.files:
        return jsonify({'error': 'No files provided'}), 400

    files = request.files.getlist('files')
    folder_name = request.form.get('folder_name', 'uploaded_folder')
    
    if not files:
        return jsonify({'error': 'No files selected'}), 400

    uploaded_files = []
    errors = []

    try:
        # Create user directory
        upload_dir = create_user_directory(current_user.id)
        folder_path = os.path.join(upload_dir, secure_filename(folder_name))
        os.makedirs(folder_path, exist_ok=True)

        for file in files:
            if file and file.filename:
                if allowed_file(file.filename):
                    try:
                        original_filename = file.filename
                        filename = secure_filename(original_filename)
                        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S_')
                        unique_filename = timestamp + filename
                        
                        file_path = os.path.join(folder_path, unique_filename)
                        file.save(file_path)
                        
                        # Create file record
                        new_file = File(
                            filename=unique_filename,
                            original_filename=original_filename,
                            path=os.path.relpath(file_path, current_app.config["UPLOAD_FOLDER"]).replace("\\", "/"),
                            owner_id=current_user.id,
                            size=os.path.getsize(file_path),
                            mime_type=file.content_type
                        )
                        
                        db.session.add(new_file)
                        uploaded_files.append(new_file.to_dict())
                        
                    except Exception as e:
                        errors.append(f'Error uploading {file.filename}: {str(e)}')
                else:
                    errors.append(f'File type not allowed: {file.filename}')

        db.session.commit()
        
        return jsonify({
            'message': f'Folder uploaded successfully. {len(uploaded_files)} files uploaded.',
            'files': uploaded_files,
            'errors': errors
        }), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error uploading folder: {str(e)}')
        return jsonify({'error': 'An error occurred while uploading the folder'}), 500

@file_bp.route('/', methods=['GET'])
@login_required
def list_files():
    """Get list of user's files and shared files."""
    try:
        # Get user's own files
        owned_files = File.query.filter_by(owner_id=current_user.id, is_deleted=False).all()
        
        # Get files shared with user
        shared_files = current_user.shared_files.filter_by(is_deleted=False).all()
        
        return jsonify({
            'owned_files': [file.to_dict() for file in owned_files],
            'shared_files': [file.to_dict(include_sharing=True) for file in shared_files]
        }), 200
        
    except Exception as e:
        current_app.logger.error(f'Error listing files: {str(e)}')
        return jsonify({'error': 'An error occurred while retrieving files'}), 500

@file_bp.route('/<int:file_id>', methods=['GET'])
@login_required
@require_permission('download_files')
def download_file(file_id):
    """Download a specific file."""
    try:
        file = File.query.get_or_404(file_id)
        
        if not file.can_access(current_user):
            return jsonify({'error': 'Unauthorized access'}), 403
            
        # Reconstruct absolute path
        absolute_file_path = os.path.join(current_app.config["UPLOAD_FOLDER"], file.path)

        if not os.path.exists(absolute_file_path):
            return jsonify({"error": "File not found on server"}), 404
            
        # Update last accessed time
        file.update_last_accessed()
            
        return send_file(
            absolute_file_path,
            as_attachment=True,
            download_name=file.original_filename,
            mimetype=file.mime_type
        )
    except Exception as e:
        current_app.logger.error(f'Error downloading file: {str(e)}')
        return jsonify({'error': 'An error occurred while downloading the file'}), 500

@file_bp.route('/<int:file_id>', methods=['DELETE'])
@login_required
def delete_file(file_id):
    """Delete a specific file."""
    try:
        file = File.query.get_or_404(file_id)
        
        # Check if user can delete this file (more restrictive logic)
        from app.models.role import RoleEnum
        can_delete = (
            file.can_delete_file(current_user) or  # Owner or explicit shared permission
            (current_user.role == RoleEnum.ADMIN) or  # Only admins can delete any file
            (has_permission(current_user, 'delete_files') and file.owner_id == current_user.id)  # Others can only delete own files
        )
        
        if not can_delete:
            return jsonify({'error': 'Unauthorized access'}), 403
            
        # Soft delete first
        file.soft_delete()
        
        # Delete physical file
        try:
            absolute_file_path = os.path.join(current_app.config["UPLOAD_FOLDER"], file.path)
            if os.path.exists(absolute_file_path):
                os.remove(absolute_file_path)
        except OSError:
            current_app.logger.warning(f'Could not delete file from disk: {absolute_file_path}')
            
        db.session.commit()
        
        return jsonify({'message': 'File deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error deleting file: {str(e)}')
        return jsonify({'error': 'An error occurred while deleting the file'}), 500

@file_bp.route('/<int:file_id>/share', methods=['POST'])
@login_required
@require_permission('share_files')
def share_file(file_id):
    """Share a file with another user."""
    try:
        file = File.query.get_or_404(file_id)
        
        if file.owner_id != current_user.id:
            return jsonify({'error': 'Only file owner can share files'}), 403
            
        data = request.get_json()
        if not data or 'email' not in data:
            return jsonify({'error': 'No email provided'}), 400
            
        user_to_share_with = User.query.filter_by(email=data['email']).first()
        if not user_to_share_with:
            return jsonify({'error': 'User not found'}), 404
            
        if user_to_share_with.id == current_user.id:
            return jsonify({'error': 'Cannot share file with yourself'}), 400
            
        if user_to_share_with in file.shared_with:
            return jsonify({'error': 'File already shared with this user'}), 400
            
        # Add sharing permissions
        can_write = data.get('can_write', False)
        can_delete = data.get('can_delete', False)
        
        file.shared_with.append(user_to_share_with)
        db.session.commit()
        
        return jsonify({'message': 'File shared successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error sharing file: {str(e)}')
        return jsonify({'error': 'An error occurred while sharing the file'}), 500

@file_bp.route('/<int:file_id>/transfer', methods=['POST'])
@login_required
def transfer_file(file_id):
    """Transfer file ownership to another user."""
    try:
        file = File.query.get_or_404(file_id)
        
        if file.owner_id != current_user.id:
            return jsonify({'error': 'Only file owner can transfer files'}), 403
            
        data = request.get_json()
        if not data or 'email' not in data:
            return jsonify({'error': 'No email provided'}), 400
            
        new_owner = User.query.filter_by(email=data['email']).first()
        if not new_owner:
            return jsonify({'error': 'User not found'}), 404
            
        if new_owner.id == current_user.id:
            return jsonify({'error': 'Cannot transfer file to yourself'}), 400

        # Create new owner's directory if it doesn't exist
        new_owner_dir = create_user_directory(new_owner.id)
        
        # Move file to new owner's directory
        old_path = os.path.join(current_app.config["UPLOAD_FOLDER"], file.path)
        new_filename = os.path.basename(file.filename)
        new_path = os.path.join(new_owner_dir, new_filename)
        
        # Handle filename conflicts
        counter = 1
        base_name, ext = os.path.splitext(new_filename)
        while os.path.exists(new_path):
            new_filename = f"{base_name}_{counter}{ext}"
            new_path = os.path.join(new_owner_dir, new_filename)
            counter += 1
        
        # Move the physical file
        shutil.move(old_path, new_path)
        
        # Update file record with relative path
        file.path = os.path.relpath(new_path, current_app.config["UPLOAD_FOLDER"]).replace("\\", "/")
        file.filename = new_filename
        file.transfer_ownership(new_owner)
        
        db.session.commit()
        
        return jsonify({'message': 'File transferred successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error transferring file: {str(e)}')
        return jsonify({'error': 'An error occurred while transferring the file'}), 500

@file_bp.route('/<int:file_id>/unshare', methods=['POST'])
@login_required
def unshare_file(file_id):
    """Remove file sharing with a user."""
    try:
        file = File.query.get_or_404(file_id)
        
        if file.owner_id != current_user.id:
            return jsonify({'error': 'Only file owner can manage sharing'}), 403
            
        data = request.get_json()
        if not data or 'email' not in data:
            return jsonify({'error': 'No email provided'}), 400
            
        user_to_unshare = User.query.filter_by(email=data['email']).first()
        if not user_to_unshare:
            return jsonify({'error': 'User not found'}), 404
            
        if user_to_unshare not in file.shared_with:
            return jsonify({'error': 'File is not shared with this user'}), 400
            
        file.shared_with.remove(user_to_unshare)
        db.session.commit()
        
        return jsonify({'message': 'File unshared successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error unsharing file: {str(e)}')
        return jsonify({'error': 'An error occurred while unsharing the file'}), 500

@file_bp.route('/bulk-download', methods=['POST'])
@login_required
def bulk_download():
    """Download multiple files as a zip archive."""
    try:
        data = request.get_json()
        if not data or 'file_ids' not in data:
            return jsonify({'error': 'No file IDs provided'}), 400
            
        file_ids = data['file_ids']
        if not file_ids:
            return jsonify({'error': 'No files selected'}), 400
            
        files = File.query.filter(File.id.in_(file_ids)).all()
        accessible_files = [f for f in files if f.can_access(current_user)]
        
        if not accessible_files:
            return jsonify({'error': 'No accessible files found'}), 404
            
        # Create temporary zip file
        import tempfile
        temp_dir = tempfile.mkdtemp()
        zip_path = os.path.join(temp_dir, 'files.zip')
        
        with zipfile.ZipFile(zip_path, 'w') as zip_file:
            for file in accessible_files:
                absolute_file_path = os.path.join(current_app.config["UPLOAD_FOLDER"], file.path)
                if os.path.exists(absolute_file_path):
                    zip_file.write(absolute_file_path, file.original_filename)
                    file.update_last_accessed()
        
        return send_file(
            zip_path,
            as_attachment=True,
            download_name='files.zip',
            mimetype='application/zip'
        )
        
    except Exception as e:
        current_app.logger.error(f'Error creating bulk download: {str(e)}')
        return jsonify({'error': 'An error occurred while creating the download'}), 500

