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
        if not os.path.isfile(sample_image_path):
            print(f"Sample image not found at path: {sample_image_path}")
            return False
            
        # Read and encode the sample image
        try:
            with open(sample_image_path, "rb") as image_file:
                encoded_image = base64.b64encode(image_file.read()).decode('utf-8')
                print(f"Successfully encoded sample image. Length of encoded data: {len(encoded_image)}")
        except Exception as e:
            print(f"Error encoding sample image: {e}")
            return False
            
        # Perform face verification
        try:
            # Here we simulate the face verification process
            # In a real scenario, you would compare the stored_encoding with the encoding of the sample image
            results = face_recognition.compare_faces([stored_encoding], encoded_image)
            print(f"Face verification results: {results}")
        except Exception as e:
            print(f"Error during face verification: {e}")
            return False
            
        print("Face verification test completed.")
        return True

if __name__ == "__main__":
    # For manual testing, you can specify a username as a command line argument
    username = sys.argv[1] if len(sys.argv) > 1 else None
    test_face_verification(username)
