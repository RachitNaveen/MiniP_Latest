#!/usr/bin/env python
# Create a test user with face verification enabled
import sys
from app import db, create_app
from app.models.models import User
from werkzeug.security import generate_password_hash
import json
import numpy as np
import cv2
import os
import face_recognition
from datetime import datetime

def create_face_user(username="testface", password="Face123!"):
    """Create a test user with face verification enabled using a default face"""
    app = create_app()
    with app.app_context():
        # Check if user exists
        user = User.query.filter_by(username=username).first()
        if user:
            print(f"User '{username}' already exists. Updating password and face data.")
            user.password_hash = generate_password_hash(password)
        else:
            print(f"Creating new user '{username}' with face verification enabled.")
            user = User(username=username, password_hash=generate_password_hash(password))
            db.session.add(user)
        
        # Use a sample face image
        sample_image_path = os.path.join('app', 'static', 'sample_face.jpg')
        
        if not os.path.exists(sample_image_path):
            print(f"Sample face image not found at {sample_image_path}")
            print("Using a random face encoding instead")
            # Generate random face encoding as a fallback
            face_encoding = np.random.rand(128).astype(np.float64)
        else:
            # Load and encode the face
            image = face_recognition.load_image_file(sample_image_path)
            face_locations = face_recognition.face_locations(image)
            
            if not face_locations:
                print("No face detected in sample image. Using random encoding.")
                face_encoding = np.random.rand(128).astype(np.float64)
            else:
                face_encoding = face_recognition.face_encodings(image, face_locations)[0]
        
        # Save face data to user
        user.face_data = json.dumps({
            'encoding': face_encoding.tolist(),
            'timestamp': datetime.utcnow().isoformat()
        })
        user.face_verification_enabled = True
        
        db.session.commit()
        print(f"User '{username}' created with password '{password}' and face verification enabled.")
        print("You can now log in with this user to test face verification.")

if __name__ == '__main__':
    username = sys.argv[1] if len(sys.argv) > 1 else "testface"
    password = sys.argv[2] if len(sys.argv) > 2 else "Face123!"
    create_face_user(username, password)
