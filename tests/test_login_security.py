"""
Test script for validating login with different security levels in the MFA system.
"""
import os
import sys
import unittest
from flask import session
from app import create_app, db
from app.models.models import User
from app.security.security_ai import SECURITY_LEVEL_LOW, SECURITY_LEVEL_MEDIUM, SECURITY_LEVEL_HIGH
from werkzeug.security import generate_password_hash

class LoginSecurityLevelTests(unittest.TestCase):
    """Test cases for different security levels in the login process"""
    
    def setUp(self):
        """Set up test environment"""
        self.app = create_app('testing')
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for testing
        self.app.config['RECAPTCHA_ENABLED'] = False  # Disable reCAPTCHA for testing
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        
        # Create test users
        test_user = User(
            username='testuser',
            password_hash=generate_password_hash('password123', method='sha256')
        )
        
        db.session.add(test_user)
        db.session.commit()
        
    def tearDown(self):
        """Clean up after tests"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
        
    def test_low_security_login(self):
        """Test login with low security level"""
        with self.client:
            # Set security level to low
            response = self.client.post('/security/set_security_level_login', 
                                      json={'level': 'low'},
                                      follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            
            # Attempt login with just username and password
            login_response = self.client.post('/auth/login',
                                            data={
                                                'username': 'testuser',
                                                'password': 'password123'
                                            },
                                            follow_redirects=True)
            
            # Check successful login
            self.assertEqual(login_response.status_code, 200)
            
            # Check that we were redirected to the chat page
            self.assertIn(b'SecureChat', login_response.data)
            
    def test_medium_security_login(self):
        """Test login with medium security level"""
        with self.client:
            # Set security level to medium
            response = self.client.post('/security/set_security_level_login', 
                                      json={'level': 'medium'},
                                      follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            
            # Attempt login with username and password but no CAPTCHA
            # In a testing environment with RECAPTCHA_ENABLED = False, this should pass
            # In production, it would require a valid CAPTCHA response
            login_response = self.client.post('/auth/login',
                                            data={
                                                'username': 'testuser',
                                                'password': 'password123',
                                                # In testing, the reCAPTCHA field isn't actually validated
                                            },
                                            follow_redirects=True)
            
            self.assertEqual(login_response.status_code, 200)
            
            # Check that we were redirected to the chat page
            self.assertIn(b'SecureChat', login_response.data)
            
    def test_invalid_credentials(self):
        """Test login with invalid credentials at any security level"""
        with self.client:
            # Set security level to low
            self.client.post('/security/set_security_level_login', 
                           json={'level': 'low'},
                           follow_redirects=True)
            
            # Attempt login with wrong password
            login_response = self.client.post('/auth/login',
                                            data={
                                                'username': 'testuser',
                                                'password': 'wrongpassword'
                                            },
                                            follow_redirects=True)
            
            # Check for failure message
            self.assertEqual(login_response.status_code, 200)
            self.assertIn(b'Invalid username or password', login_response.data)

if __name__ == '__main__':
    unittest.main()
