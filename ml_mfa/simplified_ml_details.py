"""
ML Risk Details for Simplified Model
Provides risk details functions for the simplified ML model
"""
import os
from flask import request
from datetime import datetime

from app.models.models import User
from ml_mfa.simplified_ml import SimplifiedMLClassifier, SECURITY_LEVEL_LOW, SECURITY_LEVEL_MEDIUM, SECURITY_LEVEL_HIGH

def get_simplified_risk_details(username):
    """
    Get detailed risk assessment info using the simplified ML model
    
    Args:
        username (str): The username to assess
        
    Returns:
        dict: Dictionary containing risk assessment details
    """
    from app.security.security_ai import (
        get_failed_attempts_risk,
        get_location_risk,
        get_time_risk,
        get_previous_breaches_risk,
        get_device_risk,
        get_failed_attempts_description,
        get_location_description,
        get_time_risk_description,
        get_breach_description,
        get_device_description
    )
    
    try:
        user = User.query.filter_by(username=username).first()
        
        if not user:
            # Return default medium risk details
            return {
                'security_level': 'Medium',
                'security_level_num': SECURITY_LEVEL_MEDIUM,
                'risk_score': 0.5,
                'risk_factors': {
                    'failed_attempts': {'score': 0.0, 'description': 'Unknown user'},
                    'unusual_location': {'score': 0.5, 'description': 'New login location'},
                    'time_risk': {'score': 0.5, 'description': 'Time of login risk'},
                    'previous_breaches': {'score': 0.5, 'description': 'Unknown user history'},
                    'device_risk': {'score': 0.5, 'description': 'Device type risk'}
                },
                'required_factors': ['Password', 'CAPTCHA'],
                'ml_assessment': True,
                'ml_simplified': True
            }
        
        # Get feature values
        features = {
            'failed_attempts': get_failed_attempts_risk(user),
            'location_risk': get_location_risk(),
            'time_risk': get_time_risk(),
            'breach_risk': get_previous_breaches_risk(user),
            'device_risk': get_device_risk()
        }
        
        # Create classifier
        classifier = SimplifiedMLClassifier()
        
        # Get prediction and probabilities
        prediction = classifier.predict(features)
        probabilities = classifier.predict_proba(features)
        
        # Calculate risk score (weighted average)
        risk_score = (
            features['failed_attempts'] * 0.3 +
            features['location_risk'] * 0.2 +
            features['time_risk'] * 0.15 +
            features['breach_risk'] * 0.2 +
            features['device_risk'] * 0.15
        )
        
        # Create risk factors with descriptions
        risk_factors = {
            'failed_attempts': {
                'score': float(features['failed_attempts']),
                'description': get_failed_attempts_description(features['failed_attempts']),
                'confidence': probabilities.get('high', 0) * 100 if features['failed_attempts'] > 0.5 else 
                              probabilities.get('low', 0) * 100
            },
            'unusual_location': {
                'score': float(features['location_risk']),
                'description': get_location_description(features['location_risk']),
                'confidence': probabilities.get('high', 0) * 100 if features['location_risk'] > 0.5 else 
                              probabilities.get('low', 0) * 100
            },
            'time_risk': {
                'score': float(features['time_risk']),
                'description': get_time_risk_description(),
                'confidence': probabilities.get('high', 0) * 100 if features['time_risk'] > 0.5 else 
                              probabilities.get('low', 0) * 100
            },
            'previous_breaches': {
                'score': float(features['breach_risk']),
                'description': get_breach_description(user),
                'confidence': probabilities.get('high', 0) * 100 if features['breach_risk'] > 0.5 else 
                              probabilities.get('low', 0) * 100
            },
            'device_risk': {
                'score': float(features['device_risk']),
                'description': get_device_description(),
                'confidence': probabilities.get('high', 0) * 100 if features['device_risk'] > 0.5 else 
                              probabilities.get('low', 0) * 100
            }
        }
        
        # Map security level to required factors
        if prediction == 'low':
            security_level_num = SECURITY_LEVEL_LOW
            required_factors = ['Password']
        elif prediction == 'medium':
            security_level_num = SECURITY_LEVEL_MEDIUM
            required_factors = ['Password', 'CAPTCHA']
        else:
            security_level_num = SECURITY_LEVEL_HIGH
            required_factors = ['Password', 'CAPTCHA', 'Face Verification']
        
        # Capitalize security level for display
        display_level = prediction.capitalize()
        
        return {
            'security_level': display_level,
            'security_level_num': security_level_num,
            'risk_score': float(risk_score),
            'risk_factors': risk_factors,
            'required_factors': required_factors,
            'ml_assessment': True,
            'ml_simplified': True,
            'ml_confidence': max(probabilities.values()) * 100,
            'ml_probabilities': {k: v*100 for k, v in probabilities.items()}
        }
    
    except Exception as e:
        print(f"Error in simplified ML risk assessment: {str(e)}")
        # Return default medium security level
        return {
            'security_level': 'Medium',
            'security_level_num': SECURITY_LEVEL_MEDIUM,
            'risk_score': 0.5,
            'risk_factors': {
                'error': {'score': 0.5, 'description': 'Error in ML assessment'}
            },
            'required_factors': ['Password', 'CAPTCHA'],
            'ml_assessment': False,
            'ml_simplified': True
        }
