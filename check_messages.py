#!/usr/bin/env python3
"""
Script to check existing messages in the database
"""
from app import create_app
from app.models.models import Message

app = create_app()

with app.app_context():
    messages = Message.query.all()
    
    if not messages:
        print("No messages found in the database.")
    else:
        print(f"Found {len(messages)} messages:")
        for msg in messages:
            print(f"ID: {msg.id}, Sender: {msg.sender_id}, Recipient: {msg.recipient_id}, " +
                  f"Face-locked: {msg.face_locked}, Attempts: {msg.unlock_attempts}")
