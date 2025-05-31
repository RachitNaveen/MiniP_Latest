from flask_socketio import emit, join_room, leave_room
from flask_login import current_user
from flask import request
from app import socketio

# Track online users: {user_id: {'username': ..., 'sid': ...}}
online_users = {}

@socketio.on('connect')
def handle_connect(auth=None):
    if current_user.is_authenticated:
        # Add user to online users and join their private room
        online_users[current_user.id] = {'username': current_user.username, 'sid': request.sid}
        join_room(f"user_{current_user.id}")
        print(f"{current_user.username} connected and joined room user_{current_user.id}")

        # Debug log: Print the current online users
        print("Current online users:", online_users)

        # Notify all users about the updated online user list
        user_list = [
            {'id': uid, 'username': u['username']}
            for uid, u in online_users.items()
        ]
        print("Emitting user_list event with data:", user_list)  # Debug log
        emit('user_list', user_list, broadcast=True)

@socketio.on('disconnect')
def handle_disconnect():
    if current_user.is_authenticated:
        # Remove user from online users and leave their private room
        online_users.pop(current_user.id, None)
        leave_room(f"user_{current_user.id}")
        print(f"{current_user.username} disconnected")

        # Debug log: Print the current online users
        print("Current online users after disconnect:", online_users)

        # Notify all users about the updated online user list
        user_list = [
            {'id': uid, 'username': u['username']}
            for uid, u in online_users.items()
        ]
        print("Emitting user_list event with data:", user_list)  # Debug log
        emit('user_list', user_list, broadcast=True)

@socketio.on('send_message')
def handle_send_message(data):
    # Debug log to check the current user
    print(f"[DEBUG] current_user.id: {current_user.id}, current_user.username: {current_user.username}")

    if not current_user.is_authenticated:
        print("Unauthorized message attempt")
        return

    recipient_id = data.get('recipient_id')
    content = data.get('content')

    if not recipient_id or not content:
        print("Invalid message data")
        emit('status', {'msg': 'Invalid message data'})
        return

    # Emit the message to the sender's and recipient's private rooms
    payload = {
        'content': content,
        'sender_id': current_user.id,
        'sender_username': current_user.username,
        'recipient_id': recipient_id
    }
    emit('new_message', payload, room=f"user_{current_user.id}")
    emit('new_message', payload, room=f"user_{recipient_id}")
    print(f"Message sent from user_{current_user.id} to user_{recipient_id}")

    # Emit updated user list
    emit('user_list', [
        {'id': uid, 'username': u['username']}
        for uid, u in online_users.items()
    ], broadcast=True)

@socketio.on('new_file')
def handle_new_file(data):
    recipient_id = data.get('recipient_id')
    file_url = data.get('file_url')
    file_name = data.get('file_name')

    if not recipient_id or not file_url or not file_name:
        print("[ERROR] Invalid file data:", data)
        return

    payload = {
        'file_url': file_url,
        'file_name': file_name,
        'sender_id': current_user.id,
        'recipient_id': recipient_id
    }
    print("[DEBUG] Emitting new_file event with payload:", payload)

    # Emit the event to the sender and recipient
    socketio.emit('new_file', payload, room=f"user_{current_user.id}")
    socketio.emit('new_file', payload, room=f"user_{recipient_id}")