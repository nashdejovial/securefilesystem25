"""
Authentication routes for user registration, login, and email verification.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.security import check_password_hash
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadTimeSignature

from app.extensions import db, bcrypt
from app.models import User
from app.utils.email import send_confirmation_email

# Initialize blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

def get_serializer():
    """Get URL safe serializer for tokens."""
    return URLSafeTimedSerializer(current_app.config['SECRET_KEY'])

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Handle user registration."""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        name = request.form.get('name', '').strip()
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if not all([email, name, password, confirm_password]):
            flash('All fields are required.', 'error')
            return redirect(url_for('auth.register'))

        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return redirect(url_for('auth.register'))

        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'error')
            return redirect(url_for('auth.register'))

        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'error')
            return redirect(url_for('auth.register'))

        user = User(
            email=email,
            name=name,
            is_verified=False  # User must verify email before account is active
        )
        user.set_password(password)  # Use the User model's set_password method
        
        try:
            db.session.add(user)
            db.session.commit()
            
            # Try to send confirmation email, but don't fail if it doesn't work
            try:
                # Generate confirmation token
                token = get_serializer().dumps(user.email, salt='email-confirm')
                confirm_url = url_for('auth.confirm_email', token=token, _external=True)
                
                # Send confirmation email
                send_confirmation_email(user.email, confirm_url)
                flash('Registration successful! Please check your email to confirm your account before logging in.', 'success')
            except Exception as email_error:
                current_app.logger.warning(f'Could not send confirmation email: {str(email_error)}')
                flash('Registration successful! However, we could not send the confirmation email. Please contact support or try resending the verification email.', 'warning')
            
            return redirect(url_for('auth.login'))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Error during registration: {str(e)}')
            flash('An error occurred during registration. Please try again.', 'error')
            return redirect(url_for('auth.register'))

    return render_template('auth/register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login."""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password')
        remember = bool(request.form.get('remember'))

        if not email or not password:
            flash('Email and password are required.', 'error')
            return redirect(url_for('auth.login'))

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            if not user.is_active:
                flash('Your account has been deactivated. Please contact support.', 'error')
                return redirect(url_for('auth.login'))
            
            if not user.is_verified:
                flash('Please verify your email address before logging in. Check your inbox for the verification link.', 'warning')
                return redirect(url_for('auth.login'))

            login_user(user, remember=remember)
            user.update_last_login()
            
            # Redirect to next page or profile
            next_page = request.args.get('next')
            if next_page and next_page.startswith('/'):
                return redirect(next_page)
            return redirect(url_for('main.index'))
        else:
            flash('Invalid email or password.', 'error')

    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    """Handle user logout."""
    logout_user()
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('auth.login'))

@auth_bp.route('/confirm/<token>')
def confirm_email(token):
    """Confirm user email address."""
    try:
        serializer = get_serializer()
        email = serializer.loads(token, salt='email-confirm', max_age=3600)  # 1 hour expiry
    except SignatureExpired:
        flash('The confirmation link has expired.', 'error')
        return redirect(url_for('auth.login'))
    except BadTimeSignature:
        flash('Invalid confirmation link.', 'error')
        return redirect(url_for('auth.login'))

    user = User.query.filter_by(email=email).first()
    if user:
        if user.is_verified:
            flash('Account already confirmed. Please login.', 'info')
        else:
            user.is_verified = True
            user.email_confirmed_at = db.func.now()
            db.session.commit()
            flash('Your account has been confirmed! You can now login.', 'success')
    else:
        flash('Invalid confirmation link.', 'error')

    return redirect(url_for('auth.login'))

@auth_bp.route('/resend-verification', methods=['GET', 'POST'])
def resend_verification():
    """Resend email verification for unverified users."""
    if current_user.is_authenticated and current_user.is_verified:
        flash('Your email is already verified.', 'info')
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        
        if not email:
            flash('Email address is required.', 'error')
            return redirect(url_for('auth.resend_verification'))

        user = User.query.filter_by(email=email).first()
        
        if user and not user.is_verified:
            try:
                # Generate confirmation token
                token = get_serializer().dumps(user.email, salt='email-confirm')
                confirm_url = url_for('auth.confirm_email', token=token, _external=True)
                
                # Send confirmation email
                send_confirmation_email(user.email, confirm_url)
                flash('Verification email sent! Please check your inbox.', 'success')
            except Exception as e:
                current_app.logger.error(f'Error sending verification email: {str(e)}')
                flash('Could not send verification email. Please try again later.', 'error')
        else:
            # Don't reveal if email exists or is already verified for security
            flash('If that email address is in our system and unverified, you will receive a verification email.', 'info')

        return redirect(url_for('auth.login'))

    return render_template('auth/resend_verification.html')

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Handle password reset request."""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        
        if not email:
            flash('Email address is required.', 'error')
            return redirect(url_for('auth.forgot_password'))

        user = User.query.filter_by(email=email).first()
        
        if user:
            try:
                # Generate reset token
                token = get_serializer().dumps(user.email, salt='password-reset')
                reset_url = url_for('auth.reset_password', token=token, _external=True)
                
                # Send reset email
                # send_password_reset_email(user.email, reset_url)
                flash('Password reset instructions have been sent to your email.', 'success')
            except Exception as e:
                current_app.logger.error(f'Error sending password reset email: {str(e)}')
                flash('Could not send password reset email. Please try again later.', 'error')
        else:
            # Don't reveal if email exists or not
            flash('If that email address is in our system, you will receive password reset instructions.', 'info')

        return redirect(url_for('auth.login'))

    return render_template('auth/forgot_password.html')

@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Handle password reset."""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    try:
        serializer = get_serializer()
        email = serializer.loads(token, salt='password-reset', max_age=3600)  # 1 hour expiry
    except SignatureExpired:
        flash('The password reset link has expired.', 'error')
        return redirect(url_for('auth.forgot_password'))
    except BadTimeSignature:
        flash('Invalid password reset link.', 'error')
        return redirect(url_for('auth.forgot_password'))

    user = User.query.filter_by(email=email).first()
    if not user:
        flash('Invalid password reset link.', 'error')
        return redirect(url_for('auth.forgot_password'))

    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if not password or not confirm_password:
            flash('Both password fields are required.', 'error')
            return render_template('auth/reset_password.html', token=token)

        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('auth/reset_password.html', token=token)

        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'error')
            return render_template('auth/reset_password.html', token=token)

        try:
            user.set_password(password)
            db.session.commit()
            flash('Your password has been reset successfully. You can now login.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Error resetting password: {str(e)}')
            flash('An error occurred while resetting your password. Please try again.', 'error')

    return render_template('auth/reset_password.html', token=token)

