"""
Face Verification Module for SecureChat
---------------------------------------
This module handles face registration, verification, and face-locked message functionality.

Functions:
- verify_user_face: Compare a submitted face image with stored face data
- unlock_item: Endpoint to unlock face-locked messages and files
- face_status: Check if a user has face verification enabled

Usage:
- During registration, users can capture their face using the webcam
- During high-security logins, users must verify their face
- Users can send and receive face-locked messages that require face verification to view
"""

from flask import Blueprint, jsonify, request, session, render_template, redirect, url_for, flash, current_app
from flask_login import current_user, login_required, login_user
from app.models.models import Message, User, FaceVerificationLog
from app.auth.auth import verify_user_face
from app import db, socketio
import logging
import base64
import numpy as np
import cv2
import face_recognition
import json
import os
import uuid
from datetime import datetime
from app.static.face_api_models import FaceAPI

# Ensure logs directory exists
import os
if not os.path.exists('logs'):
    os.makedirs('logs', exist_ok=True)

# Set up logging to a file
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/routes_face.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Initialize FaceAPI with model paths
face_api = FaceAPI(
    model_path="app/static/face-api-models"
)

face_blueprint = Blueprint('face', __name__)

@face_blueprint.route('/face_status', methods=['GET'])
@login_required
def face_status():
    """Check if the current user has face verification enabled"""
    user = User.query.get(current_user.id)
    
    if not user:
        return jsonify({'success': False, 'message': 'User not found'}), 404
    
    return jsonify({
        'success': True,
        'face_verification_enabled': user.face_verification_enabled,
        'username': user.username
    })

@face_blueprint.route('/unlock_item', methods=['POST'])
@login_required
def unlock_item():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'Invalid request data.'}), 400

        item_id = data.get('itemId')
        item_type = data.get('itemType')
        face_image_b64 = data.get('faceImage')
        is_cancelled = data.get('cancelled', False)

        if not is_cancelled and (not item_id or not item_type):
            return jsonify({'success': False, 'message': 'Missing itemType or itemId from request.'}), 400

        message = Message.query.get(item_id)
        if not message:
            return jsonify({'success': False, 'message': 'Message not found.'}), 404

        if message.is_replaced:
            return jsonify({
                'success': False, 
                'message': 'This message was deleted due to too many failed unlock attempts.',
                'deleted': True
            }), 403

        if is_cancelled:
            message.unlock_attempts += 1
            if message.unlock_attempts >= 3:
                message.content = "MESSAGE DELETED"
                message.is_replaced = True
            db.session.commit()
            return jsonify({'success': True, 'message': 'Unlock cancelled.'})

        face_image = data.get('faceImage')
        if not face_image:
            return jsonify({'success': False, 'message': 'Missing required field: faceImage'}), 400

        try:
            if ',' in face_image:
                img_str = face_image.split(',')[1]
            else:
                img_str = face_image
            img_data = base64.b64decode(img_str)
            nparr = np.frombuffer(img_data, np.uint8)
            img_rgb = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if img_rgb is None:
                raise ValueError("Failed to decode image")
        except Exception as e:
            logger.error(f"[ERROR] Error decoding face image: {str(e)}")
            return jsonify({'success': False, 'message': 'Error processing face image.'}), 400

        is_match = verify_user_face(current_user, img_rgb)

        if is_match:
            message.unlock_attempts = 0
            db.session.commit()
            return jsonify({'success': True, 'content': message.content}), 200

        else:
            message.unlock_attempts += 1
            attempts_left = 3 - message.unlock_attempts
            logger.warning(f"[FAILURE] Face verification failed for user {current_user.username}, message {item_id}. Attempts: {message.unlock_attempts}")

            try:
                sender = User.query.get(message.sender_id)
                if sender:
                    filename = f"failed_attempt_{uuid.uuid4().hex}.jpg"
                    upload_folder = os.path.join(current_app.static_folder, 'intruder_snaps')
                    os.makedirs(upload_folder, exist_ok=True)
                    filepath = os.path.join(upload_folder, filename)

                    with open(filepath, 'wb') as f:
                        f.write(img_data)

                    image_url = url_for('static', filename=f'intruder_snaps/{filename}', _external=True)

                    room_name = f"user_{sender.id}"
                    socketio.emit('intruder_alert', {
                        'message': f"Alert: A failed attempt was made to unlock your message sent to {message.recipient.username}.",
                        'image_url': image_url,
                        'timestamp': datetime.utcnow().isoformat()
                    }, room=room_name)
                    logger.info(f"[INTRUDER] Notified sender {sender.username} of the failed attempt.")

            except Exception as e:
                logger.error(f"[INTRUDER] Failed to process and send intruder snapshot on failure: {e}")

            if attempts_left <= 0:
                logger.error(f"[DELETE] Message {item_id} deleted after 3 failed unlock attempts.")
                message.content = "MESSAGE DELETED"
                message.is_replaced = True
                db.session.commit()
                return jsonify({
                    'success': False, 
                    'message': 'Final attempt failed. The message has been permanently deleted.',
                    'deleted': True
                }), 403
            else:
                db.session.commit()
                return jsonify({
                    'success': False, 
                    'message': f'Face verification failed. You have {attempts_left} attempt(s) left.',
                    'attempts_left': attempts_left
                }), 403

    except Exception as e:
        logger.error(f"[UNLOCK_ITEM] Unexpected error: {str(e)}")
        return jsonify({'success': False, 'message': 'An unexpected error occurred. Please try again later.'}), 500

@face_blueprint.route('/update_face_data', methods=['POST'])
@login_required
def update_face_data():
    """Update or enable face data for the current user"""
    data = request.get_json()
    
    if not data or not data.get('faceData'):
        return jsonify({'success': False, 'message': 'No face data provided'})
    
    try:
        face_data = data.get('faceData')
        
        # Remove data URL prefix if present
        if ',' in face_data:
            face_data = face_data.split(',')[1]
        
        # Decode base64 to image
        img_data = base64.b64decode(face_data)
        nparr = np.frombuffer(img_data, np.uint8)
        img_rgb = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # Detect faces
        face_locations = face_recognition.face_locations(img_rgb)
        if not face_locations:
            return jsonify({'success': False, 'message': 'No face detected in the image'})
        
        # Get face encodings
        face_encoding = face_recognition.face_encodings(img_rgb, face_locations)[0]
        
        # Store face data
        current_user.face_data = json.dumps({
            'encoding': face_encoding.tolist(),
            'timestamp': datetime.utcnow().isoformat()
        })
        current_user.face_verification_enabled = True
        
        db.session.commit()
        logger.info(f"Face data updated for user {current_user.username}")
        
        return jsonify({'success': True, 'message': 'Face data updated successfully'})
    
    except Exception as e:
        logger.error(f"Error updating face data for {current_user.username}: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

@face_blueprint.route('/disable_face_verification', methods=['POST'])
@login_required
def disable_face_verification():
    """Disable face verification for the current user"""
    try:
        current_user.face_verification_enabled = False
        db.session.commit()
        logger.info(f"Face verification disabled for user {current_user.username}")
        
        return jsonify({'success': True, 'message': 'Face verification disabled'})
    
    except Exception as e:
        logger.error(f"Error disabling face verification for {current_user.username}: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

# --- Helper functions ---

def validate_face_verification_session(session_data):
    """
    Validates that the face verification session data is consistent and complete.
    Returns a tuple of (is_valid, error_message, user)
    """
    # Check required session data
    temp_user_id = session_data.get('temp_user_id')
    username = session_data.get('username')
    
    if not temp_user_id:
        return False, "Missing user ID in session", None
        
    if not username:
        return False, "Missing username in session", None
    
    # Get the user by ID
    user = User.query.get(temp_user_id)
    
    if not user:
        return False, f"User ID {temp_user_id} not found", None
    
    # Verify username matches the user ID
    if user.username != username:
        return False, f"Session username '{username}' does not match user ID {temp_user_id} (username: {user.username})", None
    
    return True, None, user

# --- Routes ---

@face_blueprint.route('/face_verification', methods=['GET', 'POST'])
def face_verification():
    """Handle face verification during high security login"""
    print("[DEBUG] Face verification page requested via face_blueprint")
    
    # Check if already logged in
    if current_user.is_authenticated:
        return redirect(url_for('main.chat'))
    
    # Validate the face verification session
    is_valid, error_message, user = validate_face_verification_session(session)
    
    if not is_valid:
        print(f"[ERROR] Face verification session validation failed: {error_message}")
        flash(f'Authentication error: {error_message}. Please log in again.', 'danger')
        return redirect(url_for('auth.login'))
        
    # Get remaining session data
    username = session.get('username')  # We know this exists and matches user.username from validation
    risk_details = session.get('risk_details')
    next_page = session.get('next_page')
    high_security_auth = session.get('high_security_auth', False)
    face_verification_required = session.get('face_verification_required', False)
    
    print(f"[DEBUG] Face verification page - session data: high_security_auth={high_security_auth}, face_verification_required={face_verification_required}")
    print(f"[DEBUG] Face verification page - username: {username}, user_id: {user.id}")
    print(f"[DEBUG] Face verification page - risk_details: {risk_details}")
    
    # If no risk details, create default high security risk details
    if not risk_details:
        print("[DEBUG] Creating default high security risk details")
        risk_details = {
            'security_level': 'High',
            'security_level_num': 2, # HIGH level
            'risk_score': 0.85,
            'risk_factors': {
                'login_time': {'score': 0.7, 'description': 'Login at unusual time'},
                'ip_address': {'score': 0.8, 'description': 'Connection from unusual location'},
                'login_frequency': {'score': 0.9, 'description': 'Multiple login attempts detected'}
            },
            'required_factors': ['Password', 'CAPTCHA', 'Face Verification']
        }
        session['risk_details'] = risk_details
    
    if request.method == 'POST':
        # Re-validate session to ensure it's still valid
        is_valid, error_message, user = validate_face_verification_session(session)
        
        if not is_valid:
            print(f"[ERROR] Face verification POST validation failed: {error_message}")
            return jsonify({
                'success': False, 
                'message': f'Authentication error: {error_message}. Please log in again.',
                'redirect_url': url_for('auth.login')
            }), 401
            
        data = request.get_json()
        face_image = data.get('faceImage')
        
        if not face_image:
            return jsonify({'success': False, 'message': 'Face image required'}), 400
        
        print(f"[DEBUG] Processing face verification for: {username}")
        print(f"[DEBUG] Face image data length: {len(face_image) if face_image else 'None'}")
        
        # Process the face image
        try:
            import base64
            import numpy as np
            import cv2
            import json
            import face_recognition
            
            # Extract the base64 data
            if ',' in face_image:
                face_image = face_image.split(',')[1]
                
            # Decode the image
            img_data = base64.b64decode(face_image)
            nparr = np.frombuffer(img_data, np.uint8)
            img_rgb = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if img_rgb is None:
                print(f"[ERROR] Failed to decode image")
                return jsonify({'success': False, 'message': 'Failed to decode image'}), 400
                
            # Get face encodings from the image
            face_locations = face_recognition.face_locations(img_rgb)
            
            if not face_locations:
                print(f"[ERROR] No face detected in the image")
                return jsonify({
                    'success': False, 
                    'message': 'No face detected in the image. Please try again.',
                    'match_percentage': 0.0,
                    'risk_details': risk_details
                }), 400
                
            face_encoding = face_recognition.face_encodings(img_rgb, face_locations)[0]
            
            # Get the stored face data
            if not user.face_data or not user.face_verification_enabled:
                print(f"[ERROR] User {username} does not have face verification enabled")
                return jsonify({
                    'success': False, 
                    'message': 'Face verification is not set up for this user.',
                    'match_percentage': 0.0,
                    'risk_details': risk_details
                }), 400
                
            stored_face_data = json.loads(user.face_data)
            stored_encoding = np.array(stored_face_data['encoding'])
            
            # Compare the face encodings
            face_distance = face_recognition.face_distance([stored_encoding], face_encoding)[0]
            match_percentage = (1 - face_distance) * 100
            
            # Face verification threshold (0.6 distance = 40% match)
            if face_distance < 0.6:  # Lower distance is better match
                # Log successful face verification
                print(f"[DEBUG] Face verification SUCCESSFUL for: {username} with distance {face_distance}")
                
                # Mark face verification as completed
                session['face_verification_required'] = False
                
                # Double-check that we're logging in the correct user from session
                temp_user_id = session.get('temp_user_id')
                session_username = session.get('username')
                
                if not temp_user_id or not session_username or user.id != temp_user_id or user.username != session_username:
                    print(f"[ERROR] User mismatch during login: session_user_id={temp_user_id}, user.id={user.id}, session_username={session_username}, user.username={user.username}")
                    return jsonify({
                        'success': False,
                        'message': 'Authentication error: user mismatch. Please log in again.',
                        'redirect_url': url_for('auth.login')
                    }), 401
                
                # Log in the correct user
                print(f"[DEBUG] Logging in user: id={user.id}, username={user.username}")
                login_user(user)
                
                # Update user's last login time
                user.last_login = datetime.utcnow()
                db.session.commit()
                
                # Log the successful verification
                try:
                    log_entry = FaceVerificationLog(
                        user_id=user.id,
                        success=True,
                        match_percentage=match_percentage,
                        timestamp=datetime.utcnow()
                    )
                    db.session.add(log_entry)
                    db.session.commit()
                    print(f"[INFO] Face verification log entry created for user {user.username}")
                except Exception as e:
                    print(f"[ERROR] Failed to log face verification: {str(e)}")
                
                # Clear session data related to verification
                session.pop('username', None) 
                session.pop('risk_details', None)
                session.pop('next_page', None)
                session.pop('face_verification_required', None)
                session.pop('temp_user_id', None)
                
                # Keep a record that face verification was successful
                session['face_verified'] = True
                session['face_verified_time'] = datetime.utcnow().timestamp()
                
                print(f"[DEBUG] Face verification successful. Session updated: face_verified=True")
                
                return jsonify({
                    'success': True,
                    'message': 'Face verification successful',
                    'redirect_url': next_page or url_for('main.chat')
                })
            else:
                print(f"[DEBUG] Face verification FAILED for: {username} with distance {face_distance}")
                
                return jsonify({
                    'success': False,
                    'message': f'Face verification failed. Not enough similarity ({match_percentage:.1f}% match).',
                    'match_percentage': match_percentage,
                    'risk_details': risk_details
                }), 401
                
        except Exception as e:
            print(f"[ERROR] Exception during face verification: {str(e)}")
            return jsonify({
                'success': False,
                'message': f'Error during face verification: {str(e)}',
                'match_percentage': 0.0,
                'risk_details': risk_details
            }), 500
    
    print(f"[DEBUG] Rendering face verification page for {username}")
    return render_template('face_verification.html', risk_details=risk_details, username=username)

@face_blueprint.route('/debug_user_session', methods=['GET'])
@login_required
def debug_user_session():
    """Debug endpoint to verify the current user session"""
    try:
        return jsonify({
            'success': True,
            'user': {
                'id': current_user.id,
                'username': current_user.username
            },
            'session_data': {
                'temp_user_id': session.get('temp_user_id'),
                'username': session.get('username'),
                'face_verified': session.get('face_verified'),
                'security_level': session.get('security_level'),
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
