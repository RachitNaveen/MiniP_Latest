#!/usr/bin/env python3
"""
End-to-end test for AI-based MFA in SecureChat
Tests different login scenarios and verifies security level transitions
"""
import os
import sys
import argparse
from datetime import datetime, timedelta
from flask import Flask, session

# Add app directory to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import create_app, db
from app.models.models import User, FaceVerificationLog
from app.security.security_ai import (
    calculate_security_level, 
    get_risk_details, 
    SECURITY_LEVEL_LOW, 
    SECURITY_LEVEL_MEDIUM,
    SECURITY_LEVEL_HIGH
)
from werkzeug.security import generate_password_hash

def setup_user(app, username='testuser', password='Password123!'):
    """Set up a test user"""
    with app.app_context():
        # Check if user exists
        user = User.query.filter_by(username=username).first()
        if not user:
            print(f"Creating test user: {username}")
            user = User(
                username=username,
                password_hash=generate_password_hash(password)
            )
            db.session.add(user)
            db.session.commit()
        
        return user

def clear_face_logs(app, user_id):
    """Clear face verification logs for a user"""
    with app.app_context():
        FaceVerificationLog.query.filter_by(user_id=user_id).delete()
        db.session.commit()

def create_face_logs(app, user_id, count=3, success=False):
    """Create face verification logs for testing"""
    with app.app_context():
        for i in range(count):
            log = FaceVerificationLog(
                user_id=user_id,
                timestamp=datetime.utcnow() - timedelta(minutes=i),
                success=success
            )
            db.session.add(log)
        db.session.commit()

def test_security_level_transitions(app):
    """Test different security level transitions"""
    with app.app_context():
        user = setup_user(app)
        
        # Initial state - no logs, should be low security
        level = calculate_security_level(user.id)
        assert level == SECURITY_LEVEL_LOW, f"Expected {SECURITY_LEVEL_LOW}, got {level}"
        
        # Create successful face logs, security level should remain low
        create_face_logs(app, user.id, success=True)
        level = calculate_security_level(user.id)
        assert level == SECURITY_LEVEL_LOW, f"Expected {SECURITY_LEVEL_LOW}, got {level}"
        
        # Create a failed face log, security level should transition to medium
        clear_face_logs(app, user.id)
        create_face_logs(app, user.id, count=1, success=False)
        level = calculate_security_level(user.id)
        assert level == SECURITY_LEVEL_MEDIUM, f"Expected {SECURITY_LEVEL_MEDIUM}, got {level}"
        
        # Add more failed logs, security level should transition to high
        create_face_logs(app, user.id, count=2, success=False)
        level = calculate_security_level(user.id)
        assert level == SECURITY_LEVEL_HIGH, f"Expected {SECURITY_LEVEL_HIGH}, got {level}"
        
        print("Security level transition tests passed.")

def main():
    parser = argparse.ArgumentParser(description="Run end-to-end tests for AI-based MFA in SecureChat.")
    parser.add_argument('--app', type=str, help="The Flask app instance")
    args = parser.parse_args()
    
    app = create_app(args.app)
    
    with app.app_context():
        test_security_level_transitions(app)

if __name__ == "__main__":
    main()
