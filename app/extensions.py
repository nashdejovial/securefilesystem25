# extensions.py
"""
This module initializes Flask extensions used throughout the application.
Extensions are initialized here without binding to a specific application instance.
They will be initialized with the application instance in the application factory.
"""

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from flask_mail import Mail
from flask_login import LoginManager

# Database and migrations
db = SQLAlchemy()
migrate = Migrate()

# Security and authentication
bcrypt = Bcrypt()
jwt = JWTManager()
login_manager = LoginManager()

# Email
mail = Mail()