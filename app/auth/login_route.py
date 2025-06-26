from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

from app import db
from app.models.models import User, FaceVerificationLog
from app.auth.forms import RegistrationForm, LoginForm
from app.security.security_ai import calculate_security_level, SECURITY_LEVEL_LOW, SECURITY_LEVEL_MEDIUM, SECURITY_LEVEL_HIGH, get_risk_details

import logging
logger = logging.getLogger(__name__)

auth_blueprint = Blueprint('auth', __name__)

@auth_blueprint.route('/login', methods=['GET', 'POST'])
def login():
    """
    Handle user login with dynamic security level determination
    and multi-factor authentication
    """
    # Step 1: Determine the security level
    manual_security_level = session.get('manual_security_level')
    if manual_security_level:
        security_level = manual_security_level
    else:
        security_level = session.get('security_level', SECURITY_LEVEL_LOW)
    
    logger.info(f"Security level for this login attempt: {security_level}")
    
    # Step 2: Configure form requirements based on security level
    form = LoginForm()
    show_captcha = security_level in [SECURITY_LEVEL_MEDIUM, SECURITY_LEVEL_HIGH]
    
    # For low security, CAPTCHA is not required
    if security_level == SECURITY_LEVEL_LOW:
        form.recaptcha.validators = []
    
    # Step 3: Handle form submission (POST request)
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        logger.info(f"Login attempt for user: {username}")
        logger.info(f"Security level: {security_level}, Show CAPTCHA: {show_captcha}")
        
        # Step 4: Validate credentials based on security level
        if security_level == SECURITY_LEVEL_LOW:
            # Low security only requires username and password
            if not username or not password:
                flash('Username and password are required.', 'danger')
                return render_template('login.html', form=form, show_captcha=False)
                
            # Check credentials
            user = User.query.filter_by(username=username).first()
            if not user or not check_password_hash(user.password_hash, password):
                flash('Invalid username or password.', 'danger')
                return render_template('login.html', form=form, show_captcha=False)
                
            # Success - log the user in
            login_user(user)
            flash('Login successful with Low Security.', 'success')
            return redirect(url_for('main.chat'))
            
        elif security_level == SECURITY_LEVEL_MEDIUM:
            # Medium security requires username, password, and CAPTCHA
            if form.validate_on_submit():
                user = User.query.filter_by(username=username).first()
                if not user or not check_password_hash(user.password_hash, password):
                    flash('Invalid username or password.', 'danger')
                    return render_template('login.html', form=form, show_captcha=True)
                    
                # Success - log the user in
                login_user(user)
                flash('Login successful with Medium Security.', 'success')
                return redirect(url_for('main.chat'))
            else:
                # Form validation failed
                if 'recaptcha' in form.errors:
                    flash('CAPTCHA verification required.', 'danger')
                elif not username or not password:
                    flash('Username and password are required.', 'danger')
                return render_template('login.html', form=form, show_captcha=True)
                
        elif security_level == SECURITY_LEVEL_HIGH:
            # High security requires username, password, CAPTCHA, and face verification
            if form.validate_on_submit():
                user = User.query.filter_by(username=username).first()
                if not user or not check_password_hash(user.password_hash, password):
                    flash('Invalid username or password.', 'danger')
                    return render_template('login.html', form=form, show_captcha=True)
                    
                # Store data for face verification
                session['temp_user_id'] = user.id
                session['username'] = username
                session['face_verification_enabled'] = True
                
                # Redirect to face verification page
                return redirect(url_for('auth.face_verification'))
            else:
                # Form validation failed
                if 'recaptcha' in form.errors:
                    flash('CAPTCHA verification required.', 'danger')
                elif not username or not password:
                    flash('Username and password are required.', 'danger')
                return render_template('login.html', form=form, show_captcha=True)
    
    # Step 5: Display the login form (GET request)
    return render_template('login.html', form=form, show_captcha=show_captcha)
