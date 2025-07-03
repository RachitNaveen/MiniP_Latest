from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

from app import db, socketio
from app.models.models import User, FaceVerificationLog
from app.auth.forms import RegistrationForm, LoginForm  # Import the LoginForm
from app.security.security_ai import SECURITY_LEVEL_LOW, SECURITY_LEVEL_MEDIUM, SECURITY_LEVEL_HIGH, get_risk_details

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
    """Save face data for a user."""
    try:
        if ',' in face_image_data_url:
            face_image_data_url = face_image_data_url.split(',')[1]

        img_data = base64.b64decode(face_image_data_url)
        nparr = np.frombuffer(img_data, np.uint8)
        img_rgb = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        face_locations = face_recognition.face_locations(img_rgb)
        if not face_locations:
            return False

        face_encoding = face_recognition.face_encodings(img_rgb, face_locations)[0]
        user.face_data = json.dumps({'encoding': face_encoding.tolist(), 'timestamp': datetime.utcnow().isoformat()})
        user.face_verification_enabled = True

        db.session.commit()
        return True

    except Exception as e:
        db.session.rollback()
        return False

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
    Compares a submitted face image array with a user's stored face data,
    with enhanced logging for debugging.
    """
    print(f"[INFO] Starting face verification for user: {user.username}")

    if user.face_data is None:
        logger.warning(f"User {user.username} has no stored face data for verification.")
        return False
        
    try:
        # 1. Load stored face encoding
        stored_data = json.loads(user.face_data)
        stored_face_encoding = np.array(stored_data['encoding'])

        # 2. Find and encode the face in the submitted image
        face_locations = face_recognition.face_locations(submitted_image_array)
        if not face_locations:
            logger.warning("No face detected in the submitted image.")
            return False

        submitted_face_encodings = face_recognition.face_encodings(submitted_image_array, face_locations)
        if not submitted_face_encodings:
            logger.warning("Could not create an encoding for the face in the submitted image.")
            return False
            
        # 3. Compare the faces and get the distance
        known_encoding = [stored_face_encoding]
        unknown_encoding = submitted_face_encodings[0]
        
        matches = face_recognition.compare_faces(known_encoding, unknown_encoding, tolerance=0.6)
        # --- THIS IS THE KEY PART ---
        # Calculate the actual numerical distance between the faces
        distance = face_recognition.face_distance(known_encoding, unknown_encoding)[0]
        
        # --- NEW: Detailed logging of the distance ---
        logger.info(f"Face comparison for {user.username}: Match={matches[0]}, Distance={distance:.4f} (Tolerance is 0.6)")
        
        is_match = matches[0]
        
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
    
    # Debug information for form submission
    if request.method == 'POST':
        print(f"[DEBUG] Register form submitted. Form data keys: {list(request.form.keys())}")
        
        # Get face data from any available source
        face_data = None
        
        # Check if face_data is in the form object
        if hasattr(form, 'face_data') and form.face_data.data and form.face_data.data.strip():
            face_data = form.face_data.data
            print(f"[DEBUG] Face data found in form.face_data.data. Length: {len(face_data)}")
            
        # Check if face_data is in request.form
        elif 'face_data' in request.form and request.form['face_data'] and request.form['face_data'].strip():
            face_data = request.form['face_data']
            print(f"[DEBUG] Face data found in request.form['face_data']. Length: {len(face_data)}")
            
        # Check if face_data_backup is in request.form
        elif 'face_data_backup' in request.form and request.form['face_data_backup'] and request.form['face_data_backup'].strip():
            face_data = request.form['face_data_backup']
            print(f"[DEBUG] Face data found in request.form['face_data_backup']. Length: {len(face_data)}")
            
        # Handle direct processing if we have all required data
        if 'username' in request.form and 'password' in request.form and face_data:
            print("[DEBUG] Processing registration with direct form data")
            username = request.form['username']
            password = request.form['password']
            
            # Only proceed if we have the essential data
            if username and password and face_data:
                print(f"[DEBUG] Processing registration for user: {username}")
                return process_registration(username, password, face_data)
    
    # Normal form processing path
    if form.validate_on_submit():
        print("[DEBUG] Form validation passed")
        username = form.username.data
        password = form.password.data
        
        # Print all form data for debugging
        print(f"[DEBUG] All form fields: {dir(form)}")
        print(f"[DEBUG] All request.form keys: {list(request.form.keys())}")
        
        # Get face data - directly from request.form for simplicity and reliability
        face_data = None
        
        # First try the standard field
        if 'face_data' in request.form and request.form['face_data']:
            face_data = request.form['face_data']
            print(f"[DEBUG] Face data found in request.form['face_data']. Length: {len(face_data)}")
            
        # If that fails, try the backup field
        elif 'face_data_backup' in request.form and request.form['face_data_backup']:
            face_data = request.form['face_data_backup']
            print(f"[DEBUG] Face data found in request.form['face_data_backup']. Length: {len(face_data)}")
        
        # Fallback to form data only if necessary
        elif hasattr(form, 'face_data') and form.face_data.data:
            face_data = form.face_data.data
            print(f"[DEBUG] Face data found in form.face_data.data. Length: {len(face_data)}")
        
        print(f"[DEBUG] Username: {username}")
        print(f"[DEBUG] Password set: {bool(password)}")
        print(f"[DEBUG] Face data exists: {bool(face_data)}")
        
        # Validate that face data is provided (required)
        if not face_data or not face_data.strip():
            print("[ERROR] Face data missing or empty in all possible locations")
            flash('Face registration is required. Please capture your face image.', 'error')
            return redirect(url_for('auth.register'))
            
        return process_registration(username, password, face_data)
            
    return render_template('register.html', form=form)

# Separate function to process registration data
def process_registration(username, password, face_data):
    """Process user registration with the provided data"""
    print(f"[DEBUG] Processing registration for {username}")
    
    # Check if username already exists
    user = User.query.filter_by(username=username).first()
    if user:
        flash('Username already exists.', 'warning')
        return redirect(url_for('auth.register'))

    new_user = User(
        username=username,
        password_hash=generate_password_hash(password, method='pbkdf2:sha256')
    )
    
    # Process the face data if provided
    if face_data and face_data.strip():
        try:
            # Log face data properties for debugging
            print(f"[DEBUG] Processing face data of length: {len(face_data)}")
            print(f"[DEBUG] Face data starts with: {face_data[:30]}...")
            print(f"[DEBUG] Face data is data URL format: {'data:image' in face_data}")
            
            # Decode the base64 data
            face_data = face_data.split(',')[1] if ',' in face_data else face_data
            print(f"[DEBUG] Face data after splitting: {face_data[:30]}...")
            
            # Try to decode the data
            try:
                img_data = base64.b64decode(face_data)
                print(f"[DEBUG] Decoded image data size: {len(img_data)} bytes")
            except Exception as decode_error:
                print(f"[ERROR] Base64 decode error: {str(decode_error)}")
                print(f"[DEBUG] First 100 chars of problematic data: {face_data[:100]}")
                flash('Error processing face data. Please try again.', 'error')
                return redirect(url_for('auth.register'))

            # Convert to numpy array and decode image
            nparr = np.frombuffer(img_data, np.uint8)
            img_rgb = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if img_rgb is None or img_rgb.size == 0:
                print("[ERROR] Failed to decode image data")
                flash('Invalid image data. Please try again.', 'error')
                return redirect(url_for('auth.register'))
                
            print(f"[DEBUG] Image dimensions: {img_rgb.shape}")

            # Try multiple methods for more reliable face detection
            # First try HOG method which is faster
            face_locations = face_recognition.face_locations(img_rgb, model="hog")
            
            # If that fails, try CNN model which is more accurate but slower
            if not face_locations:
                print("[DEBUG] No face detected with HOG model, trying CNN model...")
                face_locations = face_recognition.face_locations(img_rgb, model="cnn")
                
            if not face_locations:
                print("[ERROR] No face detected in the image")
                flash('No face detected in the image. Please ensure good lighting and try again.', 'error')
                return redirect(url_for('auth.register'))
            else:
                print(f"[DEBUG] Face detected at position: {face_locations[0]}")
                
                # Try to generate face encoding with increased number of jitters for better accuracy
                face_encodings = face_recognition.face_encodings(img_rgb, face_locations, num_jitters=5)
                
                if not face_encodings or len(face_encodings) == 0:
                    print("[ERROR] Failed to generate face encoding")
                    flash('Failed to process face features. Please try again with better lighting.', 'error')
                    return redirect(url_for('auth.register'))
                
                face_encoding = face_encodings[0]
                print(f"[DEBUG] Generated face encoding of length: {len(face_encoding)}")
                
                # Store face data securely
                face_data_json = json.dumps({
                    'encoding': face_encoding.tolist(),
                    'timestamp': datetime.utcnow().isoformat()
                })
                
                # Verify the face data is valid JSON
                try:
                    json.loads(face_data_json)
                    new_user.face_data = face_data_json
                    new_user.face_verification_enabled = True
                    print(f"[INFO] Face data stored successfully for user: {username}")
                    flash('Face registered successfully!', 'success')
                except json.JSONDecodeError as json_err:
                    print(f"[ERROR] Invalid JSON face data: {str(json_err)}")
                    flash('Error storing face data. Please try again.', 'error')
                    return redirect(url_for('auth.register'))
        except Exception as e:
            print(f"[ERROR] Face registration failed: {str(e)}")
            flash('Error processing face data. Please try again.', 'error')
            return redirect(url_for('auth.register'))
    
    db.session.add(new_user)
    try:
        # Print debug information before commit
        print(f"[DEBUG] About to commit new user: {username}")
        print(f"[DEBUG] Face data exists: {new_user.face_data is not None}")
        print(f"[DEBUG] Face verification enabled: {new_user.face_verification_enabled}")
        print(f"[DEBUG] Face data length: {len(new_user.face_data) if new_user.face_data else 'None'}")
        
        db.session.commit()
        print(f"[DEBUG] User committed successfully. User ID: {new_user.id}")
        flash('Account created! Please log in.', 'success')
        return redirect(url_for('auth.login'))
    except Exception as e:
        db.session.rollback()
        print(f"[ERROR] Failed to commit new user: {str(e)}")
        flash(f'Error creating account: {str(e)}', 'danger')
        # Print the full traceback for better debugging
        import traceback
        traceback.print_exc()
        return redirect(url_for('auth.register'))

    return render_template('register.html', form=form)

@auth_blueprint.route('/login', methods=['GET', 'POST'])
def login():
    """
    Handle user login with high security level and face verification.
    """
    # Set security level to high
    session['security_level'] = SECURITY_LEVEL_HIGH
    logger.info(f"Security level set to HIGH for login.")

    form = LoginForm()
    show_captcha = True  # Always show CAPTCHA for high security

    if request.method == 'POST':
        username = form.username.data
        password = form.password.data

        logger.info(f"Login attempt for user: {username}")
        
        # Clear any existing session data to prevent session mixups
        session.pop('temp_user_id', None)
        session.pop('username', None)
        session.pop('face_verification_enabled', None)
        session.pop('face_verification_required', None)
        session.pop('high_security_auth', None)
        session.pop('next_page', None)
        session.pop('face_verified', None)
        session.pop('face_verified_time', None)

        # Validate credentials
        user = User.query.filter_by(username=username).first()
        if not user or not user.check_password(password):
            flash('Invalid username or password.', 'danger')
            return render_template('login.html', form=form, show_captcha=True)

        # Log the high security authentication attempt
        logger.info(f"High security login validated for user: {username} (ID: {user.id}). Proceeding to face verification.")

        # Store data for face verification
        session['temp_user_id'] = user.id
        session['username'] = username
        session['face_verification_enabled'] = True
        session['face_verification_required'] = True
        session['high_security_auth'] = True
        session['next_page'] = url_for('main.chat')
        
        # Debug log session data
        print(f"[DEBUG] Session data for login: temp_user_id={session.get('temp_user_id')}, username={session.get('username')}")

        # Redirect to face verification page
        return redirect(url_for('face.face_verification'))

    return render_template('login.html', form=form, show_captcha=True)

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

@auth_blueprint.route('/register_with_face', methods=['POST'])
def register_with_face():
    """API endpoint to register a user with face data, bypassing form validation"""
    if request.method == 'POST':
        try:
            data = request.get_json()
            if not data:
                return jsonify({'success': False, 'message': 'No data provided'}), 400
                
            username = data.get('username')
            password = data.get('password')
            confirm_password = data.get('confirm_password')
            face_data = data.get('face_data')
            
            # Basic validation
            if not username or not password or not confirm_password:
                return jsonify({'success': False, 'message': 'Missing required fields'}), 400
                
            if password != confirm_password:
                return jsonify({'success': False, 'message': 'Passwords do not match'}), 400
                
            if not face_data:
                return jsonify({'success': False, 'message': 'Face data is required'}), 400
                
            print(f"[DEBUG] Direct API registration for {username}")
            print(f"[DEBUG] Face data length: {len(face_data)}")
            
            # Check if username already exists
            user = User.query.filter_by(username=username).first()
            if user:
                return jsonify({'success': False, 'message': 'Username already exists'}), 400
                
            # Create new user
            new_user = User(
                username=username,
                password_hash=generate_password_hash(password, method='pbkdf2:sha256')
            )
            
            # Process face data
            try:
                print(f"[DEBUG] Processing face data for API registration. Raw data type: {type(face_data)}")
                if not isinstance(face_data, str):
                    return jsonify({'success': False, 'message': 'Face data must be a string'}), 400
                
                print(f"[DEBUG] Face data starts with: {face_data[:30]}...")
                print(f"[DEBUG] Face data is data URL format: {'data:image' in face_data}")
                
                # Extract base64 data
                face_data = face_data.split(',')[1] if ',' in face_data else face_data
                print(f"[DEBUG] Face data after splitting: {face_data[:30]}...")
                
                # Decode base64
                try:
                    img_data = base64.b64decode(face_data)
                    print(f"[DEBUG] Decoded image data size: {len(img_data)} bytes")
                except Exception as e:
                    print(f"[ERROR] Base64 decode error: {str(e)}")
                    return jsonify({'success': False, 'message': f'Invalid base64 data: {str(e)}'}), 400
                
                # Decode image
                nparr = np.frombuffer(img_data, np.uint8)
                img_rgb = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                
                if img_rgb is None or img_rgb.size == 0:
                    return jsonify({'success': False, 'message': 'Invalid image data'}), 400
                    
                # Detect face in the image
                face_locations = face_recognition.face_locations(img_rgb)
                if not face_locations:
                    face_locations = face_recognition.face_locations(img_rgb, model="cnn")
                    
                if not face_locations:
                    return jsonify({'success': False, 'message': 'No face detected in the image'}), 400
                    
                # Generate face encoding
                face_encodings = face_recognition.face_encodings(img_rgb, face_locations)
                if not face_encodings:
                    return jsonify({'success': False, 'message': 'Could not generate face encoding'}), 400
                    
                # Save face data
                face_encoding = face_encodings[0]
                new_user.face_data = json.dumps({
                    'encoding': face_encoding.tolist(),
                    'timestamp': datetime.utcnow().isoformat()
                })
                new_user.face_verification_enabled = True
                
                # Save user to database
                db.session.add(new_user)
                db.session.commit()
                
                return jsonify({
                    'success': True, 
                    'message': 'Account created successfully',
                    'redirect': url_for('auth.login')
                })
                
            except Exception as e:
                db.session.rollback()
                print(f"[ERROR] Face processing error: {str(e)}")
                return jsonify({'success': False, 'message': f'Error processing face data: {str(e)}'}), 500
                
        except Exception as e:
            print(f"[ERROR] Registration API error: {str(e)}")
            return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500
            
    return jsonify({'success': False, 'message': 'Invalid request method'}), 405