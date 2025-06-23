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
