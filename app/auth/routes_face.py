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
from app.models.models import Message, User
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

# --- Routes ---

@face_blueprint.route('/face_verification', methods=['GET', 'POST'])
def face_verification():
    """Handle face verification during high security login"""
    print("[DEBUG] Face verification page requested")
    
    # Check if already logged in
    if current_user.is_authenticated:
        return redirect(url_for('main.chat'))
    
    # Get session data
    username = session.get('username') 
    risk_details = session.get('risk_details')
    next_page = session.get('next_page')
    
    print(f"[DEBUG] Face verification page - username: {username}")
    
    if not username or not risk_details:
        flash('Session expired. Please log in again.', 'danger')
        return redirect(url_for('auth.login'))
        
    # Get user
    user = User.query.filter_by(username=username).first()
    if not user:
        flash('User not found. Please log in again.', 'danger')
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        data = request.get_json()
        face_image = data.get('faceImage')
        
        if not face_image:
            return jsonify({'success': False, 'message': 'Face image required'}), 400
        
        # Verify the face
        if verify_user_face(user, face_image):
            # Log in and clear session data
            login_user(user)
            session.pop('username', None) 
            session.pop('risk_details', None)
            session.pop('next_page', None)
            
            return jsonify({
                'success': True,
                'message': 'Face verification successful',
                'redirect_url': next_page or url_for('main.chat')
            })
        else:
            # Calculate match percentage (for demo/testing)
            match_percentage = 65.0  # Example value
            
            return jsonify({
                'success': False,
                'message': 'Face verification failed',
                'match_percentage': match_percentage, 
                'risk_details': risk_details
            }), 401
    
    print(f"[DEBUG] Rendering face verification page for {username}")
    return render_template('face_verification.html', risk_details=risk_details, username=username)
