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

from flask import Blueprint, jsonify, request, session, render_template, redirect, url_for, flash
from flask_login import current_user, login_required, login_user
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
from app.static.face_api_models import FaceAPI

# Set up logging to a file
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("/Users/rajattripathi/Documents/GitHub/MiniP_Latest/logs/routes_face.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Initialize FaceAPI with model paths
face_api = FaceAPI(
    model_path="/Users/rajattripathi/Documents/GitHub/MiniP_Latest/app/static/face-api-models"
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

    item_type = data.get('itemType')
    item_id = data.get('itemId')
    face_image = data.get('faceImage')

    # Log missing fields
    missing_fields = []
    if not item_type:
        missing_fields.append('itemType')
    if not item_id:
        missing_fields.append('itemId')
    if not face_image:
        missing_fields.append('faceImage')

    if missing_fields:
        logger.warning(f"[WARNING] Missing required fields: {', '.join(missing_fields)}")
        return jsonify({'success': False, 'message': f"Missing required fields: {', '.join(missing_fields)}"}), 400

    # Debugging: Log the received faceImage
    logger.debug(f"[DEBUG] Received request payload: {data}")
    logger.debug(f"[DEBUG] faceImage content: {face_image[:30] if face_image else 'None'}")
    logger.debug(f"[DEBUG] Stored face data: {current_user.face_data[:30] if current_user.face_data else 'None'}")

    # Ensure faceImage is base64-decoded
    if ',' in face_image:
        face_image = face_image.split(',')[1]

    try:
        img_data = base64.b64decode(face_image)
        nparr = np.frombuffer(img_data, np.uint8)
        img_rgb = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if img_rgb is None:
            logger.error("[ERROR] Failed to decode face image")
            return jsonify({'success': False, 'message': 'Invalid face image format.'}), 400
        logger.debug("[DEBUG] Face image successfully decoded")

    except Exception as e:
        logger.error(f"[ERROR] Error decoding face image: {str(e)}")
        return jsonify({'success': False, 'message': 'Error processing face image.'}), 400

    # Verify face using FaceAPI
    try:
        face_locations = face_recognition.face_locations(img_rgb)
        if not face_locations:
            return jsonify({'success': False, 'message': 'No face detected in the input image'}), 400

        face_encoding = face_recognition.face_encodings(img_rgb, face_locations)
        if not face_encoding:
            return jsonify({'success': False, 'message': 'Could not encode face from the input image'}), 400

        stored_data = json.loads(current_user.face_data)
        stored_face_encoding = np.array(stored_data['encoding'])

        results = face_recognition.compare_faces([stored_face_encoding], face_encoding[0], tolerance=0.6)
        face_distance = face_recognition.face_distance([stored_face_encoding], face_encoding[0])[0]
        match_percentage = (1 - face_distance) * 100

        if results[0]:
            # Retrieve the content based on item type
            if item_type == 'message':
                message = Message.query.get(item_id)
                if not message:
                    return jsonify({'success': False, 'message': 'Message not found.'}), 404
                return jsonify({'success': True, 'content': message.content}), 200
            elif item_type == 'file':
                message = Message.query.get(item_id)
                if not message or not message.file_path:
                    return jsonify({'success': False, 'message': 'File not found.'}), 404
                return jsonify({'success': True, 'fileUrl': message.file_path, 'fileName': message.content}), 200
            else:
                return jsonify({'success': False, 'message': 'Invalid item type.'}), 400
        else:
            logger.warning(f"[WARNING] Face verification failed ({match_percentage:.1f}% match, 80% required)")
            return jsonify({'success': False, 'message': 'Face verification failed'}), 403

    except Exception as e:
        logger.error(f"[ERROR] Error unlocking item: {e}")
        return jsonify({'success': False, 'message': 'An error occurred during face verification'}), 500

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
