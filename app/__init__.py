import os
from flask import Flask
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_mail import Mail
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_cors import CORS

from app.extensions import db
from app.config import config
from app.utils.filters import register_filters
from app.utils.error_handlers import register_error_handlers
from app.cli import register_commands

# Initialize extensions
migrate = Migrate()
jwt = JWTManager()
mail = Mail()
login_manager = LoginManager()
bcrypt = Bcrypt()
cors = CORS()

def create_app(config_name=None):
    app = Flask(__name__)

    # Load the default configuration if none is specified
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')
    
    # Load configuration
    app.config.from_object(config[config_name])

    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    mail.init_app(app)
    login_manager.init_app(app)
    bcrypt.init_app(app)
    
    # Initialize CORS with proper configuration
    cors.init_app(app, resources={
        r"/api/*": {"origins": "*"},
        r"/files/*": {"origins": "*"},
        r"/auth/*": {"origins": "*"},
        r"/users/*": {"origins": "*"}
    })

    # Configure login manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'

    # Ensure upload directory exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Register custom filters
    register_filters(app)

    # Register error handlers
    register_error_handlers(app)

    # Register CLI commands
    register_commands(app)

    # Register blueprints
    from app.routes import register_blueprints
    register_blueprints(app)

    # Initialize models
    with app.app_context():
        from app import models
        db.create_all()

    return app

@login_manager.user_loader
def load_user(user_id):
    from app.models import User
    return User.query.get(int(user_id))

