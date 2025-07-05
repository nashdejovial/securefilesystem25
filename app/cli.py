"""
Command-line interface for managing the application.
"""

import click
from flask.cli import with_appcontext
from werkzeug.security import generate_password_hash

from app.extensions import db
from app.models import User
from app.models.role import RoleEnum

def register_commands(app):
    """Register custom commands with the Flask CLI."""

    @app.cli.command('create-admin')
    @click.argument('email')
    @click.argument('password')
    @with_appcontext
    def create_admin(email, password):
        """Create an admin user."""
        try:
            admin = User(
                email=email,
                name='Admin',
                password_hash=generate_password_hash(password),
                role=RoleEnum.ADMIN,
                is_verified=True,
                is_active=True
            )
            db.session.add(admin)
            db.session.commit()
            click.echo(f'Admin user created successfully: {email}')
        except Exception as e:
            db.session.rollback()
            click.echo(f'Error creating admin user: {str(e)}', err=True)

    @app.cli.command('init-db')
    @with_appcontext
    def init_db():
        """Initialize the database."""
        try:
            db.create_all()
            click.echo('Database initialized successfully.')
        except Exception as e:
            click.echo(f'Error initializing database: {str(e)}', err=True)

    @app.cli.command('drop-db')
    @with_appcontext
    def drop_db():
        """Drop all database tables."""
        if click.confirm('Are you sure you want to drop all tables?'):
            try:
                db.drop_all()
                click.echo('Database tables dropped successfully.')
            except Exception as e:
                click.echo(f'Error dropping database tables: {str(e)}', err=True)

    @app.cli.command('list-users')
    @with_appcontext
    def list_users():
        """List all users in the system."""
        try:
            users = User.query.all()
            if not users:
                click.echo('No users found.')
                return

            click.echo('\nUsers:')
            for user in users:
                click.echo(f'ID: {user.id}')
                click.echo(f'Email: {user.email}')
                click.echo(f'Name: {user.name}')
                click.echo(f'Role: {user.role.value}')
                click.echo(f'Verified: {user.is_verified}')
                click.echo(f'Active: {user.is_active}')
                click.echo('-' * 40)
        except Exception as e:
            click.echo(f'Error listing users: {str(e)}', err=True)

    @app.cli.command('verify-user')
    @click.argument('email')
    @with_appcontext
    def verify_user(email):
        """Verify a user's email address."""
        try:
            user = User.query.filter_by(email=email).first()
            if not user:
                click.echo(f'User not found: {email}', err=True)
                return

            user.is_verified = True
            db.session.commit()
            click.echo(f'User verified successfully: {email}')
        except Exception as e:
            db.session.rollback()
            click.echo(f'Error verifying user: {str(e)}', err=True)

    @app.cli.command('change-role')
    @click.argument('email')
    @click.argument('role')
    @with_appcontext
    def change_role(email, role):
        """Change a user's role."""
        try:
            user = User.query.filter_by(email=email).first()
            if not user:
                click.echo(f'User not found: {email}', err=True)
                return

            try:
                new_role = RoleEnum[role.upper()]
            except KeyError:
                click.echo(f'Invalid role: {role}. Valid roles: {", ".join(r.name for r in RoleEnum)}', err=True)
                return

            user.role = new_role
            db.session.commit()
            click.echo(f'Role changed successfully for {email}: {new_role.value}')
        except Exception as e:
            db.session.rollback()
            click.echo(f'Error changing role: {str(e)}', err=True) 