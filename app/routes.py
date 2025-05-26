from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app, jsonify, send_from_directory
from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from app import db, socketio
from app.models import User, Message, LoginForm, MessageForm

import os
import base64
import json
import cv2
import numpy as np
from datetime import datetime
import face_recognition

# Create a Blueprint
bp = Blueprint('main', __name__)

# Home route
@bp.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('main.chat'))
    return redirect(url_for('main.login'))

# Login route
@bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    next_page = request.args.get('next')
    
    if request.method == 'POST':
        username = form.username.data
        password = form.password.data

        if not username or not password:
            flash('Username and password are required', 'error')
            return redirect(url_for('main.login', next=next_page))

        user = User.query.filter_by(username=username).first()

        if not user:
            flash('Invalid username or password', 'error')
            return redirect(url_for('main.login', next=next_page))

        # Verify password
        if not check_password_hash(user.password, password):
            flash('Invalid username or password', 'error')
            return redirect(url_for('main.login', next=next_page))

        # Clear any existing temp session data
        session.pop('temp_user_id', None)
        session.pop('next_page', None)
        
        # Store user ID in session for verification
        session['temp_user_id'] = user.id
        
        # Store next page in session
        if next_page:
            session['next_page'] = next_page
        
        # Check if face verification is required
        if user.face_data and current_app.config.get('FACE_VERIFICATION_REQUIRED', False):
            return redirect(url_for('main.face_verification'))
        
        # Otherwise log in directly
        login_user(user)
        return redirect(next_page or url_for('main.chat'))

    return render_template('login.html', form=form, next=next_page)

# Register route
@bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        face_data = request.form.get('faceData')
        
        # Validate input
        if not username or not password:
            flash('Username and password are required')
            return render_template('register.html')
            
        if password != confirm_password:
            flash('Passwords do not match')
            return render_template('register.html')
            
        # Check if username exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists')
            return render_template('register.html')
        
        # Create new user
        hashed_password = generate_password_hash(password)
        new_user = User(username=username, password=hashed_password)
        
        # Save face data if provided
        if face_data:
            try:
                # Remove the data URL prefix to get the base64 data
                face_data = face_data.split(',')[1] if ',' in face_data else face_data
                
                # Decode the base64 data
                img_data = base64.b64decode(face_data)
                
                # Convert to numpy array and decode image
                nparr = np.frombuffer(img_data, np.uint8)
                img_rgb = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                
                # Detect and encode face
                face_locations = face_recognition.face_locations(img_rgb)
                if not face_locations:
                    flash('No face detected in the image. Please try again with a clear face image.')
                    return render_template('register.html')
                    
                # Get the face encoding
                face_encoding = face_recognition.face_encodings(img_rgb, face_locations)[0]
                
                # Convert encoding to string and store
                new_user.face_data = json.dumps({
                    'encoding': face_encoding.tolist(),
                    'timestamp': datetime.utcnow().isoformat()
                })
                
            except Exception as e:
                flash(f'Error processing face image: {str(e)}')
                return render_template('register.html')
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful! Please login.')
        return redirect(url_for('main.login'))
        
    return render_template('register.html')

# Face verification route
@bp.route('/face_verification', methods=['GET', 'POST'])
def face_verification():
    temp_user_id = session.get('temp_user_id')
    if not temp_user_id:
        flash('No user session found')
        return redirect(url_for('main.login'))

    user = User.query.get(temp_user_id)
    if not user:
        flash('User not found')
        return redirect(url_for('main.login'))

    if request.method == 'POST':
        face_image = request.form.get('faceImage')
        if not face_image:
            flash('No face image provided')
            return redirect(url_for('main.face_verification'))

        try:
            # Process the incoming face image
            img_data = base64.b64decode(face_image.split(',')[1])
            nparr = np.frombuffer(img_data, np.uint8)
            img_rgb = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            # Load stored face data
            stored_face_data = user.face_data
            if not stored_face_data:
                return jsonify({'success': False, 'message': 'No stored face data found'}), 400
                
            try:
                stored_data = json.loads(stored_face_data)
                if 'encoding' not in stored_data:
                    return jsonify({'success': False, 'message': 'Invalid stored face data format'}), 400
                    
                stored_face_encoding = np.array(stored_data['encoding'])
            except json.JSONDecodeError:
                return jsonify({'success': False, 'message': 'Invalid JSON format in stored face data'}), 400
            except Exception as e:
                return jsonify({'success': False, 'message': f'Error processing stored face data: {str(e)}'}), 400
            
            # Detect faces
            face_locations = face_recognition.face_locations(img_rgb)
            if not face_locations:
                return jsonify({
                    'success': False,
                    'message': 'No face detected in the input image'
                }), 400
            
            # Get the first face encoding
            face_encoding = face_recognition.face_encodings(img_rgb, face_locations)
            if not face_encoding:
                return jsonify({
                    'success': False,
                    'message': 'Could not encode face from the input image'
                }), 400
            
            # Compare faces
            results = face_recognition.compare_faces([stored_face_encoding], face_encoding[0], tolerance=0.6)
            face_distance = face_recognition.face_distance([stored_face_encoding], face_encoding[0])[0]
            match_percentage = (1 - face_distance) * 100
            
            if results[0]:
                # Complete login process
                login_user(user)
                session.pop('temp_user_id', None)
                next_page = session.pop('next_page', None)
                return redirect(next_page or url_for('main.chat'))
            else:
                flash(f'Face verification failed ({match_percentage:.1f}% match, 80% required)')
                return redirect(url_for('main.face_verification'))
        except Exception as e:
            print(f"Face verification error: {str(e)}")
            flash('Error processing face verification')
            return redirect(url_for('main.face_verification'))

    return render_template('face_verification.html', username=user.username)

# API endpoint for face verification
@bp.route('/verify_face', methods=['POST'])
def verify_face():
    if request.method != 'POST':
        return jsonify({'success': False, 'message': 'Method not allowed'}), 405

    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No data received'}), 400

        face_image = data.get('faceImage')
        if not face_image:
            return jsonify({'success': False, 'message': 'No face image provided'}), 400

        # Get user from session
        temp_user_id = session.get('temp_user_id')
        if not temp_user_id:
            return jsonify({'success': False, 'message': 'No user session found'}), 400

        user = User.query.get(temp_user_id)
        if not user or not user.face_data:
            return jsonify({'success': False, 'message': 'User not found or no face data registered'}), 404

        try:
            # Process the incoming face image
            img_data = base64.b64decode(face_image.split(',')[1])
            nparr = np.frombuffer(img_data, np.uint8)
            img_rgb = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            # Load stored face data
            stored_face_data = user.face_data
            if not stored_face_data:
                return jsonify({'success': False, 'message': 'No stored face data found'}), 400
                
            try:
                stored_data = json.loads(stored_face_data)
                if 'encoding' not in stored_data:
                    return jsonify({'success': False, 'message': 'Invalid stored face data format'}), 400
                    
                stored_face_encoding = np.array(stored_data['encoding'])
            except json.JSONDecodeError:
                return jsonify({'success': False, 'message': 'Invalid JSON format in stored face data'}), 400
            except Exception as e:
                return jsonify({'success': False, 'message': f'Error processing stored face data: {str(e)}'}), 400
            
            # Detect faces
            face_locations = face_recognition.face_locations(img_rgb)
            if not face_locations:
                return jsonify({
                    'success': False,
                    'message': 'No face detected in the input image'
                }), 400
            
            # Get the first face encoding
            face_encoding = face_recognition.face_encodings(img_rgb, face_locations)
            if not face_encoding:
                return jsonify({
                    'success': False,
                    'message': 'Could not encode face from the input image'
                }), 400
            
            # Compare faces
            results = face_recognition.compare_faces([stored_face_encoding], face_encoding[0], tolerance=0.6)
            face_distance = face_recognition.face_distance([stored_face_encoding], face_encoding[0])[0]
            match_percentage = (1 - face_distance) * 100
            
            if results[0]:
                # Complete login process
                login_user(user)
                session.pop('temp_user_id', None)
                next_page = session.pop('next_page', None)
                
                # Get the redirect URL from session
                redirect_url = next_page or url_for('main.chat')
                
                return jsonify({
                    'success': True,
                    'verified': True,
                    'redirect_url': redirect_url
                })
            else:
                return jsonify({
                    'success': True,
                    'verified': False,
                    'match_percentage': match_percentage
                })
        except Exception as e:
            print(f"Face verification error: {str(e)}")
            return jsonify({'success': False, 'message': f'Error processing face: {str(e)}'}), 500

    except Exception as e:
        print(f"General error: {str(e)}")
        return jsonify({'success': False, 'message': f'Unexpected error: {str(e)}'}), 500

    return jsonify({'success': False, 'message': 'Method not allowed'}), 405

# Chat route (protected)
@bp.route('/chat', methods=['GET', 'POST'])
@login_required
def chat():
    form = MessageForm()
    users = User.query.filter(User.id != current_user.id).all()
    messages = Message.query.filter(
        ((Message.sender_id == current_user.id) | (Message.recipient_id == current_user.id))
    ).order_by(Message.timestamp.desc()).limit(50).all()
    messages.reverse()
    recipient_id = request.args.get('recipient_id', type=int)
    
    return render_template('chat.html', users=users, messages=messages, recipient_id=recipient_id, form=form)

# Send message API
@bp.route('/send_message', methods=['POST'])
@login_required
def send_message():
    recipient_id = request.form.get('recipient_id')
    if not recipient_id:
        return jsonify({'success': False, 'message': 'Recipient ID is required'}), 400

    recipient = User.query.get(recipient_id)
    if not recipient:
        return jsonify({'success': False, 'message': 'Recipient not found'}), 404

    # Get message content and face_locked from form data
    content = request.form.get('content', '')  # Default to empty string
    face_locked = request.form.get('face_locked', 'false').lower() == 'true'
    file = request.files.get('file')

    # Skip if both content and file are empty
    if not content.strip() and not file:
        return jsonify({'success': False, 'message': 'Message content or file is required'}), 400

    message = Message(
        sender_id=current_user.id,
        recipient_id=recipient_id,
        content=content,
        is_face_locked=face_locked,
        timestamp=datetime.utcnow()
    )

    # Handle file upload if present
    if file and file.filename:
        filename = secure_filename(file.filename)
        file_path = os.path.join('uploads', filename)
        
        # Create uploads directory if it doesn't exist
        uploads_dir = os.path.join(current_app.static_folder, 'uploads')
        if not os.path.exists(uploads_dir):
            os.makedirs(uploads_dir)
            
        file.save(os.path.join(uploads_dir, filename))
        message.file_path = file_path

    db.session.add(message)
    db.session.commit()

    # Emit new message event
    socketio.emit('new_message', {
        'message': message.content,
        'sender_id': current_user.id,
        'sender': {'username': current_user.username},
        'recipient_id': recipient_id,
        'recipient': {'username': recipient.username},
        'timestamp': message.timestamp.isoformat(),
        'file_path': message.file_path,
        'is_face_locked': message.is_face_locked
    }, room=f'user_{recipient_id}')

    return jsonify({'success': True, 'message_id': message.id})

# Get messages API
@bp.route('/get_messages')
@login_required
def get_messages():
    recipient_id = request.args.get('recipient_id', type=int)
    if not recipient_id:
        return jsonify({'success': False, 'message': 'Recipient ID is required'}), 400

    messages = Message.query.filter(
        ((Message.sender_id == current_user.id) & (Message.recipient_id == recipient_id)) |
        ((Message.sender_id == recipient_id) & (Message.recipient_id == current_user.id))
    ).order_by(Message.timestamp.desc()).limit(50).all()

    return jsonify({
        'success': True,
        'messages': [
            {
                'id': msg.id,
                'content': msg.content,
                'sender_id': msg.sender_id,
                'sender': {'username': msg.sender.username},
                'recipient_id': msg.recipient_id,
                'recipient': {'username': msg.recipient.username},
                'timestamp': msg.timestamp.isoformat(),
                'file_path': msg.file_path,
                'is_face_locked': msg.is_face_locked
            }
            for msg in reversed(messages)
        ]
    })

# File upload route
@bp.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(os.path.join(current_app.static_folder, 'uploads'), filename)

# Logout route
@bp.route('/logout')
@login_required
def logout():
    # Emit logout event to user's room
    socketio.emit('user_logout', room=f'user_{current_user.id}')
    logout_user()
    return redirect(url_for('main.login'))