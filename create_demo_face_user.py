#!/usr/bin/env python
"""
Simple Face Verification Demo Script for SecureChat
"""

from app import create_app, db
from app.models.models import User
from werkzeug.security import generate_password_hash
import json
import numpy as np
from datetime import datetime
import os
import sys
import random

def create_face_user(username, password):
    """Create a test user with face verification enabled"""
    print("Starting face user creation...")
    app = create_app()
    print("App context created")
    with app.app_context():
        # Check if user exists
        user = User.query.filter_by(username=username).first()
        if user:
            print(f"User '{username}' already exists. Updating password and face data.")
            user.password_hash = generate_password_hash(password, method='sha256')
        else:
            print(f"Creating new user '{username}' with face verification enabled.")
            user = User(username=username, password_hash=generate_password_hash(password, method='sha256'))
            db.session.add(user)
        
        # Generate random face encoding as a fallback
        face_encoding = np.random.rand(128).astype(np.float64)
        
        # Save face data to user
        user.face_data = json.dumps({
            'encoding': face_encoding.tolist(),
            'timestamp': datetime.utcnow().isoformat()
        })
        user.face_verification_enabled = True
        
        db.session.commit()
        print(f"User '{username}' created with password '{password}' and face verification enabled.")
        print("You can now log in with this user to test face verification.")

if __name__ == "__main__":
    username = "facedemo" if len(sys.argv) <= 1 else sys.argv[1]
    password = "FaceDemo123!" if len(sys.argv) <= 2 else sys.argv[2]
    create_face_user(username, password)
