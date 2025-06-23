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
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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
        if not os.path.isfile(sample_image_path):
            print(f"Sample image not found at {sample_image_path}. Please ensure the file exists.")
            return False

        # Load and encode the sample image
        try:
            sample_image = face_recognition.load_image_file(sample_image_path)
            sample_encoding = face_recognition.face_encodings(sample_image)[0]
            print(f"Sample face encoding loaded successfully. First 5 values: {sample_encoding[:5]}")
        except Exception as e:
            print(f"Error loading or encoding sample image: {e}")
            return False

        # Compare the stored encoding with the sample encoding
        match = face_recognition.compare_faces([stored_encoding], sample_encoding)
        if match[0]:
            print(f"Face verification successful for user: {user.username}")
            logging.info(f"Face verification successful for user: {user.username}")
            return True
        else:
            print(f"Face verification failed for user: {user.username}")
            logging.info(f"Face verification failed for user: {user.username}")
            return False

if __name__ == "__main__":
    username = sys.argv[1] if len(sys.argv) > 1 else None
    test_face_verification(username)
