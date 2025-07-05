"""
Main routes for the application.
"""

from flask import Blueprint, render_template
from flask_login import current_user

# Initialize blueprint
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Render the index page."""
    if current_user.is_authenticated:
        return render_template('files/list.html')
    return render_template('index.html') 