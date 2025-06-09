#!/usr/bin/env python3
"""
Script to create a test message for the face unlock feature
"""
from app import create_app, db
from app.models.models import Message, User
from datetime import datetime

app = create_app()

with app.app_context():
    # Get the testuser
    user = User.query.filter_by(username='testuser').first()
    if not user:
        print("testuser not found.")
        exit(1)
    
    # Create a face-locked message from testuser to testuser
    message = Message(
        sender_id=user.id,
        recipient_id=user.id,
        content="This is a face-locked test message",
        timestamp=datetime.utcnow(),
        face_locked=True,
        unlock_attempts=0,
        is_replaced=False
    )
    
    db.session.add(message)
    db.session.commit()
    
    print(f"Created test message with ID: {message.id}")
    print(f"Sender ID: {message.sender_id}")
    print(f"Recipient ID: {message.recipient_id}")
    print(f"Face-locked: {message.face_locked}")
