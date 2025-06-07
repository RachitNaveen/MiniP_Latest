from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app, jsonify, send_from_directory
from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from app import db, socketio
from app.models.models import User, Message
from app.auth.forms import LoginForm, RegistrationForm, MessageForm
from app.security.security_ai import SECURITY_LEVEL_LOW, SECURITY_LEVEL_MEDIUM, SECURITY_LEVEL_HIGH

import os
from datetime import datetime

# Import Socket.IO functions
from flask_socketio import emit, join_room, leave_room

# Create a Blueprint
bp = Blueprint('main', __name__)

# Home route
@bp.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('main.chat'))
    return redirect(url_for('main.login'))

# Profile route
@bp.route('/profile')
@login_required
def profile():
    # Get security level
    from sqlalchemy import desc
    
    security_level = session.get('security_level', SECURITY_LEVEL_LOW)
    security_level_name = "Low"
    
    if security_level == SECURITY_LEVEL_MEDIUM:
        security_level_name = "Medium"
    elif security_level == SECURITY_LEVEL_HIGH:
        security_level_name = "High"
    
    # Get face verification logs
    face_logs = current_user.face_logs.order_by(desc("timestamp")).limit(5).all()
    
    return render_template('profile.html', 
                          current_user=current_user,
                          security_level=security_level_name,
                          face_logs=face_logs)

# FIXED: Login route with proper security level handling
@bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    next_page = request.args.get('next')
    
    # Get the security level (check both session keys)
    manual_security_level = session.get('manual_security_level')
    session_security_level = session.get('security_level')
    
    # Use manual level if set, otherwise use session level, otherwise default to low
    if manual_security_level is not None:
        security_level = manual_security_level
    elif session_security_level is not None:
        security_level = session_security_level
    else:
        security_level = SECURITY_LEVEL_LOW  # Default to low
    
    print(f"DEBUG: Login route - manual_level: {manual_security_level}, session_level: {session_security_level}, using: {security_level}")
    
    # FIXED: Determine what authentication factors are required
    show_captcha = False
    require_face_verification = False
    
    if security_level == SECURITY_LEVEL_LOW:  # 0
        # Password only
        form.recaptcha.validators = []  # Remove CAPTCHA requirement
        show_captcha = False
        require_face_verification = False
        print("DEBUG: Low security - Password only")
        
    elif security_level == SECURITY_LEVEL_MEDIUM:  # 1
        # Password + CAPTCHA
        show_captcha = True
        require_face_verification = False
        print("DEBUG: Medium security - Password + CAPTCHA")
        
    elif security_level == SECURITY_LEVEL_HIGH:  # 2
        # Password + CAPTCHA + Face Verification
        show_captcha = True
        require_face_verification = True
        print("DEBUG: High security - Password + CAPTCHA + Face")
        
    else:  # AI or unknown
        # Default to medium for now
        show_captcha = True
        require_face_verification = False
        print(f"DEBUG: AI/Unknown security level {security_level} - defaulting to medium")
    
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        print(f"DEBUG: Login attempt for username: {username} with security level: {security_level}")
        user = User.query.filter_by(username=username).first()
        
        if user:
            print(f"DEBUG: Found user with username: {username}")
        
        # Check password
        if not user or not user.check_password(password):
            print(f"DEBUG: Password verification failed for user: {username}")
            flash('Invalid username or password', 'error')
            return render_template('login.html', form=form, next=next_page, 
                                 show_captcha=show_captcha, 
                                 require_face_verification=require_face_verification,
                                 security_level=security_level)

        # For high security, handle face verification
        if require_face_verification:
            print("DEBUG: High security login - face verification required")
            # Store credentials and info in session for face verification
            session['username'] = username
            session['next_page'] = next_page
            
            # Get risk assessment details 
            risk_details = {
                'security_level': 'High',
                'risk_score': 0.8,
                'required_factors': ['Password', 'CAPTCHA', 'Face Verification'],
                'risk_factors': {
                    'security_level': {'score': 0.8, 'description': 'High security verification required'}
                }
            }
            session['risk_details'] = risk_details
            
            # Redirect to face verification
            print("DEBUG: Redirecting to face verification page")
            return redirect(url_for('face.face_verification'))
            
        # No face verification required, proceed with login
        print(f"DEBUG: Login successful for user: {username}")
        login_user(user)
        return redirect(next_page or url_for('main.chat'))

    # Render the login template with security level info
    return render_template('login.html', form=form, next=next_page,
                         show_captcha=show_captcha,
                         require_face_verification=require_face_verification, 
                         security_level=security_level)

# Register route
@bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    
    # Get the security level to determine if CAPTCHA should be shown
    security_level = session.get('security_level', SECURITY_LEVEL_LOW)
    show_captcha = security_level in [SECURITY_LEVEL_MEDIUM, SECURITY_LEVEL_HIGH]
    
    # Remove CAPTCHA validation if not needed
    if not show_captcha and hasattr(form, 'recaptcha'):
        delattr(form.__class__, 'recaptcha')
    
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        
        print(f"DEBUG: Attempting to register user: {username}")
        
        # Check if username exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            print(f"DEBUG: Username {username} already exists")
            flash('Username already exists', 'error')
            return render_template('register.html', form=form, show_captcha=show_captcha)
        
        try:
            # FIXED: Create new user and use the set_password method
            new_user = User(username=username)
            new_user.set_password(password)  # Use the model's method instead
            
            print(f"DEBUG: Created user object for {username}")
            print(f"DEBUG: Password hash: {new_user.password_hash}")
            
            # Add and commit the new user to the database
            db.session.add(new_user)
            db.session.commit()
            
            print(f"DEBUG: Successfully saved user {username} to database")
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('main.login'))
            
        except Exception as e:
            print(f"DEBUG: Error creating user: {str(e)}")
            db.session.rollback()
            flash(f'Error creating user: {str(e)}', 'error')
            return render_template('register.html', form=form, show_captcha=show_captcha)
    
    # Show validation errors if any
    if form.errors:
        print(f"DEBUG: Form validation errors: {form.errors}")
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{field}: {error}', 'error')
        
    return render_template('register.html', form=form, show_captcha=show_captcha)

# Chat route (protected) - FIXED WITH DEBUGGING
@bp.route('/chat', methods=['GET', 'POST'])
@login_required
def chat():
    form = MessageForm()
    
    # DEBUG: Check current user
    print(f"DEBUG: Current user ID: {current_user.id}, Username: {current_user.username}")
    
    # Check total users in database
    total_users = User.query.count()
    print(f"DEBUG: Total users in database: {total_users}")
    
    # Get all users except current user
    all_users = User.query.all()
    print(f"DEBUG: All users in database:")
    for user in all_users:
        print(f"  - ID: {user.id}, Username: {user.username}")
    
    # Filter out current user
    users = User.query.filter(User.id != current_user.id).all()
    print(f"DEBUG: Other users (excluding current user): {len(users)}")
    for user in users:
        print(f"  - Available user: ID: {user.id}, Username: {user.username}")
    
    # Get messages for current user
    messages = Message.query.filter(
        ((Message.sender_id == current_user.id) | (Message.recipient_id == current_user.id))
    ).order_by(Message.timestamp.desc()).limit(50).all()
    
    print(f"DEBUG: Total messages for current user: {len(messages)}")
    for msg in messages:
        print(f"  - Message ID: {msg.id}, From: {msg.sender_id}, To: {msg.recipient_id}, Content: '{msg.content}'")
    
    messages.reverse()
    recipient_id = request.args.get('recipient_id', type=int)
    print(f"DEBUG: Recipient ID from URL: {recipient_id}")
    
    # If no users found, let's add some debug info to the template
    debug_info = {
        'total_users_in_db': total_users,
        'available_users': len(users),
        'current_user_id': current_user.id
    }
    
    return render_template('chat.html', 
                         users=users, 
                         messages=messages, 
                         recipient_id=recipient_id, 
                         form=form,
                         current_user=current_user,
                         debug_info=debug_info)

# FIXED: Send message API with proper Socket.IO emission
@bp.route('/send_message', methods=['POST'])
@login_required
def send_message():
    print(f"DEBUG: current_user.id = {current_user.id} current_user.username = {current_user.username}")
    
    # Debug: Print all form data
    print(f"DEBUG: Form data received: {dict(request.form)}")
    
    recipient_id = request.form.get('recipient_id')
    content = request.form.get('content')
    face_locked_raw = request.form.get('face_locked')
    
    print(f"DEBUG: recipient_id = {recipient_id}")
    print(f"DEBUG: content = '{content}'")
    print(f"DEBUG: face_locked_raw = '{face_locked_raw}'")
    
    # Fix face_locked parsing
    face_locked = face_locked_raw in ['true', 'True', '1', 'on'] if face_locked_raw else False
    print(f"DEBUG: face_locked parsed = {face_locked}")
    
    if not recipient_id:
        print("DEBUG: ERROR - Missing recipient_id")
        return jsonify({'success': False, 'message': 'Missing recipient'}), 400
        
    if not content or not content.strip():
        print("DEBUG: ERROR - Missing or empty content")
        return jsonify({'success': False, 'message': 'Missing content'}), 400
    
    recipient = User.query.get(recipient_id)
    if not recipient:
        print(f"DEBUG: ERROR - Recipient not found for ID: {recipient_id}")
        return jsonify({'success': False, 'message': 'Recipient not found'}), 404
    
    print(f"DEBUG: Recipient found: {recipient.username}")
    
    try:
        print("DEBUG: Creating message object...")
        message = Message(
            sender_id=current_user.id,
            recipient_id=int(recipient_id),
            content=content.strip(),
            is_face_locked=face_locked,
            timestamp=datetime.utcnow()
        )
        
        print(f"DEBUG: Message object created - sender_id: {message.sender_id}, recipient_id: {message.recipient_id}")
        
        db.session.add(message)
        print("DEBUG: Message added to session, attempting commit...")
        
        db.session.commit()
        print(f"DEBUG: Message successfully committed to database with ID: {message.id}")
        
        # Prepare message data for Socket.IO
        message_data = {
            'id': message.id,
            'content': message.content,
            'sender_id': current_user.id,
            'sender_username': current_user.username,
            'recipient_id': int(recipient_id),
            'recipient_username': recipient.username,
            'timestamp': message.timestamp.isoformat(),
            'is_face_locked': message.is_face_locked
        }
        
        print(f"DEBUG: Prepared message data for Socket.IO: {message_data}")
        
        # 🔥 IMPORTANT: Emit to recipient via Socket.IO
        recipient_room = f'user_{recipient_id}'
        print(f"DEBUG: Emitting to recipient room: {recipient_room}")
        
        try:
            socketio.emit('new_message', message_data, room=recipient_room)
            print(f"DEBUG: ✅ Successfully emitted new_message to {recipient_room}")
        except Exception as socketio_error:
            print(f"DEBUG: ❌ Socket.IO emit failed: {str(socketio_error)}")
        
        # Also emit to sender for confirmation (optional, but useful for debugging)
        sender_room = f'user_{current_user.id}'
        try:
            socketio.emit('message_confirmation', {
                'message': 'Message sent successfully',
                'message_id': message.id
            }, room=sender_room)
            print(f"DEBUG: ✅ Sent confirmation to sender room: {sender_room}")
        except Exception as confirm_error:
            print(f"DEBUG: ❌ Confirmation emit failed: {str(confirm_error)}")
        
        # Return the message data so sender can display it immediately
        print(f"DEBUG: 📤 Returning message data to HTTP client")
        return jsonify({
            'success': True, 
            'message_id': message.id,
            'message_data': message_data
        })
        
    except Exception as e:
        print(f"DEBUG: ERROR in send_message: {str(e)}")
        print(f"DEBUG: Exception type: {type(e)}")
        import traceback
        print(f"DEBUG: Traceback: {traceback.format_exc()}")
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

# Test Socket.IO connectivity
@bp.route('/test_socketio')
@login_required
def test_socketio():
    """Test if Socket.IO is working"""
    print(f"DEBUG: Testing Socket.IO for user {current_user.username}")
    
    # Send a test message to the current user's room
    try:
        socketio.emit('test_message', {
            'message': f'Test message for {current_user.username}',
            'timestamp': datetime.utcnow().isoformat()
        }, room=f'user_{current_user.id}')
        print(f"DEBUG: ✅ Sent test message to room user_{current_user.id}")
        
        return jsonify({'success': True, 'message': 'Test message sent via Socket.IO'})
    except Exception as e:
        print(f"DEBUG: ❌ Socket.IO test failed: {str(e)}")
        return jsonify({'success': False, 'message': f'Socket.IO test failed: {str(e)}'})

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

ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@bp.route('/upload_file', methods=['POST'])
@login_required
def upload_file():
    print("[DEBUG] request.files:", request.files)
    print("[DEBUG] request.form:", request.form)

    if 'file' not in request.files:
        print("[ERROR] No file part in request")
        return jsonify({'success': False, 'message': 'No file part'}), 400

    file = request.files['file']
    recipient_id = request.form.get('recipient_id')

    if not recipient_id or not file:
        print("[ERROR] Missing recipient ID or file")
        return jsonify({'success': False, 'message': 'Recipient ID and file are required'}), 400

    if not allowed_file(file.filename):
        print("[ERROR] File type not allowed:", file.filename)
        return jsonify({'success': False, 'message': 'File type not allowed'}), 400

    filename = secure_filename(file.filename)
    uploads_dir = os.path.join(current_app.static_folder, 'uploads')
    if not os.path.exists(uploads_dir):
        os.makedirs(uploads_dir)

    file_path = os.path.join(uploads_dir, filename)
    file.save(file_path)

    file_url = url_for('static', filename=f'uploads/{filename}', _external=True)

    payload = {
        'file_url': file_url,
        'file_name': filename,
        'sender_id': current_user.id,
        'recipient_id': recipient_id
    }
    print("[DEBUG] Emitting new_file event with payload:", payload)
    socketio.emit('new_file', payload, room=f"user_{current_user.id}")
    socketio.emit('new_file', payload, room=f"user_{recipient_id}")

    return jsonify({'success': True, 'file_url': file_url, 'file_name': filename})

# DEBUG ROUTE - Add this to your routes.py temporarily
@bp.route('/debug')
@login_required
def debug_users():
    """Debug route to check users in database"""
    all_users = User.query.all()
    
    debug_info = {
        'current_user': {
            'id': current_user.id,
            'username': current_user.username
        },
        'total_users': len(all_users),
        'all_users': []
    }
    
    for user in all_users:
        debug_info['all_users'].append({
            'id': user.id,
            'username': user.username,
            'created_at': user.last_login.isoformat() if user.last_login else 'Never'
        })
    
    return jsonify(debug_info)

# DEBUG ROUTE for session checking
@bp.route('/debug_session')
def debug_session():
    """Debug route to check session values"""
    return jsonify({
        'session_security_level': session.get('security_level'),
        'manual_security_level': session.get('manual_security_level'),
        'all_session_keys': list(session.keys()),
        'full_session': dict(session)
    })

# FIXED: Security level routes (no duplicates)
@bp.route('/set_security_level_login', methods=['POST'])
def set_security_level_login():
    """Set the security level for login attempts"""
    try:
        data = request.get_json()
        print(f"DEBUG: Security level change request: {data}")
        
        if not data:
            print("DEBUG: No JSON data received for security level")
            return jsonify({'success': False, 'message': 'No data provided'}), 400
        
        # Handle both 'security_level' and 'level' parameters for backwards compatibility
        security_level = data.get('security_level')
        if security_level is None:
            security_level = data.get('level')
        
        if security_level is None:
            print("DEBUG: Missing security_level in request")
            return jsonify({'success': False, 'message': 'Missing security_level'}), 400
        
        print(f"DEBUG: Raw security level received: {security_level} (type: {type(security_level)})")
        
        # Convert string values to numeric if needed
        if isinstance(security_level, str):
            level_mapping = {
                'low': 0,      # SECURITY_LEVEL_LOW
                'medium': 1,   # SECURITY_LEVEL_MEDIUM  
                'high': 2,     # SECURITY_LEVEL_HIGH
                'ai': 3        # AI mode
            }
            security_level = level_mapping.get(security_level.lower())
            if security_level is None:
                print(f"DEBUG: Invalid security level string: {data.get('security_level') or data.get('level')}")
                return jsonify({'success': False, 'message': 'Invalid security level'}), 400
        
        # Ensure it's an integer
        security_level = int(security_level)
        
        # FIXED: Validate against actual constants (assuming 0, 1, 2 based on errors)
        valid_levels = [0, 1, 2, 3]  # Low, Medium, High, AI
        if security_level not in valid_levels:
            print(f"DEBUG: Invalid security level number: {security_level}")
            return jsonify({'success': False, 'message': f'Invalid security level: {security_level}'}), 400
        
        # Store in session
        session['manual_security_level'] = security_level
        session['security_level'] = security_level
        
        # FIXED: Correct level name mapping
        level_names = {
            0: 'Low',       # SECURITY_LEVEL_LOW = 0
            1: 'Medium',    # SECURITY_LEVEL_MEDIUM = 1
            2: 'High',      # SECURITY_LEVEL_HIGH = 2
            3: 'AI-Based'   # AI mode = 3
        }
        
        level_name = level_names.get(security_level, 'Unknown')
        
        print(f"DEBUG: Security level set to {level_name} ({security_level})")
        print(f"DEBUG: Session values - manual_security_level: {session.get('manual_security_level')}, security_level: {session.get('security_level')}")
        
        return jsonify({
            'success': True,
            'message': f'Security level set to {level_name}',
            'security_level': security_level,
            'level_name': level_name
        })
        
    except Exception as e:
        print(f"DEBUG: Error setting security level: {str(e)}")
        import traceback
        print(f"DEBUG: Traceback: {traceback.format_exc()}")
        return jsonify({'success': False, 'message': f'Server error: {str(e)}'}), 500

# Route to get current security level
@bp.route('/get_security_level', methods=['GET'])
def get_security_level():
    """Get the current security level"""
    try:
        current_level = session.get('security_level', 0)  # Default to low (0)
        manual_level = session.get('manual_security_level')
        
        print(f"DEBUG: Getting security level - session: {current_level}, manual: {manual_level}")
        
        level_names = {
            0: 'Low',
            1: 'Medium', 
            2: 'High',
            3: 'AI-Based'
        }
        
        return jsonify({
            'success': True,
            'security_level': current_level,
            'level_name': level_names.get(current_level, 'Unknown'),
            'manual_security_level': manual_level
        })
        
    except Exception as e:
        print(f"DEBUG: Error getting security level: {str(e)}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

# Face unlock functionality
@bp.route('/unlock_item', methods=['POST'])
@login_required
def unlock_item():
    """Unlock a face-locked message or file after successful face verification"""
    print(f"DEBUG: unlock_item called by user {current_user.username}")
    
    try:
        # Get JSON data from request
        data = request.get_json()
        print(f"DEBUG: Unlock request data: {data}")
        
        if not data:
            print("DEBUG: No JSON data received")
            return jsonify({'success': False, 'message': 'No data provided'}), 400
        
        item_type = data.get('item_type')  # 'message' or 'file'
        item_id = data.get('item_id')
        
        print(f"DEBUG: Attempting to unlock {item_type} with ID: {item_id}")
        
        if not item_type or not item_id:
            print("DEBUG: Missing item_type or item_id")
            return jsonify({'success': False, 'message': 'Missing item_type or item_id'}), 400
        
        if item_type == 'message':
            # Find the message
            message = Message.query.get(item_id)
            if not message:
                print(f"DEBUG: Message {item_id} not found")
                return jsonify({'success': False, 'message': 'Message not found'}), 404
            
            # Check if current user is the recipient
            if message.recipient_id != current_user.id:
                print(f"DEBUG: User {current_user.id} is not the recipient of message {item_id}")
                return jsonify({'success': False, 'message': 'Unauthorized'}), 403
            
            # Check if message is actually face-locked
            if not message.is_face_locked:
                print(f"DEBUG: Message {item_id} is not face-locked")
                return jsonify({'success': False, 'message': 'Message is not face-locked'}), 400
            
            print(f"DEBUG: Successfully unlocking message {item_id}")
            return jsonify({
                'success': True,
                'item_type': 'message',
                'content': message.content,
                'sender_username': message.sender.username,
                'timestamp': message.timestamp.isoformat()
            })
        
        elif item_type == 'file':
            # Handle file unlocking (if you have file messages)
            print(f"DEBUG: File unlocking not yet implemented")
            return jsonify({'success': False, 'message': 'File unlocking not implemented yet'}), 501
        
        else:
            print(f"DEBUG: Invalid item_type: {item_type}")
            return jsonify({'success': False, 'message': 'Invalid item_type'}), 400
    
    except Exception as e:
        print(f"DEBUG: Error in unlock_item: {str(e)}")
        import traceback
        print(f"DEBUG: Traceback: {traceback.format_exc()}")
        return jsonify({'success': False, 'message': f'Server error: {str(e)}'}), 500

# Face verification route (placeholder)
@bp.route('/verify_face', methods=['POST'])
@login_required
def verify_face():
    """Handle face verification (placeholder - implement actual face recognition here)"""
    print(f"DEBUG: Face verification requested by user {current_user.username}")
    
    try:
        # For now, we'll just simulate successful verification
        # In a real app, you'd process the face image here
        
        data = request.get_json()
        print(f"DEBUG: Face verification data: {data}")
        
        # Simulate face verification (always succeed for now)
        verification_successful = True
        
        if verification_successful:
            print(f"DEBUG: Face verification successful for user {current_user.username}")
            return jsonify({
                'success': True,
                'message': 'Face verification successful',
                'user_id': current_user.id
            })
        else:
            print(f"DEBUG: Face verification failed for user {current_user.username}")
            return jsonify({
                'success': False,
                'message': 'Face verification failed'
            }), 401
    
    except Exception as e:
        print(f"DEBUG: Error in face verification: {str(e)}")
        return jsonify({'success': False, 'message': f'Verification error: {str(e)}'}), 500

# ===== SOCKET.IO EVENT HANDLERS =====

@socketio.on('connect')
def on_connect():
    print(f"DEBUG: Socket.IO connect event triggered")
    print(f"DEBUG: current_user.is_authenticated = {current_user.is_authenticated}")
    
    if current_user.is_authenticated:
        room_name = f'user_{current_user.id}'
        join_room(room_name)
        print(f"DEBUG: User {current_user.username} (ID: {current_user.id}) connected and joined room {room_name}")
        
        # Send updated user list to all connected users
        all_users = User.query.all()
        user_list = [{'id': user.id, 'username': user.username} for user in all_users]
        emit('user_list', user_list, broadcast=True)
        print(f"DEBUG: Sent user_list to all users: {user_list}")
        
        # Send a welcome message to confirm the connection
        emit('connection_confirmed', {
            'message': f'Connected successfully as {current_user.username}',
            'user_id': current_user.id,
            'room': room_name
        })
        print(f"DEBUG: Sent connection confirmation to {current_user.username}")
    else:
        print("DEBUG: Unauthenticated user attempted to connect")
        emit('error', {'message': 'Authentication required'})

@socketio.on('disconnect')
def on_disconnect():
    print(f"DEBUG: Socket.IO disconnect event triggered")
    if current_user.is_authenticated:
        room_name = f'user_{current_user.id}'
        leave_room(room_name)
        print(f"DEBUG: User {current_user.username} (ID: {current_user.id}) disconnected from room {room_name}")

@socketio.on('test_connection')
def handle_test_connection(data):
    """Test handler to verify Socket.IO is working"""
    print(f"DEBUG: Received test_connection from {current_user.username}: {data}")
    emit('test_response', {
        'message': f'Test successful for {current_user.username}',
        'received_data': data
    })

@socketio.on('send_message')
def handle_send_message(data):
    """BACKUP: Handle Socket.IO message sending (if needed)"""
    if not current_user.is_authenticated:
        emit('error', {'message': 'Not authenticated'})
        return
    
    print(f"DEBUG: Received send_message event from {current_user.username}: {data}")
    
    recipient_id = data.get('recipient_id')
    content = data.get('content', '')
    face_locked = data.get('face_locked', False)
    
    if not recipient_id:
        emit('error', {'message': 'Recipient ID is required'})
        return
    
    if not content.strip():
        emit('error', {'message': 'Message content is required'})
        return
    
    recipient = User.query.get(recipient_id)
    if not recipient:
        emit('error', {'message': 'Recipient not found'})
        return
    
    try:
        # Create and save message
        message = Message(
            sender_id=current_user.id,
            recipient_id=recipient_id,
            content=content,
            is_face_locked=face_locked,
            timestamp=datetime.utcnow()
        )
        
        db.session.add(message)
        db.session.commit()
        
        print(f"DEBUG: Message saved to database - ID: {message.id}")
        
        # Emit to both sender and recipient
        message_data = {
            'id': message.id,
            'content': message.content,
            'sender_id': current_user.id,
            'sender_username': current_user.username,
            'recipient_id': int(recipient_id),
            'recipient_username': recipient.username,
            'timestamp': message.timestamp.isoformat(),
            'is_face_locked': message.is_face_locked
        }
        
        # Emit to sender and recipient rooms
        for uid in [current_user.id, int(recipient_id)]:
            socketio.emit('new_message', message_data, room=f'user_{uid}')
            print(f"DEBUG: Emitted new_message to user_{uid}")
        
        # Send success response to sender
        emit('message_sent', {'success': True, 'message_id': message.id})
        
    except Exception as e:
        print(f"DEBUG: Error saving message: {str(e)}")
        db.session.rollback()
        emit('error', {'message': f'Error saving message: {str(e)}'})