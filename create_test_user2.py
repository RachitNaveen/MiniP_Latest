#!/usr/bin/env python3
"""
Create a test user for the SecureChat application with SHA256 hash
"""
import os
import sys

# Add the project directory to the path
sys.path.insert(0, os.path.abspath('.'))

from app import create_app, db
from app.models.models import User
from werkzeug.security import generate_password_hash

def create_test_user(username='testuser2', password='password123'):
    """Create a test user if it doesn't exist"""
    app = create_app()
    
    with app.app_context():
        user = User.query.filter_by(username=username).first()
        
        if not user:
            print(f"Creating test user: {username}")
            user = User(
                username=username,
                password_hash=generate_password_hash(password)
            )
            db.session.add(user)
            db.session.commit()
            print(f"Test user created: {username}")
        else:
            print(f"Test user already exists: {username}")
            # Update the password hash
            user.password_hash = generate_password_hash(password)
            db.session.commit()
            print(f"Updated password hash for {username} to use sha256")

if __name__ == '__main__':
    if len(sys.argv) == 3:
        username = sys.argv[1]
        password = sys.argv[2]
        create_test_user(username, password)
    else:
        create_test_user()
