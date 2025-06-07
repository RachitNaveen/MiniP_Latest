#!/usr/bin/env python3
"""
Automated tests for Multi-Factor Authentication (MFA) in SecureChatApp.

This script tests the authentication validations without requiring user interaction.
"""

import unittest
import os
import sys
import requests
import json
from time import sleep
from flask import Flask, session
from unittest.mock import patch, MagicMock
import tempfile

# Add the project root directory to the path so we can import modules
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import create_app, db
from app.models.models import User
from app.security.security_ai import SECURITY_LEVEL_LOW, SECURITY_LEVEL_MEDIUM, SECURITY_LEVEL_HIGH

class MFATestCase(unittest.TestCase):
    """Test case for Multi-Factor Authentication."""

    def setUp(self):
        """Set up test environment."""
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()
        
        # Create test database
        db.create_all()
        
        # Create a test user
        test_user = User(username='testuser')
        test_user.set_password('testpassword')
        db.session.add(test_user)
        db.session.commit()

    def tearDown(self):
        """Tear down test environment."""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_password_required_at_low_security(self):
        """Test that password is always required even at low security level."""
        # Set the security level to low
        with self.client.session_transaction() as session:
            session['manual_security_level'] = SECURITY_LEVEL_LOW
        
        # Try to login without a password
        response = self.client.post('/login', data={
            'username': 'testuser',
            'password': '',  # Empty password
            'submit': 'Login'
        }, follow_redirects=True)
        
        # Check that the login failed
        self.assertIn(b'Username and password are required', response.data)
        
    def test_captcha_required_at_medium_security(self):
        """Test that CAPTCHA is required at medium security level."""
        # Mock the CAPTCHA validation to simulate a failed validation
        with patch('flask_wtf.recaptcha.widgets.RecaptchaWidget.__call__', return_value=''):
            with patch('flask_wtf.recaptcha.validators.Recaptcha.validate', return_value=False):
                
                # Set the security level to medium
                with self.client.session_transaction() as session:
                    session['manual_security_level'] = SECURITY_LEVEL_MEDIUM
                
                # Try to login without completing CAPTCHA
                response = self.client.post('/login', data={
                    'username': 'testuser',
                    'password': 'testpassword',
                    'submit': 'Login'
                }, follow_redirects=True)
                
                # Check that login failed due to CAPTCHA
                self.assertIn(b'CAPTCHA validation failed', response.data)
    
    def test_security_level_endpoint(self):
        """Test the security level setting endpoint."""
        # Test setting security level to medium
        response = self.client.post('/set_security_level_login', 
                                   json={'level': 'medium'},
                                   content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['level'], 'medium')
        self.assertEqual(data['levelName'], 'Medium')
        
        # Check if the session values are updated correctly
        with self.client.session_transaction() as session:
            self.assertEqual(session['manual_security_level'], SECURITY_LEVEL_MEDIUM)
            self.assertTrue(session['captcha_enabled'])
            self.assertFalse(session['face_verification_enabled'])
            self.assertTrue(session['password_required'])

if __name__ == '__main__':
    unittest.main()
