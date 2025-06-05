#!/usr/bin/env python3
"""
Test runner for SecureChat security level transitions
This script runs the application and tests security level transitions.
"""
import os
import sys
from flask import url_for
from app import create_app, db
from app.models.models import User, FaceVerificationLog
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta

app = create_app()

def setup_test_user():
    """Create a test user for demonstrating security levels"""
    with app.app_context():
        # Check if test user exists
        test_user = User.query.filter_by(username='testuser').first()
        if not test_user:
            test_user = User(
                username='testuser',
                password_hash=generate_password_hash('Password123!'),
                last_login=datetime.utcnow() - timedelta(days=1)
            )
            db.session.add(test_user)
            db.session.commit()
            print("Test user created: testuser / Password123!")
        else:
            print("Test user already exists")
        
        return test_user

def print_test_instructions():
    """Print instructions for testing security level transitions"""
    print("\n========== SECURITY LEVEL TESTING INSTRUCTIONS ==========")
    print("1. Run the application with: python run.py")
    print("2. Open your browser and go to: http://localhost:5000/login")
    print("3. Log in with: testuser / Password123!")
    print()
    print("To test different security levels:")
    print("- Low Risk: Use the demo_security_ai.py script with 'low' scenario")
    print("- Medium Risk: Use the demo_security_ai.py script with 'medium' scenario")
    print("- High Risk: Use the demo_security_ai.py script with 'high' scenario")
    print()
    print("Run: python demo_security_ai.py testuser")
    print("This will show detailed risk assessments for each scenario")
    print()
    print("To simulate different security levels:")
    print("- Low: First login, normal conditions")
    print("- Medium: Few failed login attempts (run the script)")
    print("- High: Multiple failed login attempts + unusual location")
    print("======================================================\n")

if __name__ == '__main__':
    with app.app_context():
        # Setup test user
        test_user = setup_test_user()
        
        # Print testing instructions
        print_test_instructions()
        
        # Run the app
        app.run(debug=True)
