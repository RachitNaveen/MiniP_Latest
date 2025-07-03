#!/usr/bin/env python3
"""
Demonstration test file for risk escalation after failed login attempts.
"""
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
from app import create_app
from app.models.models import User
from app.security.security_ai import calculate_security_level

def test_risk_escalation():
    """Test risk escalation after failed login attempts"""
    app = create_app()
    with app.app_context():
        username = 'testuser'
        user = User.query.filter_by(username=username).first()
        
        if not user:
            print(f"User {username} not found")
            return
        
        print(f"Simulating failed login attempts for user: {username}")
        for attempt in range(3):
            print(f"Failed attempt {attempt + 1}")
            security_level = calculate_security_level(username)
            print(f"Updated security level: {security_level}")
