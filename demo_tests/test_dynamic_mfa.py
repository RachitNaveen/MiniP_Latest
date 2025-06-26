#!/usr/bin/env python3
"""
Demonstration test file for dynamic MFA requirements based on AI risk assessment.
"""
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
from app import create_app
from app.models.models import User
from app.security.security_ai import calculate_security_level, get_risk_details

def test_dynamic_mfa():
    """Test dynamic MFA requirements based on AI risk assessment"""
    app = create_app()
    with app.app_context():
        username = 'testuser'
        user = User.query.filter_by(username=username).first()
        
        if not user:
            print(f"User {username} not found")
            return
        
        print(f"Testing dynamic MFA requirements for user: {username}")
        security_level = calculate_security_level(username)
        risk_details = get_risk_details(username)
        
        print(f"Security level: {security_level}")
        print(f"Risk details: {risk_details}")
        
        if security_level == 'high':
            print("High security level detected. Enforcing face verification.")
        elif security_level == 'medium':
            print("Medium security level detected. Enforcing CAPTCHA.")
        else:
            print("Low security level detected. Standard login.")
