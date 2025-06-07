"""Configuration settings for the SecureChatApp."""

import os
from datetime import timedelta

class Config:
    """Base configuration."""
    
    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here'
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(os.path.dirname(os.path.dirname(__file__)), 'instance/db.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Security
    SECURITY_PASSWORD_SALT = 'your-security-password-salt'
    SECURITY_REGISTERABLE = True
    SECURITY_SEND_REGISTER_EMAIL = False
    SECURITY_LOGIN_URL = '/login'
    SECURITY_REGISTER_URL = '/register'
    
    # Session
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=30)
    
    # File Upload
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'app/static/uploads')
    
    # Face Recognition
    FACE_RECOGNITION_TOLERANCE = 0.6
    FACE_RECOGNITION_MODEL = 'hog'  # or 'cnn' for GPU support
    
    # ReCAPTCHA
    RECAPTCHA_USE_SSL = True
    RECAPTCHA_PUBLIC_KEY = os.environ.get('RECAPTCHA_PUBLIC_KEY', 'your-site-key')
    RECAPTCHA_PRIVATE_KEY = os.environ.get('RECAPTCHA_PRIVATE_KEY', 'your-secret-key')
    RECAPTCHA_OPTIONS = {'theme': 'clean'}
    
    # Socket.IO
    SOCKETIO_ASYNC_MODE = 'eventlet'
    
class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    
class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    
class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    # Add production-specific settings here
