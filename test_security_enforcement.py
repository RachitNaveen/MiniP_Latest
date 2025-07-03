#!/usr/bin/env python3
"""
Test High Security Level with Face Verification
This script verifies that face verification is enforced for high security level.
"""
import requests
import json
import sys
import time

def test_high_security_enforcement():
    """Test that high security level properly enforces face verification"""
    base_url = 'http://127.0.0.1:5000'
    session = requests.Session()
    
    # Step 1: Set security level to HIGH
    print("\nStep 1: Setting security level to HIGH...")
    response = session.post(
        f"{base_url}/security/set_security_level_login",
        json={"level": "high"}
    )
    
    if response.ok:
        security_data = response.json()
        print(f"Security level set to {security_data.get('levelName')}")
        print(f"Required factors: {security_data.get('requiredFactors')}")
    else:
        print(f"Failed to set security level: {response.status_code}")
        return False
    
    # Step 2: Try to login with normal credentials (should prompt for face verification)
    print("\nStep 2: Logging in with credentials...")
    login_data = {
        'username': 'testuser2',
        'password': 'password123',
        'recaptcha': 'dummy_token'  # Bypass CAPTCHA for testing
    }
    
    login_response = session.post(
        f"{base_url}/login",
        data=login_data,
        allow_redirects=False
    )
    
    if login_response.status_code == 302:
        redirect_location = login_response.headers.get('Location', '')
        print(f"Login redirected to: {redirect_location}")
        
        if 'face_verification' in redirect_location:
            print("SUCCESS: User correctly redirected to face verification.")
        else:
            print(f"ERROR: User not redirected to face verification: {redirect_location}")
            return False
    else:
        print(f"Login failed with status code: {login_response.status_code}")
        return False
    
    # Step 3: Try to access chat directly (should fail or redirect)
    print("\nStep 3: Attempting to access chat directly (should be prevented)...")
    chat_response = session.get(
        f"{base_url}/chat",
        allow_redirects=False
    )
    
    if chat_response.status_code == 302:
        redirect_url = chat_response.headers.get('Location', '')
        print(f"Chat access redirected to: {redirect_url}")
        
        if 'login' in redirect_url or 'face_verification' in redirect_url:
            print("SUCCESS: Direct chat access properly restricted")
        else:
            print(f"WARNING: Unexpected redirect: {redirect_url}")
    elif chat_response.status_code == 200:
        print("ERROR: Chat access allowed without face verification!")
        return False
    else:
        print(f"Chat access returned status code: {chat_response.status_code}")
    
    print("\nTest completed! The system is enforcing face verification properly for high security mode.")
    return True

if __name__ == "__main__":
    test_high_security_enforcement()
