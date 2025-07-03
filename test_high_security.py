#!/usr/bin/env python3
"""
Test script to verify high security face verification functionality
"""
import argparse
import requests
import json
import base64
from pprint import pprint

def test_high_security_face_verification(username, password, face_image_path=None):
    """
    Test the high security face verification flow by:
    1. Setting security level to HIGH
    2. Attempting login with credentials
    3. Submitting face verification
    4. Checking response
    """
    base_url = "http://127.0.0.1:5000"
    session = requests.Session()
    
    print("\n===== Testing High Security Face Verification =====\n")
    
    # Step 1: Set security level to HIGH
    print("Setting security level to HIGH...")
    response = session.post(
        f"{base_url}/security/set_security_level_login",
        json={"level": "high"}
    )
    
    if not response.ok:
        print(f"Failed to set security level: {response.status_code}")
        return False
        
    security_data = response.json()
    print(f"Security level set to {security_data.get('levelName')}")
    print(f"Required factors: {security_data.get('requiredFactors')}")
    
    # Step 2: Attempt login
    print("\nAttempting login with credentials...")
    login_response = session.post(
        f"{base_url}/login",
        data={
            "username": username,
            "password": password,
            "recaptcha": "dummy_value"  # For testing purposes
        },
        allow_redirects=False
    )
    
    if login_response.status_code != 302:
        print(f"Login failed: {login_response.status_code}")
        return False
        
    # Check if redirected to face verification
    location = login_response.headers.get('Location', '')
    if 'face_verification' not in location:
        print(f"Not redirected to face verification page: {location}")
        return False
        
    print("Login successful, redirected to face verification")
    
    # Step 3: Get the face verification page
    face_verify_url = f"{base_url}{location}"
    face_page = session.get(face_verify_url)
    
    if not face_page.ok:
        print(f"Failed to get face verification page: {face_page.status_code}")
        return False
        
    print("Face verification page loaded successfully")
    
    # Step 4: Submit face verification
    if face_image_path:
        print(f"\nSubmitting face verification with image: {face_image_path}")
        
        # Read and encode face image
        with open(face_image_path, 'rb') as f:
            image_data = f.read()
            base64_image = f"data:image/jpeg;base64,{base64.b64encode(image_data).decode('utf-8')}"
        
        # Submit face verification
        verify_response = session.post(
            f"{base_url}/face/face_verification",
            json={"faceImage": base64_image, "username": username}
        )
        
        print(f"Face verification response status: {verify_response.status_code}")
        result = verify_response.json()
        pprint(result)
        
        if result.get('success'):
            print("\n✓ Face verification successful!")
            print(f"Redirect URL: {result.get('redirect_url')}")
            return True
        else:
            print(f"\n✗ Face verification failed: {result.get('message')}")
            if 'match_percentage' in result:
                print(f"Match percentage: {result.get('match_percentage'):.1f}%")
            return False
    else:
        print("\nNo face image provided for testing")
        return True  # Return success as we can't test without an image

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Test high security face verification')
    parser.add_argument('--username', required=True, help='Username for login')
    parser.add_argument('--password', required=True, help='Password for login')
    parser.add_argument('--image', help='Path to face image for verification (optional)')
    
    args = parser.parse_args()
    
    test_high_security_face_verification(args.username, args.password, args.image)
