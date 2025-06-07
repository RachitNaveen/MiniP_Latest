#socket_events.py
from flask_socketio import emit, join_room, leave_room
from flask_login import current_user
from flask import request
from app import socketio, db
from app.models.models import Message
from datetime import datetime

# Track online users: {user_id: {'username': ..., 'sid': ...}}
online_users = {}

@socketio.on('connect')
def handle_connect(auth=None):
    if current_user.is_authenticated:
        online_users[current_user.id] = {'username': current_user.username, 'sid': request.sid}
        join_room(f"user_{current_user.id}")
        print(f"{current_user.username} connected and joined room user_{current_user.id}")
        print("Current online users:", online_users)

        user_list = [{'id': uid, 'username': u['username']} for uid, u in online_users.items()]
        print("Emitting user_list event with data:", user_list)
        emit('user_list', user_list, broadcast=True)

@socketio.on('disconnect')
def handle_disconnect():
    if current_user.is_authenticated:
        online_users.pop(current_user.id, None)
        leave_room(f"user_{current_user.id}")
        print(f"{current_user.username} disconnected")
        print("Current online users after disconnect:", online_users)

        user_list = [{'id': uid, 'username': u['username']} for uid, u in online_users.items()]
        print("Emitting user_list event with data:", user_list)
        emit('user_list', user_list, broadcast=True)

@socketio.on('send_message')
def handle_send_message(data):
    print(f"[DEBUG] current_user.id: {current_user.id}, current_user.username: {current_user.username}")
    if not current_user.is_authenticated:
        print("Unauthorized message attempt")
        return

    recipient_id = data.get('recipient_id')
    content = data.get('content')
    # --- MODIFICATION: Get the face_locked status from client data ---
    is_face_locked = data.get('face_locked', False) # Default to False if not provided

    if not recipient_id or not content:
        print("Invalid message data")
        # Consider emitting a status back to the sender only
        # emit('message_error', {'msg': 'Invalid message data'}, room=request.sid)
        return
    
    # Save message to database
    try:
        message = Message(
            sender_id=current_user.id,
            recipient_id=recipient_id,
            content=content,
            is_face_locked=is_face_locked,
            timestamp=datetime.utcnow()
        )
        db.session.add(message)
        db.session.commit()
        print(f"[DEBUG] Message saved to database with ID: {message.id}, face locked: {is_face_locked}")
        
        # Include the message ID in the payload so it can be referenced for unlocking
        payload = {
            'id': message.id,
            'content': content,
            'sender_id': current_user.id,
            'sender_username': current_user.username,
            'recipient_id': recipient_id,
            'is_face_locked': is_face_locked
        }
    except Exception as e:
        print(f"[ERROR] Failed to save message to database: {e}")
        # Still try to emit the message even if DB save fails
        import uuid
        temp_id = str(uuid.uuid4())  # Generate a unique temp ID
        print(f"[DEBUG] Using temp message ID: {temp_id} due to DB save failure")
        payload = {
            'id': temp_id,  # Include a temporary ID so frontend can reference it
            'content': content,
            'sender_id': current_user.id,
            'sender_username': current_user.username,
            'recipient_id': recipient_id,
            'is_face_locked': is_face_locked,
            'is_temp_id': True  # Flag to indicate this is not a real database ID
        }

    # Emit to sender's room (so they see their own message, potentially styled as locked or normal)
    emit('new_message', payload, room=f"user_{current_user.id}")
    # Emit to recipient's room
    if recipient_id != current_user.id: # Avoid double sending if sending to self (though UI should prevent)
        emit('new_message', payload, room=f"user_{recipient_id}")
    
    print(f"Message sent from user_{current_user.id} to user_{recipient_id}. Face Locked: {is_face_locked}")

    # Note: Emitting user_list on every message might be excessive if it's large.
    # Consider if this is necessary or can be optimized.
    emit('user_list', [{'id': uid, 'username': u['username']} for uid, u in online_users.items()], broadcast=True)

@socketio.on('new_file')
def handle_new_file(data):
    if not current_user.is_authenticated: # Added authentication check
        print("Unauthorized file attempt")
        return

    recipient_id = data.get('recipient_id')
    file_url = data.get('file_url')
    file_name = data.get('file_name')
    # --- MODIFICATION: Get the face_locked status from client data ---
    is_face_locked = data.get('face_locked', False) # Default to False if not provided


    if not recipient_id or not file_url or not file_name:
        print("[ERROR] Invalid file data:", data)
        return

    # For files, we need to create a database record to track face_locked status
    try:
        # Create a message with a file path
        message = Message(
            sender_id=current_user.id,
            recipient_id=recipient_id,
            content=f"Shared file: {file_name}",
            file_path=file_url,
            is_face_locked=is_face_locked,
            timestamp=datetime.utcnow()
        )
        db.session.add(message)
        db.session.commit()
        print(f"[DEBUG] File message saved to database with ID: {message.id}, face locked: {is_face_locked}")
        
        payload = {
            'id': message.id,
            'file_url': file_url,
            'file_name': file_name,
            'sender_id': current_user.id,
            'sender_username': current_user.username,
            'recipient_id': recipient_id,
            'is_face_locked': is_face_locked
        }
    except Exception as e:
        print(f"[ERROR] Failed to save file message to database: {e}")
        import uuid
        temp_id = str(uuid.uuid4())
        print(f"[DEBUG] Using temp file message ID: {temp_id} due to DB save failure")
        
        payload = {
            'id': temp_id,
            'file_url': file_url,
            'file_name': file_name,
            'sender_id': current_user.id,
            'sender_username': current_user.username,
            'recipient_id': recipient_id,
            'is_face_locked': is_face_locked,
            'is_temp_id': True
        }
    
    print(f"[DEBUG] Emitting new_file event with payload. Face Locked: {is_face_locked}", payload)
    print(f"[DEBUG] Emitting new_file event with payload. Face Locked: {is_face_locked}", payload)

    # Emit the event to the sender and recipient
    socketio.emit('new_file', payload, room=f"user_{current_user.id}")
    if recipient_id != current_user.id:
        socketio.emit('new_file', payload, room=f"user_{recipient_id}")
