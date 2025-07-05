"""
User model for the application.
Handles user authentication and relationships with other models.
"""

from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from app.extensions import db, bcrypt
from app.models.role import RoleEnum

class User(UserMixin, db.Model):
    """User model for storing user account information."""
    
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    name = db.Column(db.String(128), nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    
    # Account status
    is_verified = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    role = db.Column(db.Enum(RoleEnum), nullable=False, default=RoleEnum.USER)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login_at = db.Column(db.DateTime)
    email_confirmed_at = db.Column(db.DateTime)
    
    # Relationships - removed conflicting backref
    owned_files = db.relationship('File', foreign_keys='File.owner_id', lazy='dynamic',
                                cascade='all, delete-orphan')

    def __init__(self, **kwargs):
        """Initialize a new user."""
        super(User, self).__init__(**kwargs)
        if 'password' in kwargs:
            self.set_password(kwargs['password'])

    def set_password(self, password):
        """Set the user's password."""
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        """Check if the provided password matches the user's password."""
        return bcrypt.check_password_hash(self.password_hash, password)

    def update_last_login(self):
        """Update the last login timestamp."""
        self.last_login_at = datetime.utcnow()
        db.session.commit()

    @property
    def is_admin(self):
        """Check if the user has admin role."""
        return self.role == RoleEnum.ADMIN

    def to_dict(self, include_email=False):
        """Convert user object to dictionary."""
        data = {
            'id': self.id,
            'name': self.name,
            'role': self.role.value,
            'is_verified': self.is_verified,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_login_at': self.last_login_at.isoformat() if self.last_login_at else None
        }
        if include_email:
            data['email'] = self.email
        return data

    def __repr__(self):
        """String representation of the user."""
        return f'<User {self.email}>'

