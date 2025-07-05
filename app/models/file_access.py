from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class FileAccess(db.Model):
    __tablename__ = 'file_access'

    id = db.Column(db.Integer, primary_key=True)
    file_id = db.Column(db.Integer, db.ForeignKey('files.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    granted_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    granted_at = db.Column(db.DateTime, default=datetime.utcnow)