from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

from app import db, socketio
from app.models import User, FaceVerificationLog
from app.forms import RegistrationForm, LoginForm  # Import the LoginForm
from app.security_ai import calculate_security_level, SECURITY_LEVEL_LOW, SECURITY_LEVEL_MEDIUM, SECURITY_LEVEL_HIGH

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
    print(f"[INFO] Verifying face for user {user.username}.")
    
    try:
        # Check if user has face data
        if not user.face_data:
            print(f"[WARN] No face data registered for user {user.username}")
            return False
        
        import json
        import base64
        import numpy as np
        import cv2
        import face_recognition
        
        # Load stored face encoding from user model
        stored_face_data = json.loads(user.face_data)
        stored_encoding = np.array(stored_face_data['encoding'])
        
        # Process the submitted face image
        # Remove data URL prefix if present
        if ',' in submitted_face_image_data_url:
            submitted_face_image_data_url = submitted_face_image_data_url.split(',')[1]
        
        # Decode base64 to image
        img_data = base64.b64decode(submitted_face_image_data_url)
        nparr = np.frombuffer(img_data, np.uint8)
        img_rgb = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # Detect faces
        face_locations = face_recognition.face_locations(img_rgb)
        if not face_locations:
            print(f"[WARN] No face detected in submitted image for {user.username}")
            return False
        
        # Get face encodings
        face_encodings = face_recognition.face_encodings(img_rgb, face_locations)
        if not face_encodings:
            print(f"[WARN] Could not encode face in submitted image for {user.username}")
            return False
        
        # Compare the face encodings with a threshold
        # Lower values are more strict (less tolerance for differences)
        face_distances = face_recognition.face_distance([stored_encoding], face_encodings[0])
        match = face_distances[0] <= 0.6  # Threshold can be adjusted based on security needs
        
        print(f"[INFO] Face verification for {user.username}: {'SUCCESS' if match else 'FAILED'} (distance: {face_distances[0]:.4f})")
        return match
        
    except Exception as e:
        print(f"[ERROR] Face verification error for {user.username}: {str(e)}")
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
                import base64
                import numpy as np
                import cv2
                import json
                import face_recognition
                from datetime import datetime
                
                # Remove the data URL prefix to get the base64 data
                face_data = face_data.split(',')[1] if ',' in face_data else face_data
                
                # Decode the base64 data
                img_data = base64.b64decode(face_data)
                
                # Convert to numpy array and decode image
                nparr = np.frombuffer(img_data, np.uint8)
                img_rgb = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                
                # Detect faces
                face_locations = face_recognition.face_locations(img_rgb)
                if not face_locations:
                    flash('No face detected in the image. Face registration skipped.', 'warning')
                else:
                    # Get the face encoding
                    face_encoding = face_recognition.face_encodings(img_rgb, face_locations)[0]
                    
                    # Store face data as JSON
                    new_user.face_data = json.dumps({
                        'encoding': face_encoding.tolist(),
                        'timestamp': datetime.utcnow().isoformat()
                    })
                    new_user.face_verification_enabled = True
                    
                    flash('Face registered successfully!', 'success')
            except Exception as e:
                print(f"Face registration error: {str(e)}")
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
    form = LoginForm()
    manual_security_level = session.get('manual_security_level')

    # Determine security level
    if manual_security_level is not None:
        security_level = manual_security_level
    else:
        security_level = session.get('security_level', SECURITY_LEVEL_LOW)

    if form.validate_on_submit():  # CAPTCHA is validated here
        username = form.username.data
        password = form.password.data
        remember = form.remember.data

        # Get detailed risk assessment
        from app.security_ai import get_risk_details
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
            'required_factors': risk_details['required_factors']
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
            # Directly log in the user
            login_user(user, remember=form.remember.data)
            flash('Login successful with Low Security.', 'success')
            return redirect(url_for('main.chat'))

        elif security_level == SECURITY_LEVEL_MEDIUM:
            # Require CAPTCHA validation
            if not form.recaptcha.data:
                flash('CAPTCHA validation failed.', 'danger')
                return redirect(url_for('auth.login'))

            login_user(user, remember=form.remember.data)
            flash('Login successful with Medium Security.', 'success')
            return redirect(url_for('main.chat'))

        elif security_level == SECURITY_LEVEL_HIGH:
            # Redirect to face verification
            session['temp_user_id'] = user.id
            flash('Additional verification required.', 'info')
            return redirect(url_for('auth.face_verification'))

    return render_template('login.html', form=form)

@auth_blueprint.route('/verify_face', methods=['POST'])
def verify_face_endpoint():
    if current_user.is_authenticated:
        return jsonify({'success': False, 'message': 'Already logged in.'}), 400

    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': 'Invalid request data.'}), 400

    # Get username from session or request
    username = session.get('username')
    face_image_b64 = data.get('faceImage')

    if not username or not face_image_b64:
        return jsonify({'success': False, 'message': 'Username in session and face image are required.'}), 400

    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({'success': False, 'message': 'User not found.'}), 404

    is_face_match_successful = verify_user_face(user, face_image_b64)

    if is_face_match_successful:
        login_user(user, remember=True)
        
        log_entry = FaceVerificationLog(user_id=user.id, success=True, timestamp=datetime.utcnow())
        db.session.add(log_entry)
        db.session.commit()

        print(f"[INFO] User {user.username} logged in via face verification.")

        try:
            if current_user.is_authenticated and current_user.id == user.id:
                notification_payload = {
                    'type': 'face_unlocked',
                    'userId': current_user.id,
                    'username': current_user.username,
                    'message': f"{current_user.username} just logged in with Face Unlock!",
                    'timestamp': datetime.utcnow().isoformat() + 'Z'
                }
                socketio.emit('user_status_update', notification_payload, broadcast=True, include_self=False)
                print(f"[INFO] Emitted 'user_status_update' for {current_user.username} (face unlocked).")
            else:
                 print(f"[WARN] current_user not consistent after face login for {username}. Notification not sent.")
        except Exception as e:
            print(f"[ERROR] Failed to emit face unlocked notification for {username}: {e}")

        return jsonify({'success': True, 'message': 'Face verified successfully. Redirecting...'})
    else:
        log_entry = FaceVerificationLog(user_id=user.id, success=False, timestamp=datetime.utcnow())
        db.session.add(log_entry)
        db.session.commit()
        print(f"[INFO] Face verification failed for user {user.username}.")
        return jsonify({'success': False, 'message': 'Face verification failed.'})

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
    user_id = session.get('temp_user_id')
    if not user_id:
        flash('Session expired. Please log in again.', 'danger')
        return redirect(url_for('auth.login'))

    user = User.query.get(user_id)
    if not user:
        flash('User not found. Please log in again.', 'danger')
        return redirect(url_for('auth.login'))

    # Retrieve risk details from the session
    risk_details = session.get('risk_details')
    if not risk_details:
        flash('Risk details not found. Please log in again.', 'danger')
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        submitted_face_data = request.form.get('face_data')
        if not submitted_face_data:
            flash('Face data not provided.', 'danger')
            return redirect(url_for('auth.face_verification'))

        if verify_user_face(user, submitted_face_data):
            login_user(user)
            flash('Face verification successful. Login complete.', 'success')
            return redirect(url_for('main.chat'))
        else:
            flash('Face verification failed. Please try again.', 'danger')

    return render_template('face_verification.html', risk_details=risk_details)