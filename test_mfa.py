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
from app.models import User, FaceVerificationLog
from app.security_ai import (
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
                success=success,
                timestamp=datetime.utcnow() - timedelta(hours=i)
            )
            db.session.add(log)
        db.session.commit()

def update_last_login(app, user_id, days_ago=0):
    """Update a user's last login timestamp"""
    with app.app_context():
        user = User.query.get(user_id)
        if user:
            user.last_login = datetime.utcnow() - timedelta(days=days_ago)
            db.session.commit()

def test_security_level(app, username, scenario):
    """Test security level for a specific scenario"""
    with app.app_context():
        user = User.query.filter_by(username=username).first()
        if not user:
            print(f"User {username} not found!")
            return
        
        # Setup test case
        if scenario == "low":
            clear_face_logs(app, user.id)
            update_last_login(app, user.id, days_ago=0)
        elif scenario == "medium":
            clear_face_logs(app, user.id)
            create_face_logs(app, user.id, count=2, success=False)
            update_last_login(app, user.id, days_ago=10)
        elif scenario == "high":
            clear_face_logs(app, user.id)
            create_face_logs(app, user.id, count=5, success=False)
            update_last_login(app, user.id, days_ago=35)
        else:
            print(f"Unknown scenario: {scenario}")
            return
        
        # Test the security level
        security_level = calculate_security_level(username)
        risk_details = get_risk_details(username)
        
        print(f"\n===== SECURITY LEVEL TEST: {scenario.upper()} =====")
        print(f"Security Level: {risk_details['security_level']} ({security_level})")
        print(f"Risk Score: {risk_details['risk_score']:.2f}")
        print(f"Required Factors: {', '.join(risk_details['required_factors'])}")
        
        print("\nRisk Factor Breakdown:")
        for factor_name, factor_data in risk_details['risk_factors'].items():
            print(f"  • {factor_name.replace('_', ' ').title()}: {factor_data['score']:.2f}")
            print(f"    {factor_data['description']}")
        
        # Verify security level is correct
        expected_level = {
            "low": SECURITY_LEVEL_LOW,
            "medium": SECURITY_LEVEL_MEDIUM,
            "high": SECURITY_LEVEL_HIGH
        }.get(scenario)
        
        if security_level == expected_level:
            print(f"\n✅ Test PASSED: Security level is correctly determined as {risk_details['security_level']}")
        else:
            print(f"\n❌ Test FAILED: Expected security level {expected_level} but got {security_level}")

def main():
    """Main function to run the tests"""
    parser = argparse.ArgumentParser(description='Test security level transitions')
    parser.add_argument('scenario', choices=['low', 'medium', 'high', 'all'],
                        help='Security level scenario to test')
    parser.add_argument('--username', default='testuser',
                        help='Username to test (default: testuser)')
    
    args = parser.parse_args()
    
    # Create app
    app = create_app()
    
    # Setup user
    user = setup_user(app, args.username)
    
    # Run tests
    if args.scenario == 'all':
        for scenario in ['low', 'medium', 'high']:
            test_security_level(app, args.username, scenario)
    else:
        test_security_level(app, args.username, args.scenario)

if __name__ == '__main__':
    main()
