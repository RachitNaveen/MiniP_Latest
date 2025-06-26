#!/usr/bin/env python3
"""
Demonstration test file for AI-based MFA functionality.
"""
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
from app import create_app
from app.models.models import User
from app.security.security_ai import calculate_security_level, get_risk_details

def test_ai_mfa():
    """Test AI-based MFA functionality"""
    app = create_app()
    with app.app_context():
        username = 'testuser'
        user = User.query.filter_by(username=username).first()
        
        if not user:
            print(f"User {username} not found")
            return
        
        print(f"Testing AI-based MFA for user: {username}")
        security_level = calculate_security_level(username)
        risk_details = get_risk_details(username)
        
        print(f"Security level: {security_level}")
        print(f"Risk details: {risk_details}")
