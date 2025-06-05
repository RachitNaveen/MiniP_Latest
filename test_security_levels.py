#!/usr/bin/env python3
"""
Test script for security level transitions in SecureChat app
This script tests different risk scenarios and verifies the security level determination.
"""
import sys
import os
import unittest
from datetime import datetime, timedelta
from flask import session

# Add the parent directory to the Python path for imports
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import create_app, db
from app.models.models import User, FaceVerificationLog
from app.security.security_ai import (
    calculate_security_level,
    calculate_risk_score,
    get_risk_details,
    SECURITY_LEVEL_LOW,
    SECURITY_LEVEL_MEDIUM,
    SECURITY_LEVEL_HIGH
)
from config import TestConfig

class SecurityLevelTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        
        # Create test user
        self.test_user = User(
            username='testuser',
            password_hash='hashed_password'
        )
        db.session.add(self.test_user)
        db.session.commit()
        
        # Mock the request context for the security_ai module
        self.request_context = self.app.test_request_context()
        self.request_context.push()
        
    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.request_context.pop()
        self.app_context.pop()
        
    def test_low_security_level(self):
        """Test that a user with no risk factors gets low security level"""
        # Ensure no failed verification attempts
        FaceVerificationLog.query.delete()
        
        # Update last login to recent time
        self.test_user.last_login = datetime.utcnow() - timedelta(hours=1)
        db.session.commit()
        
        # Calculate security level
        security_level = calculate_security_level(self.test_user.username)
        
        # Get detailed risk assessment
        risk_details = get_risk_details(self.test_user.username)
        
        print(f"LOW RISK TEST:")
        print(f"Security Level: {risk_details['security_level']} ({security_level})")
        print(f"Risk Score: {risk_details['risk_score']:.2f}")
        print(f"Risk Factors: {risk_details['risk_factors']}")
        
        # Assert low security level
        self.assertEqual(security_level, SECURITY_LEVEL_LOW)
        self.assertLess(risk_details['risk_score'], 0.3)
        
    def test_medium_security_level(self):
        """Test that a user with some risk factors gets medium security level"""
        # Add a few failed verification attempts
        for _ in range(2):
            log = FaceVerificationLog(
                user_id=self.test_user.id,
                success=False,
                timestamp=datetime.utcnow() - timedelta(hours=6)
            )
            db.session.add(log)
        
        # Update last login to be a week ago
        self.test_user.last_login = datetime.utcnow() - timedelta(days=8)
        db.session.commit()
        
        # Calculate security level
        security_level = calculate_security_level(self.test_user.username)
        
        # Get detailed risk assessment
        risk_details = get_risk_details(self.test_user.username)
        
        print(f"\nMEDIUM RISK TEST:")
        print(f"Security Level: {risk_details['security_level']} ({security_level})")
        print(f"Risk Score: {risk_details['risk_score']:.2f}")
        print(f"Risk Factors: {risk_details['risk_factors']}")
        
        # Assert medium security level
        self.assertEqual(security_level, SECURITY_LEVEL_MEDIUM)
        self.assertGreaterEqual(risk_details['risk_score'], 0.3)
        self.assertLess(risk_details['risk_score'], 0.7)
        
    def test_high_security_level(self):
        """Test that a user with many risk factors gets high security level"""
        # Add many failed verification attempts
        for _ in range(5):
            log = FaceVerificationLog(
                user_id=self.test_user.id,
                success=False,
                timestamp=datetime.utcnow() - timedelta(hours=2)
            )
            db.session.add(log)
        
        # Update last login to be a month ago
        self.test_user.last_login = datetime.utcnow() - timedelta(days=35)
        db.session.commit()
        
        # Mock session for location risk
        with self.app.test_client() as client:
            with client.session_transaction() as sess:
                sess['known_ip'] = '1.2.3.4'  # Different from request.remote_addr
                
            # Calculate security level
            security_level = calculate_security_level(self.test_user.username)
            
            # Get detailed risk assessment
            risk_details = get_risk_details(self.test_user.username)
            
            print(f"\nHIGH RISK TEST:")
            print(f"Security Level: {risk_details['security_level']} ({security_level})")
            print(f"Risk Score: {risk_details['risk_score']:.2f}")
            print(f"Risk Factors: {risk_details['risk_factors']}")
            
            # Assert high security level
            self.assertEqual(security_level, SECURITY_LEVEL_HIGH)
            self.assertGreaterEqual(risk_details['risk_score'], 0.7)

if __name__ == '__main__':
    unittest.main()
