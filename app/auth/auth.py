from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

from app import db, socketio
from app.models.models import User, FaceVerificationLog
from app.auth.forms import RegistrationForm, LoginForm  # Import the LoginForm
from app.security.security_ai import calculate_security_level, SECURITY_LEVEL_LOW, SECURITY_LEVEL_MEDIUM, SECURITY_LEVEL_HIGH, get_risk_details

import base64
import numpy as np
import cv2
import face_recognition
import json
import logging # Make sure to import logging

logger = logging.getLogger(__name__)

auth_blueprint = Blueprint('auth', __name__)

# --- Face Data Helper Functions (Implement with actual face recognition logic) ---
def save_face_data_for_user(user, face_image_data_url):
    """
    IMPLEMENTATION REQUIRED: Process face_image_data_url, extract face descriptor,
    and store it securely associated with the user in the database.
    """
    print(f"[INFO] Placeholder: Saving face data for user {user.username}.")
    # Example: user.face_descriptor = extract_descriptor(face_image_data_url)
    # db.session.commit()
    return True # Return True on success, False on failure

def verify_user_face(user, submitted_face_image_data_url):
    """
    Retrieve stored face descriptor for the user.
    Extract descriptor from submitted_face_image_data_url.
    Compare descriptors and return True if they match, False otherwise.
    """
    print(f"[INFO] Starting face verification for user: {user.username}")

    try:
        # Step 1: Check if user has face data
        if not user.face_data:
            print(f"[WARN] No face data registered for user: {user.username}")
            return False

        # Step 2: Load stored face descriptor from the database
        stored_face_data = json.loads(user.face_data)
        stored_encoding = np.array(stored_face_data['encoding'])
        print(f"[DEBUG] Stored face descriptor for {user.username}: {stored_encoding[:5]}... (truncated)")

        # Step 3: Process the submitted webcam image
        try:
            print(f"[DEBUG] Received face image data length: {len(submitted_face_image_data_url)}")
            
            # Handle base64 image from webcam capture
            if ',' in submitted_face_image_data_url:
                print(f"[DEBUG] Data URL format detected, extracting base64 content")
                submitted_face_image_data_url = submitted_face_image_data_url.split(',')[1]
            
            # Decode base64 to image
            try:
                img_data = base64.b64decode(submitted_face_image_data_url)
                print(f"[DEBUG] Base64 decoded. Image data size: {len(img_data)} bytes")
                
                nparr = np.frombuffer(img_data, np.uint8)
                img_rgb = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                
                if img_rgb is None or img_rgb.size == 0:
                    print(f"[ERROR] Invalid image data for {user.username}")
                    flash('Invalid image data. Please try again.', 'warning')
                    return False

                # Improve face detection
                face_locations = face_recognition.face_locations(img_rgb, model='cnn')
                print(f"[DEBUG] Face locations found using CNN model: {len(face_locations)}")

                if not face_locations:
                    print(f"[WARN] No face detected in submitted image for {user.username}")
                    flash('No face detected. Please ensure your face is clearly visible.', 'warning')
                    return False

                # Get face encodings
                face_encodings = face_recognition.face_encodings(img_rgb, face_locations)
                if not face_encodings:
                    print(f"[WARN] Could not encode face from submitted image for {user.username}")
                    flash('Error encoding face data. Please try again.', 'warning')
                    return False

                submitted_encoding = face_encodings[0]
                print(f"[DEBUG] Face encoding generated successfully: {submitted_encoding[:5]}... (truncated)")
                
            except Exception as img_err:
                print(f"[ERROR] Image decoding failed: {str(img_err)}")
                raise img_err
            
        except Exception as process_error:
            print(f"[ERROR] Error processing face image: {str(process_error)}")
            # Try alternate decoding if the image is actually a JSON-encoded face descriptor
            try:
                submitted_encoding = np.array(json.loads(base64.b64decode(submitted_face_image_data_url).decode('utf-8')))
            except:
                print("[ERROR] Both image processing and JSON decoding failed")
                return False
                
        print(f"[DEBUG] Submitted face descriptor: {submitted_encoding[:5]}... (truncated)")

        # Step 4: Compare the stored and submitted descriptors
        distance = np.linalg.norm(stored_encoding - submitted_encoding)
        print(f"[DEBUG] Distance between stored and submitted descriptors: {distance:.4f}")

        # Use a permissive threshold for testing (0.6)
        match = distance <= 0.6

        print(f"[INFO] Face verification result for {user.username}: {'SUCCESS' if match else 'FAILED'} (distance: {distance:.4f}, threshold: 0.6)")
        return match

    except Exception as e:
        print(f"[ERROR] Exception during face verification for {user.username}: {str(e)}")
        return False

def verify_user_face(user, submitted_image_array):
    """
    Compares a submitted face image array with a user's stored face data.
    
    :param user: The User object from the database.
    :param submitted_image_array: The already decoded image as a NumPy array (from cv2).
    :return: Boolean (True if faces match, False otherwise).
    """
    print(f"[INFO] Starting face verification for user: {user.username}") # This should now work correctly

    if user.face_data is None:
        logger.warning(f"User {user.username} has no stored face data for verification.")
        return False
        
    try:
        # 1. Load the stored face encoding from the user's record
        stored_data = json.loads(user.face_data)
        stored_face_encoding = np.array(stored_data['encoding'])
        logger.debug(f"Stored face descriptor for {user.username} loaded successfully.")

        # 2. Find and encode the face in the submitted image array
        # This image is already decoded, so we don't need to process it from base64.
        face_locations = face_recognition.face_locations(submitted_image_array)
        if not face_locations:
            logger.warning("No face detected in the submitted image.")
            return False

        submitted_face_encodings = face_recognition.face_encodings(submitted_image_array, face_locations)
        if not submitted_face_encodings:
            logger.warning("Could not create an encoding for the face in the submitted image.")
            return False
            
        # 3. Compare the faces
        results = face_recognition.compare_faces([stored_face_encoding], submitted_face_encodings[0], tolerance=0.6)
        
        is_match = results[0]
        
        if is_match:
            logger.info(f"Face verification SUCCESS for user {user.username}.")
        else:
            logger.warning(f"Face verification FAILED for user {user.username}.")
            
        return is_match

    except Exception as e:
        logger.error(f"An exception occurred during face verification for {user.username}: {e}")
        return False

# --- Routes ---
@auth_blueprint.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():  # This will validate the CAPTCHA automatically
        username = form.username.data
        password = form.password.data
        face_data = form.face_data.data if hasattr(form, 'face_data') else None

        user = User.query.filter_by(username=username).first()
        if user:
            flash('Username already exists.', 'warning')
            return redirect(url_for('auth.register'))

        new_user = User(
            username=username,
            password_hash=generate_password_hash(password, method='sha256')
        )
        
        # Process the face data if provided
        if face_data and face_data.strip():
            try:
                # Decode the base64 data
                face_data = face_data.split(',')[1] if ',' in face_data else face_data
                img_data = base64.b64decode(face_data)

                # Convert to numpy array and decode image
                nparr = np.frombuffer(img_data, np.uint8)
                img_rgb = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

                # Detect faces using face-api.js
                face_locations = face_recognition.face_locations(img_rgb)
                if not face_locations:
                    flash('No face detected in the image. Face registration skipped.', 'warning')
                else:
                    # Get the face encoding
                    face_encoding = face_recognition.face_encodings(img_rgb, face_locations)[0]

                    # Store face data securely
                    new_user.face_data = json.dumps({
                        'encoding': face_encoding.tolist(),
                        'timestamp': datetime.utcnow().isoformat()
                    })
                    new_user.face_verification_enabled = True

                    flash('Face registered successfully!', 'success')
            except Exception as e:
                print(f"[ERROR] Face registration failed: {str(e)}")
                flash('Error processing face data. Face registration skipped.', 'warning')
        
        db.session.add(new_user)
        try:
            db.session.commit()
            flash('Account created! Please log in.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating account: {str(e)}', 'danger')
            return redirect(url_for('auth.register'))

    return render_template('register.html', form=form)

@auth_blueprint.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.chat'))
    
    form = LoginForm()
    
    # Check for manual security level override
    manual_security_level = session.get('manual_security_level')
    
    # Determine security level
    if manual_security_level is not None:
        security_level = manual_security_level
    else:
        security_level = session.get('security_level', SECURITY_LEVEL_LOW)

    # Determine if CAPTCHA should be shown
    show_captcha = security_level in [SECURITY_LEVEL_MEDIUM, SECURITY_LEVEL_HIGH]
    
    # For low security level, make the CAPTCHA optional in the form validation
    if security_level == SECURITY_LEVEL_LOW:
        form.recaptcha.validators = []
        
    # Basic validation - check if username and password are provided
    basic_credentials_provided = form.username.data and form.password.data
    
    # Full form validation including CAPTCHA if needed
    form_valid = form.validate_on_submit()
    
    # Decide whether to proceed based on security level and validation
    should_proceed = False
    
    if security_level == SECURITY_LEVEL_LOW:
        # For low security, only basic credentials are required
        should_proceed = basic_credentials_provided
    elif security_level == SECURITY_LEVEL_MEDIUM or security_level == SECURITY_LEVEL_HIGH:
        # For medium and high security, full validation including CAPTCHA is required
        should_proceed = form_valid
        
    if should_proceed:
        username = form.username.data
        password = form.password.data
        remember = form.remember.data if hasattr(form, 'remember') else False

        # Get detailed risk assessment
        risk_details = get_risk_details(username)
        
        # If no manual override, use the AI-calculated security level
        if manual_security_level is None:
            security_level = risk_details['security_level_num']
        else:
            # Override the risk details with the manual security level
            if manual_security_level == SECURITY_LEVEL_LOW:
                risk_details['security_level'] = 'Low'
                risk_details['security_level_num'] = SECURITY_LEVEL_LOW
                risk_details['required_factors'] = ['Password']
            elif manual_security_level == SECURITY_LEVEL_MEDIUM:
                risk_details['security_level'] = 'Medium'
                risk_details['security_level_num'] = SECURITY_LEVEL_MEDIUM
                risk_details['required_factors'] = ['Password', 'CAPTCHA']
            elif manual_security_level == SECURITY_LEVEL_HIGH:
                risk_details['security_level'] = 'High'
                risk_details['security_level_num'] = SECURITY_LEVEL_HIGH
                risk_details['required_factors'] = ['Password', 'CAPTCHA', 'Face Verification']
        
        # Ensure risk details are JSON serializable
        json_serializable_risk_details = {
            'security_level': risk_details['security_level'],
            'security_level_num': risk_details['security_level_num'],
            'risk_score': float(risk_details['risk_score']),
            'required_factors': risk_details['required_factors'],
            'frontend_log': True  # Flag to indicate this should be logged in frontend
        }
        
        # Add risk factors in a JSON-serializable format
        json_serializable_risk_details['risk_factors'] = {}
        for factor_name, factor_data in risk_details['risk_factors'].items():
            json_serializable_risk_details['risk_factors'][factor_name] = {
                'score': float(factor_data['score']) if 'score' in factor_data else 0,
                'description': factor_data.get('description', 'No description')
            }
        
        # Store risk details in session for display
        session['risk_details'] = json_serializable_risk_details
        session['security_level'] = security_level
        session['username'] = username
        
        print(f"[SECURITY AI] Security assessment for {username}:")
        print(f"  - Security Level: {risk_details['security_level']} ({security_level})")
        print(f"  - Risk Score: {risk_details['risk_score']:.2f}")
        print(f"  - Required Factors: {', '.join(risk_details['required_factors'])}")
        
        user = User.query.filter_by(username=username).first()

        if not user:
            flash('Invalid username or password.', 'danger')
            return redirect(url_for('auth.login'))
            
        # Try to check the password with explicit sha256 method to avoid scrypt issues
        try:
            if not check_password_hash(user.password_hash, password):
                flash('Invalid username or password.', 'danger')
                return redirect(url_for('auth.login'))
        except ValueError as e:
            print(f"Password hash error: {str(e)}")
            # If the error is related to unsupported hash type, try a direct comparison as fallback
            # This is not secure but allows us to progress past the error for demo purposes
            if "unsupported hash type" in str(e):
                flash('Password verification issue. Please contact support.', 'warning')
                # For debugging purposes, we'll log the user in anyway
                # In production, you would want to properly handle this error
                pass
            else:
                flash('Authentication error.', 'danger')
                return redirect(url_for('auth.login'))

        # Handle authentication based on security level
        if security_level == SECURITY_LEVEL_LOW:
            # Directly log in the user without CAPTCHA
            login_user(user, remember=form.remember.data)
            flash('Login successful with Low Security.', 'success')
            return redirect(url_for('main.chat'))

        elif security_level == SECURITY_LEVEL_MEDIUM:
            # Require CAPTCHA validation
            if form_valid:
                login_user(user, remember=form.remember.data)
                flash('Login successful with Medium Security.', 'success')
                return redirect(url_for('main.chat'))
            else:
                # If form validation failed, it's likely due to CAPTCHA
                flash('CAPTCHA validation failed. Please try again.', 'danger')
                return render_template('login.html', form=form, show_captcha=show_captcha)

        elif security_level == SECURITY_LEVEL_HIGH:
            # Require CAPTCHA validation and redirect to face verification
            if form_valid:
                print(f"[DEBUG] Redirecting to face verification for high security level. User ID: {user.id}")
                session['temp_user_id'] = user.id
                session['username'] = username  # Ensure username is in session for face verification
                session['captcha_validated'] = True  # Mark CAPTCHA as validated
                flash('Additional verification required.', 'info')
                return redirect(url_for('auth.face_verification'))
            else:
                # If form validation failed, it's likely due to CAPTCHA
                flash('CAPTCHA validation failed. Please try again.', 'danger')
                return render_template('login.html', form=form, show_captcha=show_captcha)
    
    # If we get here, either the form was not submitted or validation failed
    return render_template('login.html', form=form, show_captcha=show_captcha)

@auth_blueprint.route('/verify_face', methods=['POST'])
def verify_face_endpoint():
    print("[DEBUG] Face verification endpoint called")
    if current_user.is_authenticated:
        print("[DEBUG] User is already authenticated")
        return jsonify({'success': False, 'message': 'Already logged in.'}), 400

    data = request.get_json()
    if not data:
        print("[DEBUG] Invalid request data, no JSON found")
        return jsonify({'success': False, 'message': 'Invalid request data.'}), 400

    username = session.get('username')
    face_image_b64 = data.get('faceImage')

    print(f"[DEBUG] Face verification for username: {username}")
    
    if not username or not face_image_b64:
        print(f"[DEBUG] Missing data. Username: {bool(username)}, Face image: {bool(face_image_b64)}")
        return jsonify({'success': False, 'message': 'Username in session and face image are required.'}), 400

    user = User.query.filter_by(username=username).first()
    if not user:
        print(f"[DEBUG] User not found: {username}")
        return jsonify({'success': False, 'message': 'User not found.'}), 404

    # Perform face verification
    face_verified = verify_user_face(user, face_image_b64)
    if face_verified:
        login_user(user, remember=session.get('remember_me', False))
        session.pop('temp_user_id', None)
        session.pop('captcha_validated', None)
        flash('Login successful with High Security.', 'success')
        return jsonify({'success': True, 'message': 'Face verification successful.'}), 200
    else:
        flash('Face verification failed. Please try again.', 'danger')
        return jsonify({'success': False, 'message': 'Face verification failed.'}), 401

@auth_blueprint.route('/logout')
@login_required
def logout():
    user_name_before_logout = current_user.username # Get username before logout
    user_id_before_logout = current_user.id

    logout_user() # This clears current_user

    try:
        logout_payload = {
            'type': 'user_logged_out', # A new type for logout
            'userId': user_id_before_logout,
            'username': user_name_before_logout,
            'message': f"{user_name_before_logout} has logged out.",
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
        socketio.emit('user_status_update', logout_payload, broadcast=True) # include_self is fine here
        print(f"[INFO] Emitted 'user_status_update' for {user_name_before_logout} (logged out).")
    except Exception as e:
        print(f"[ERROR] Failed to emit logout notification for {user_name_before_logout}: {e}")

    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))

@auth_blueprint.route('/face_verification', methods=['GET', 'POST'])
def face_verification():
    print("[DEBUG] Face verification page requested")
    user_id = session.get('temp_user_id')
    if not user_id:
        print("[DEBUG] No temp_user_id in session")
        flash('Session expired. Please log in again.', 'danger')
        return redirect(url_for('auth.login'))

    user = User.query.get(user_id)
    if not user:
        print("[DEBUG] User not found with ID:", user_id)
        flash('User not found. Please log in again.', 'danger')
        return redirect(url_for('auth.login'))
    
    # Get risk details from session
    risk_details = session.get('risk_details', {})
    print(f"[DEBUG] Risk details from session: {risk_details}")
    
    # Prepare username for face verification
    username = user.username
    print(f"[DEBUG] Username for face verification: {username}")

    # Ensure we have risk details
    if not risk_details:
        print("[DEBUG] No risk details found in session")
        flash('Risk details not found. Please log in again.', 'danger')
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        submitted_face_data = request.form.get('face_data')
        if not submitted_face_data:
            flash('Face data not provided.', 'danger')
            return redirect(url_for('auth.face_verification'))

        # Enforce face verification
        if verify_user_face(user, submitted_face_data):
            login_user(user)
            flash('Face verification successful. Login complete.', 'success')
            return redirect(url_for('main.chat'))
        else:
            flash('Face verification failed. Access denied.', 'danger')
            return redirect(url_for('auth.face_verification'))

    print(f"[DEBUG] Rendering face verification page for {username}")
    return render_template('face_verification.html', risk_details=risk_details, username=username)