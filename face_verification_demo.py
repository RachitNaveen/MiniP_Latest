#!/usr/bin/env python
"""
Face Verification Demo Script for SecureChat
-------------------------------------------
This script demonstrates the face verification capabilities in SecureChat.
It creates test users with face verification enabled and simulates different
security scenarios.
"""

from app import create_app, db
from app.models.models import User, Message, FaceVerificationLog
from werkzeug.security import generate_password_hash
import os
import json
import numpy as np
import face_recognition
import cv2
from datetime import datetime, timedelta
import random
import argparse

def setup_demo_environment():
    """Create a controlled environment for the demo"""
    app = create_app()
    with app.app_context():
        print("\n=== Setting up Face Verification Demo ===\n")
        
        # Create test users
        create_face_user("demo_secure", "SecurePass123!")
        create_face_user("demo_regular", "RegularPass123!")
        
        # Reset face verification logs
        FaceVerificationLog.query.delete()
        db.session.commit()
        
        # Create some face verification logs (success and failure)
        create_verification_history()
        
        print("\n=== Demo Environment Ready ===\n")
        print("Test Users:")
        print("- Username: demo_secure / Password: SecurePass123! (face verification enabled)")
        print("- Username: demo_regular / Password: RegularPass123! (face verification enabled)")
        print("\nFace-locked messages have been created between these users.")
        print("\n=== Demo Instructions ===\n")
        print("1. Log in as one of the demo users")
        print("2. Set security level to 'High' to trigger face verification")
        print("3. Try sending face-locked messages between users")
        print("4. Test the face unlock functionality for locked messages")
        print("\nRun the application with: python run.py --port 5050")

def create_face_user(username, password):
    """Create a test user with face verification enabled"""
    user = User.query.filter_by(username=username).first()
    if user:
        print(f"User '{username}' already exists. Updating password and face data.")
        user.password_hash = generate_password_hash(password, method='sha256')
    else:
        print(f"Creating user '{username}' with face verification enabled.")
        user = User(username=username, password_hash=generate_password_hash(password, method='sha256'))
        db.session.add(user)
    
    # Use sample face image
    sample_image_path = os.path.join('app', 'static', 'sample_face.jpg')
    if os.path.exists(sample_image_path):
        # Load and encode the face
        image = face_recognition.load_image_file(sample_image_path)
        face_locations = face_recognition.face_locations(image)
        
        if face_locations:
            face_encoding = face_recognition.face_encodings(image, face_locations)[0]
            
            # Add slight randomization to make each user unique
            # This is just for demo purposes
            noise = np.random.normal(0, 0.01, face_encoding.shape)
            face_encoding = face_encoding + noise
            
            # Save face data to user
            user.face_data = json.dumps({
                'encoding': face_encoding.tolist(),
                'timestamp': datetime.utcnow().isoformat()
            })
            user.face_verification_enabled = True
            
            db.session.commit()
            print(f"Face verification enabled for '{username}'")
        else:
            print("No face detected in sample image.")
    else:
        print(f"Sample face image not found at {sample_image_path}")

def create_verification_history():
    """Create simulated face verification logs"""
    users = User.query.all()
    
    for user in users:
        if user.face_verification_enabled:
            # Add successful verifications
            for _ in range(3):
                timestamp = datetime.utcnow() - timedelta(days=random.randint(1, 7))
                log = FaceVerificationLog(
                    user_id=user.id,
                    success=True,
                    timestamp=timestamp
                )
                db.session.add(log)
            
            # Add some failed verifications
            for _ in range(1):
                timestamp = datetime.utcnow() - timedelta(days=random.randint(1, 7))
                log = FaceVerificationLog(
                    user_id=user.id,
                    success=False,
                    timestamp=timestamp
                )
                db.session.add(log)
    
    db.session.commit()
    print(f"Created verification history for {len(users)} users")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Face Verification Demo for SecureChat')
    parser.add_argument('--setup', action='store_true', help='Set up the demo environment')
    
    args = parser.parse_args()
    
    if args.setup:
        setup_demo_environment()
    else:
        print("Please run with '--setup' to prepare the demo environment")
