#!/usr/bin/env python3
"""
Create a test user for the SecureChat application
"""
import os
import sys

# Add the project directory to the path
sys.path.insert(0, os.path.abspath('.'))

from app import create_app, db
from app.models.models import User
from werkzeug.security import generate_password_hash

def create_test_user(username='testuser', password='Password123!'):
    """Create a test user if it doesn't exist"""
    app = create_app()
    
    with app.app_context():
        user = User.query.filter_by(username=username).first()
        
        if not user:
            print(f"Creating test user: {username}")
            user = User(
                username=username,
                password_hash=generate_password_hash(password, method='sha256')
            )
            db.session.add(user)
            db.session.commit()
            print(f"Test user created: {username}")
        else:
            print(f"Test user already exists: {username}")

if __name__ == '__main__':
    create_test_user()
