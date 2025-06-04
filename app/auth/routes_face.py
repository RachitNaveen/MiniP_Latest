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

from flask import Blueprint, jsonify, request, session
from flask_login import current_user, login_required
from app.models.models import Message, User
from app.auth.auth import verify_user_face
from app import db
import logging
import base64
import numpy as np
import cv2
import face_recognition
import json
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
        return jsonify({'success': False, 'message': 'Invalid request data.'}), 400
    
    item_type = data.get('itemType')
    item_id = data.get('itemId')
    face_image = data.get('faceImage')
    
    if not all([item_type, item_id, face_image]):
        return jsonify({'success': False, 'message': 'Missing required fields.'}), 400
    
    # Verify the face matches the current user
    is_face_match = verify_user_face(current_user, face_image)
    
    if not is_face_match:
        return jsonify({'success': False, 'message': 'Face verification failed.'}), 401
    
    # If face matches, retrieve the content based on item type
    if item_type == 'message':
        message = Message.query.get(item_id)
        
        if not message:
            return jsonify({'success': False, 'message': 'Message not found.'}), 404
        
        # Check if the current user is either the sender or the recipient
        if message.sender_id != current_user.id and message.recipient_id != current_user.id:
            return jsonify({'success': False, 'message': 'You do not have permission to view this message.'}), 403
        
        # Return the unlocked content
        logger.info(f"Message {item_id} unlocked successfully by {current_user.username}")
        return jsonify({
            'success': True,
            'content': message.content,
            'itemId': message.id,
            'timestamp': message.timestamp.isoformat()
        })
        
    elif item_type == 'file':
        message = Message.query.get(item_id)
        
        if not message or not message.file_path:
            return jsonify({'success': False, 'message': 'File not found.'}), 404
        
        # Check if the current user is either the sender or the recipient
        if message.sender_id != current_user.id and message.recipient_id != current_user.id:
            return jsonify({'success': False, 'message': 'You do not have permission to view this file.'}), 403
        
        # Return the unlocked file info
        file_name = message.file_path.split('/')[-1]  # Extract filename from path
        logger.info(f"File {item_id} unlocked successfully by {current_user.username}")
        return jsonify({
            'success': True,
            'fileUrl': f'/uploads/{file_name}',
            'fileName': file_name,
            'itemId': message.id,
            'timestamp': message.timestamp.isoformat()
        })
    
    else:
        return jsonify({'success': False, 'message': 'Unknown item type.'}), 400

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
