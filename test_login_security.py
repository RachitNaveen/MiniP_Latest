#!/usr/bin/env python3
"""
Test runner for login security features.
This script creates a test user and runs the Flask application
so you can manually test the different security levels.
"""

import sys
import os
from werkzeug.security import generate_password_hash
from app import create_app, db
from app.models.models import User

def setup_test_user():
    """Create test users for each security level"""
    # Clear any existing test users
    User.query.filter(User.username.in_(['testlow', 'testmedium', 'testhigh'])).delete(synchronize_session=False)
    db.session.commit()
    
    # Create test users
    users = [
        User(
            username='testlow',
            password_hash=generate_password_hash('lowpass123', method='sha256'),
            email='testlow@example.com'
        ),
        User(
            username='testmedium',
            password_hash=generate_password_hash('mediumpass123', method='sha256'),
            email='testmedium@example.com'
        ),
        User(
            username='testhigh',
            password_hash=generate_password_hash('highpass123', method='sha256'),
            email='testhigh@example.com'
        )
    ]
    
    db.session.add_all(users)
    db.session.commit()
    
    print("Test users created successfully:")
    print("  - Username: testlow, Password: lowpass123 (for Low security)")
    print("  - Username: testmedium, Password: mediumpass123 (for Medium security)")
    print("  - Username: testhigh, Password: highpass123 (for High security)")

def main():
    """Create test users and run the app"""
    app = create_app()
    
    with app.app_context():
        setup_test_user()
    
    print("\nStarting Flask app for testing login security features...")
    print("Please visit: http://localhost:5000/auth/login")
    print("1. Select a security level (Low, Medium, or High)")
    print("2. Use the appropriate test credentials to test the login flow")
    
    app.run(debug=True, use_reloader=False)

if __name__ == '__main__':
    main()
