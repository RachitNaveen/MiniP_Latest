from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

from app import db, socketio
from app.models import User, FaceVerificationLog
from app.forms import RegistrationForm, LoginForm  # Import the LoginForm

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
    IMPLEMENTATION REQUIRED: Retrieve stored face descriptor for the user.
    Extract descriptor from submitted_face_image_data_url.
    Compare descriptors and return True if they match, False otherwise.
    """
    print(f"[INFO] Placeholder: Verifying face for user {user.username}.")
    # Example: stored_desc = user.face_descriptor
    # submitted_desc = extract_descriptor(submitted_face_image_data_url)
    # if compare_descriptors(stored_desc, submitted_desc, threshold=0.6):
    #     return True
    # For this template, placeholder logic:
    if submitted_face_image_data_url and hasattr(user, 'username'): # Replace with actual check
        return True
    return False

# --- Routes ---
@auth_blueprint.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():  # This will validate the CAPTCHA automatically
        username = form.username.data
        password = form.password.data

        user = User.query.filter_by(username=username).first()
        if user:
            flash('Username already exists.', 'warning')
            return redirect(url_for('auth.register'))

        new_user = User(
            username=username,
            password_hash=generate_password_hash(password, method='pbkdf2:sha256')
        )
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
    if form.validate_on_submit():  # CAPTCHA is validated here
        username = form.username.data
        password = form.password.data
        remember = form.remember.data

        user = User.query.filter_by(username=username).first()

        if not user or not check_password_hash(user.password_hash, password):
            flash('Invalid username or password.', 'danger')
            return redirect(url_for('auth.login'))

        login_user(user, remember=remember)
        return redirect(url_for('main.chat'))

    return render_template('login.html', form=form)

@auth_blueprint.route('/verify_face', methods=['POST'])
def verify_face_endpoint():
    if current_user.is_authenticated:
        return jsonify({'success': False, 'message': 'Already logged in.'}), 400

    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': 'Invalid request data.'}), 400

    username = data.get('username')
    face_image_b64 = data.get('faceImage')

    if not username or not face_image_b64:
        return jsonify({'success': False, 'message': 'Username and face image are required.'}), 400

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