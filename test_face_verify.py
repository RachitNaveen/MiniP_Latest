#!/usr/bin/env python
"""
Test script for face verification functionality
This will test if face verification is working correctly with the existing database
"""
import sys
import json
import numpy as np
import os
import base64
import cv2
import face_recognition
from app import create_app, db
from app.models.models import User, FaceVerificationLog
from datetime import datetime

def test_face_verification(username=None):
    """Test face verification for a user"""
    app = create_app()
    with app.app_context():
        # Get user with face data
        if username:
            user = User.query.filter_by(username=username).first()
        else:
            # Get any user with face data
            user = User.query.filter(User.face_data.isnot(None)).first()
            
        if not user:
            print("No users with face data found. Please create a user with face verification first.")
            return False
            
        print(f"Testing face verification for user: {user.username}")
        
        # Check if user has face data
        if not user.face_data:
            print(f"User {user.username} has no face data registered!")
            return False
            
        # Parse the stored face data
        try:
            stored_face_data = json.loads(user.face_data)
            stored_encoding = np.array(stored_face_data['encoding']) 
            print(f"Successfully loaded face encoding. First 5 values: {stored_encoding[:5]}")
        except Exception as e:
            print(f"Error parsing face data: {e}")
            return False
            
        # Load the sample image for testing
        sample_image_path = os.path.join('app', 'static', 'sample_face.jpg')
        
        if not os.path.exists(sample_image_path):
            print(f"Sample face image not found at {sample_image_path}")
            print("Cannot test verification without a reference image")
            return False
            
        # Load and encode the face
        print(f"Loading test image from {sample_image_path}")
        try:
            image = face_recognition.load_image_file(sample_image_path)
            face_locations = face_recognition.face_locations(image)
            
            if not face_locations:
                print("No face detected in sample image.")
                return False
                
            test_encoding = face_recognition.face_encodings(image, face_locations)[0]
            print(f"Successfully generated test encoding. First 5 values: {test_encoding[:5]}")
            
            # Compare the encodings
            distance = np.linalg.norm(stored_encoding - test_encoding)
            match = distance <= 0.6  # Same threshold as we're using in the app
            
            print(f"Verification result: {'SUCCESS' if match else 'FAILED'}")
            print(f"Distance: {distance:.4f}, Threshold: 0.6")
            
            return match
            
        except Exception as e:
            print(f"Error during verification test: {e}")
            return False

if __name__ == "__main__":
    username = sys.argv[1] if len(sys.argv) > 1 else None
    success = test_face_verification(username)
    print(f"Test {'passed' if success else 'failed'}")
    sys.exit(0 if success else 1)
