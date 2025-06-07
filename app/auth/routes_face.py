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

# auth/Routes_face.py

from flask import Blueprint, jsonify, request, session
from flask_login import current_user, login_required
from app.models.models import Message, User, FaceVerificationLog
from app.auth.auth import verify_user_face
from app import db
import logging
import base64
import numpy as np
import cv2
import face_recognition
import json
from datetime import datetime
from app.static.face_api_models import FaceAPI

# Set up logging to a file
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("/Users/tshreek/MiniP_Latest/logs/routes_face.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Initialize FaceAPI with model paths
face_api = FaceAPI(
    model_path="/Users/tshreek/minip_latest/app/static/face-api-models"
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
    """Endpoint to unlock a face-locked message or file"""
    data = request.get_json()

    if not data:
        logger.warning("[WARNING] Request data is empty or invalid.")
        return jsonify({'success': False, 'message': 'Invalid request data.'}), 400

    item_id = data.get('itemId')
    item_type = data.get('itemType', 'message') # Default to message for safety
    face_image = data.get('faceImage')
    is_cancelled = data.get('cancelled', False)

    if not item_id:
        return jsonify({'success': False, 'message': 'Missing required field: itemId'}), 400

    # Retrieve the message first
    message = Message.query.get(item_id)
    if not message:
        return jsonify({'success': False, 'message': 'Message not found.'}), 404

    # Deny access if message is already replaced
    if message.is_replaced:
        return jsonify({
            'success': False, 
            'message': 'This message was deleted due to too many failed unlock attempts.',
            'deleted': True
        }), 403

    # --- Handle Cancellation ---
    if is_cancelled:
        # We still count cancellation as a failed attempt
        message.unlock_attempts += 1
        logger.warning(f"[CANCEL] User cancelled unlock for message {item_id}. Attempt count is now {message.unlock_attempts}.")
        if message.unlock_attempts >= 3:
            message.content = "MESSAGE DELETED"
            message.is_replaced = True
            db.session.commit()
            return jsonify({
                'success': False,
                'message': 'Message deleted after too many failed attempts.',
                'deleted': True
            }), 403
        
        db.session.commit()
        return jsonify({
            'success': True, 
            'message': 'Unlock cancelled.', 
            'attempts_left': 3 - message.unlock_attempts
        }), 200

    # --- Handle Face Verification ---
    if not face_image:
        return jsonify({'success': False, 'message': 'Missing required field: faceImage'}), 400

    # Decode the image for verification
    try:
        if ',' in face_image:
            face_image = face_image.split(',')[1]
        img_data = base64.b64decode(face_image)
        nparr = np.frombuffer(img_data, np.uint8)
        img_rgb = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img_rgb is None:
            raise ValueError("Failed to decode image")
    except Exception as e:
        logger.error(f"[ERROR] Error decoding face image: {str(e)}")
        return jsonify({'success': False, 'message': 'Error processing face image.'}), 400

    # Perform face verification
    is_match = verify_user_face(img_rgb, current_user) # Assuming verify_user_face returns a boolean

    if is_match:
        # --- SUCCESSFUL Verification ---
        logger.info(f"[SUCCESS] User {current_user.username} unlocked message {item_id}.")
        # Optional: Reset attempts on success
        message.unlock_attempts = 0
        db.session.commit()

        # Log successful verification
        log_entry = FaceVerificationLog(user_id=current_user.id, success=True)
        db.session.add(log_entry)
        db.session.commit()

        if item_type == 'message':
            return jsonify({'success': True, 'content': message.content}), 200
        elif item_type == 'file':
            return jsonify({'success': True, 'fileUrl': message.file_path, 'fileName': message.content}), 200
        else:
            return jsonify({'success': False, 'message': 'Invalid item type.'}), 400

    else:
        # --- FAILED Verification ---
        message.unlock_attempts += 1
        attempts_left = 3 - message.unlock_attempts
        logger.warning(f"[FAILURE] Face verification failed for user {current_user.username}, message {item_id}. Attempts: {message.unlock_attempts}")

        if attempts_left <= 0:
            # --- FINAL ATTEMPT FAILED ---
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
            # --- FAILED, BUT ATTEMPTS REMAIN ---
            db.session.commit()
            return jsonify({
                'success': False, 
                'message': f'Face verification failed. You have {attempts_left} attempt(s) left.',
                'attempts_left': attempts_left
            }), 403

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

    logger.debug(f"[DEBUG] Face verification enabled for user {current_user.username}: {current_user.face_verification_enabled}")
    logger.debug(f"[DEBUG] Face data stored for user {current_user.username}: {'Yes' if current_user.face_data else 'No'}")
