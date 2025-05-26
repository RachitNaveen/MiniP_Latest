import os
import base64
import logging
from flask import request, session, current_app
from flask_socketio import emit, join_room, leave_room
from app import socketio, db
from app.models import User, Message
from flask_login import current_user
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@socketio.on('connect')
def handle_connect():
    if current_user.is_authenticated:
        room = f"user_{current_user.id}"
        join_room(room)
        logger.info(f"{current_user.username} connected to room {room}")
        emit('status', {'msg': f'Connected to room {room}'})

@socketio.on('join')
def handle_join(data):
    if current_user.is_authenticated:
        room = f"user_{current_user.id}"
        join_room(room)
        logger.info(f"{current_user.username} joined room {room}")
        emit('status', {'msg': f'Joined room {room}'})

@socketio.on('disconnect')
def handle_disconnect():
    if current_user.is_authenticated:
        room = f"user_{current_user.id}"
        leave_room(room)
        logger.info(f"{current_user.username} disconnected from room {room}")
        emit('status', {'msg': f'Disconnected from room {room}'})

@socketio.on('send_message')
def handle_send_message(data):
    if not current_user.is_authenticated:
        logger.warning("Unauthorized message attempt")
        return

    recipient_id = data.get('recipient_id')
    content = data.get('content')
    is_face_locked = data.get('is_face_locked', False)

    if not recipient_id or not content:
        logger.warning("Invalid message data")
        emit('status', {'msg': 'Invalid message data'})
        return

    try:
        message = Message(
            sender_id=current_user.id,
            recipient_id=recipient_id,
            content=content,
            is_face_locked=is_face_locked
        )
        db.session.add(message)
        db.session.commit()

        # Emit message to both sender and recipient
        emit('new_message', {
            'id': message.id,
            'user_id': current_user.id,
            'recipient_id': recipient_id,
            'content': content,
            'is_face_locked': is_face_locked,
            'timestamp': message.timestamp.isoformat(),
            'author': {
                'id': current_user.id,
                'username': current_user.username
            }
        }, room=f"user_{current_user.id}")
        
        emit('new_message', {
            'id': message.id,
            'user_id': current_user.id,
            'recipient_id': recipient_id,
            'content': content,
            'is_face_locked': is_face_locked,
            'timestamp': message.timestamp.isoformat(),
            'author': {
                'id': current_user.id,
                'username': current_user.username
            }
        }, room=f"user_{recipient_id}")

        logger.info(f"Message sent from {current_user.id} to {recipient_id}")
    except Exception as e:
        logger.error(f"Error sending message: {str(e)}")
        emit('status', {'msg': f'Error sending message: {str(e)}'})

@socketio.on_error_default
def default_error_handler(e):
    logger.error(f"Socket.IO error: {str(e)}")
    emit('status', {'msg': f'Socket.IO error: {str(e)}'})
