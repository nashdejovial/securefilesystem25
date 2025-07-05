"""
File model for managing uploaded files and their metadata.
"""

from datetime import datetime
from app.extensions import db

# File sharing association table
file_shares = db.Table(
    'file_shares',
    db.Column('file_id', db.Integer, db.ForeignKey('files.id', ondelete='CASCADE'), primary_key=True),
    db.Column('user_id', db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
    db.Column('shared_at', db.DateTime, default=datetime.utcnow),
    db.Column('can_write', db.Boolean, default=False),
    db.Column('can_delete', db.Boolean, default=False)
)

class File(db.Model):
    """Model for storing file metadata and managing file access."""
    
    __tablename__ = 'files'

    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    path = db.Column(db.String(512), nullable=False)
    size = db.Column(db.Integer, nullable=False)  # File size in bytes
    mime_type = db.Column(db.String(128))
    
    # File status
    is_public = db.Column(db.Boolean, default=False)
    is_deleted = db.Column(db.Boolean, default=False)
    
    # Ownership and sharing
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_accessed_at = db.Column(db.DateTime)
    deleted_at = db.Column(db.DateTime)

    # Relationships - fixed overlapping warning
    owner = db.relationship('User', foreign_keys=[owner_id], overlaps="owned_files")
    shared_with = db.relationship('User', secondary=file_shares, 
                                backref=db.backref('shared_files', lazy='dynamic'))

    def __init__(self, **kwargs):
        """Initialize a new file record."""
        super(File, self).__init__(**kwargs)
        if 'original_filename' not in kwargs and 'filename' in kwargs:
            self.original_filename = kwargs['filename']
        
        # Only call update_file_info if we have a path and the file should exist
        # Skip during database insertion when file might not exist yet
        if 'path' in kwargs and not kwargs.get('_skip_file_check', False):
            try:
                self.update_file_info()
            except Exception as e:
                # Don't fail initialization if file doesn't exist
                # This can happen during database operations
                pass

    def update_file_info(self):
        """Update file metadata from the actual file."""
        import os
        from flask import current_app
        
        # Handle both relative and absolute paths
        if os.path.isabs(self.path):
            file_path = self.path
        else:
            # Construct absolute path from relative path
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], self.path)
        
        if os.path.exists(file_path):
            self.size = os.path.getsize(file_path)
            # Update last accessed time
            self.last_accessed_at = datetime.utcnow()
        else:
            # Log warning but don't fail - file might not exist yet during creation
            if hasattr(current_app, 'logger'):
                current_app.logger.warning(f'File not found during update_file_info: {file_path}')

    def soft_delete(self):
        """Soft delete the file."""
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()

    def restore(self):
        """Restore a soft-deleted file."""
        self.is_deleted = False
        self.deleted_at = None

    def update_last_accessed(self):
        """Update the last accessed timestamp."""
        self.last_accessed_at = datetime.utcnow()
        db.session.commit()

    def can_access(self, user):
        """Check if a user can access this file."""
        if self.owner_id == user.id:
            return True
        if self.is_public:
            return True
        if user in self.shared_with:
            return True
        # Add role-based access for admins and managers
        from app.models.role import has_permission
        if has_permission(user, 'manage_files'):  # Admin/Manager can access all files
            return True
        return False

    def can_edit(self, user):
        """Check if a user can edit this file."""
        if self.owner_id == user.id:
            return True
        # Check if user has write permissions
        share_record = db.session.query(file_shares).filter_by(
            file_id=self.id, user_id=user.id
        ).first()
        return share_record and share_record.can_write

    def can_delete_file(self, user):
        """Check if a user can delete this file."""
        if self.owner_id == user.id:
            return True
        # Check if user has delete permissions
        share_record = db.session.query(file_shares).filter_by(
            file_id=self.id, user_id=user.id
        ).first()
        return share_record and share_record.can_delete

    def transfer_ownership(self, new_owner):
        """Transfer file ownership to another user."""
        self.owner_id = new_owner.id
        self.updated_at = datetime.utcnow()
        
        # Remove new owner from shared users if they were shared
        if new_owner in self.shared_with:
            self.shared_with.remove(new_owner)

    def to_dict(self, include_path=False, include_sharing=False):
        """Convert file object to dictionary."""
        data = {
            'id': self.id,
            'filename': self.filename,
            'original_filename': self.original_filename,
            'size': self.size,
            'mime_type': self.mime_type,
            'is_public': self.is_public,
            'owner_id': self.owner_id,
            'owner_name': self.owner.name if self.owner else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_accessed_at': self.last_accessed_at.isoformat() if self.last_accessed_at else None
        }
        if include_path:
            data['path'] = self.path
        if include_sharing:
            data['shared_with'] = [
                {
                    'user_id': user.id,
                    'user_name': user.name,
                    'user_email': user.email
                } for user in self.shared_with
            ]
        return data

    def __repr__(self):
        """String representation of the file."""
        return f'<File {self.filename} (owned by {self.owner_id})>'

