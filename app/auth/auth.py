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
        logger.info(f"Using manual security level: {security_level}")
    else:
        security_level = session.get('security_level', SECURITY_LEVEL_LOW)
        logger.info(f"Using session security level: {security_level}")
    
    # Force high security for debugging - COMMENT OUT IN PRODUCTION
    if 'force_high_security' in request.args:
        security_level = SECURITY_LEVEL_HIGH
        logger.info(f"FORCED security level to HIGH via query param")
    
    # Log all session variables for debugging
    logger.info(f"Session contents: manual_security_level={session.get('manual_security_level')}, security_level={session.get('security_level')}, face_verification_enabled={session.get('face_verification_enabled')}")
    logger.info(f"Final security level for this login attempt: {security_level}")
    
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
            # Low security requires username and password - ALWAYS CHECK PASSWORD
            if not username:
                logger.warning("Login attempt with missing username")
                flash('Username is required.', 'danger')
                return render_template('login.html', form=form, show_captcha=False)
                
            if not password:
                logger.warning(f"Login attempt for user '{username}' with missing password")
                flash('Password is required.', 'danger')
                return render_template('login.html', form=form, show_captcha=False)
                
            # Check credentials
            user = User.query.filter_by(username=username).first()
            if not user:
                logger.warning(f"Login attempt for non-existent user: {username}")
                flash('Invalid username or password.', 'danger')
                return render_template('login.html', form=form, show_captcha=False)
                
            if not check_password_hash(user.password_hash, password):
                logger.warning(f"Failed password attempt for user: {username}")
                flash('Invalid username or password.', 'danger')
                return render_template('login.html', form=form, show_captcha=False)
                
            # Success - log the user in
            logger.info(f"Successful login for user: {username} with Low Security")
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
                
                # Log the high security authentication attempt
                logger.info(f"High security login validated for user: {username}. Proceeding to face verification.")
                
                # Get risk details for this login attempt
                from app.security.security_ai import get_risk_details
                risk_details = get_risk_details(user)
                
                # Ensure we force high security level in risk details
                if risk_details['security_level'] != 'High':
                    logger.warning(f"Security level mismatch. Expected: High, Got: {risk_details['security_level']}. Forcing to High.")
                    risk_details['security_level'] = 'High'
                    risk_details['security_level_num'] = SECURITY_LEVEL_HIGH
                    risk_details['required_factors'] = ['Password', 'CAPTCHA', 'Face Verification']
                
                # Store data for face verification
                session['temp_user_id'] = user.id
                session['username'] = username
                session['face_verification_enabled'] = True
                session['face_verification_required'] = True  # Add a flag to track face verification requirement
                session['high_security_auth'] = True  # Flag indicating high security flow
                session['security_level'] = SECURITY_LEVEL_HIGH  # Ensure security level is maintained
                session['risk_details'] = risk_details
                session['next_page'] = url_for('main.chat')
                
                # Log face verification requirement
                logger.info(f"Face verification required for high security. User: {username}")
                
                # Redirect to face verification page (using face blueprint)
                return redirect(url_for('face.face_verification'))
            else:
                # Form validation failed
                if 'recaptcha' in form.errors:
                    flash('CAPTCHA verification required.', 'danger')
                    logger.warning(f"CAPTCHA validation failed for high security login attempt: {username}")
                elif not username or not password:
                    flash('Username and password are required.', 'danger')
                    logger.warning(f"Missing credentials for high security login attempt")
                return render_template('login.html', form=form, show_captcha=True)
    
    # Integrate AI-based security level determination
    from ml_mfa.ml_security import increment_failed_attempts, reset_failed_attempts, get_security_level

    if request.method == 'POST':
        user = User.query.filter_by(username=username).first()
        if not user or not check_password_hash(user.password_hash, password):
            logger.warning(f"Failed password attempt for user: {username}")
            # Increment failed login attempts and escalate risk level
            increment_failed_attempts(username)
            security_level = get_security_level(username)
            session['security_level'] = security_level
            logger.info(f"Escalated security level to {security_level} after failed login attempt")
            flash('Invalid username or password.', 'danger')
            return render_template('login.html', form=form, show_captcha=(security_level >= SECURITY_LEVEL_MEDIUM))

        # Reset failed attempts on successful login
        reset_failed_attempts(username)
        session['security_level'] = SECURITY_LEVEL_LOW
        logger.info(f"Successful login for user: {username} with security level: {security_level}")
    
    # Fetch AI risk assessment for the user
    risk_details = get_risk_details(username)
    logger.info(f"AI Risk Assessment for {username}: {risk_details}")

    # Use AI risk assessment to dynamically adjust security level
    if risk_details['security_level_num'] > security_level:
        security_level = risk_details['security_level_num']
        session['security_level'] = security_level
        logger.info(f"Updated security level to {security_level} based on AI risk assessment")

    # Log risk details for debugging
    logger.info(f"Risk details: {risk_details}")
    
    # Step 5: Display the login form (GET request)
    return render_template('login.html', form=form, show_captcha=show_captcha)

def verify_user_face(user, submitted_face_image):
    """
    Verify if the submitted face matches the user's registered face data.
    
    Args:
        user: User object from the database
        submitted_face_image: Base64 encoded face image or numpy array image
        
    Returns:
        bool: True if verification is successful, False otherwise
    """
    logger.info(f"Starting face verification for user: {user.username}")
    
    try:
        # Check if user has face data
        if not user.face_data or not user.face_verification_enabled:
            logger.warning(f"No face data registered for user: {user.username}")
            return False
            
        import face_recognition
        import json
        import base64
        import numpy as np
        import cv2
        
        # Load stored face data from the database
        stored_face_data = json.loads(user.face_data)
        stored_encoding = np.array(stored_face_data['encoding'])
        
        # Process the submitted face image
        if isinstance(submitted_face_image, str):
            # Handle base64 encoded image
            if ',' in submitted_face_image:
                submitted_face_image = submitted_face_image.split(',')[1]
                
            # Decode the image
            img_data = base64.b64decode(submitted_face_image)
            nparr = np.frombuffer(img_data, np.uint8)
            img_rgb = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if img_rgb is None:
                logger.error("Failed to decode submitted face image")
                return False
                
        elif isinstance(submitted_face_image, np.ndarray):
            # Already a numpy array image
            img_rgb = submitted_face_image
        else:
            logger.error(f"Unsupported face image type: {type(submitted_face_image)}")
            return False
        
        # Detect faces in the submitted image
        face_locations = face_recognition.face_locations(img_rgb)
        if not face_locations:
            logger.warning("No face detected in the submitted image")
            return False
            
        # Get face encodings
        face_encoding = face_recognition.face_encodings(img_rgb, face_locations)[0]
        
        # Compare face encodings
        face_distance = face_recognition.face_distance([stored_encoding], face_encoding)[0]
        match_percentage = (1 - face_distance) * 100
        
        # Log verification result
        success = face_distance < 0.6  # Lower distance is better match
        logger.info(f"Face verification result: {'SUCCESS' if success else 'FAILED'} ({match_percentage:.1f}% match)")
        
        # Log the verification attempt in database
        try:
            log_entry = FaceVerificationLog(
                user_id=user.id,
                success=success,
                match_percentage=match_percentage,
                timestamp=datetime.utcnow()
            )
            db.session.add(log_entry)
            db.session.commit()
        except Exception as e:
            logger.error(f"Error logging face verification: {str(e)}")
            db.session.rollback()
        
        return success
        
    except Exception as e:
        logger.error(f"Error during face verification: {str(e)}")
        return False
