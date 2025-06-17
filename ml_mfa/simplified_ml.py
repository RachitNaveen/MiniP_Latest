#!/usr/bin/env python3
"""
Simplified ML-based security level determination
This version doesn't require external ML libraries
"""
import os
import random

# Security levels
SECURITY_LEVEL_LOW = 1      # Password only
SECURITY_LEVEL_MEDIUM = 2   # Password + CAPTCHA
SECURITY_LEVEL_HIGH = 3     # Password + CAPTCHA + Face Verification

class SimplifiedMLClassifier:
    """A simplified ML classifier that mimics the behavior of the real ML model"""
    
    def __init__(self):
        """Initialize the classifier"""
        # The model simply applies modified weights to the rule-based approach
        self.weights = {
            'failed_attempts': 0.35,  # Higher weight than rule-based
            'location_risk': 0.25,    # Higher weight than rule-based
            'time_risk': 0.10,        # Lower weight than rule-based
            'breach_risk': 0.20,      # Same weight as rule-based
            'device_risk': 0.10       # Lower weight than rule-based
        }
        # Slightly different thresholds
        self.thresholds = {
            'low': 0.32,   # Slightly higher than rule-based (0.3)
            'high': 0.68   # Slightly lower than rule-based (0.7)
        }
    
    def predict(self, features):
        """
        Predict security level based on features
        
        Args:
            features (dict): Dict with risk features
            
        Returns:
            str: Security level ('low', 'medium', or 'high')
        """
        # Calculate weighted sum
        score = (
            features.get('failed_attempts', 0) * self.weights['failed_attempts'] +
            features.get('location_risk', 0) * self.weights['location_risk'] +
            features.get('time_risk', 0) * self.weights['time_risk'] +
            features.get('breach_risk', 0) * self.weights['breach_risk'] +
            features.get('device_risk', 0) * self.weights['device_risk']
        )
        
        # Apply thresholds
        if score < self.thresholds['low']:
            return 'low'
        elif score < self.thresholds['high']:
            return 'medium'
        else:
            return 'high'
    
    def predict_proba(self, features):
        """
        Get probabilities for each security level
        
        Args:
            features (dict): Dict with risk features
            
        Returns:
            dict: Probabilities for each security level
        """
        # Calculate score
        score = (
            features.get('failed_attempts', 0) * self.weights['failed_attempts'] +
            features.get('location_risk', 0) * self.weights['location_risk'] +
            features.get('time_risk', 0) * self.weights['time_risk'] +
            features.get('breach_risk', 0) * self.weights['breach_risk'] +
            features.get('device_risk', 0) * self.weights['device_risk']
        )
        
        # Convert score to probabilities (simplified approach)
        if score < self.thresholds['low']:
            # Low security level
            low_prob = 0.9 - (score / self.thresholds['low']) * 0.2
            medium_prob = 1.0 - low_prob - 0.01
            high_prob = 0.01
        elif score < self.thresholds['high']:
            # Medium security level
            medium_prob = 0.9 - ((score - self.thresholds['low']) / 
                               (self.thresholds['high'] - self.thresholds['low'])) * 0.2
            low_prob = (1.0 - medium_prob) * 0.3
            high_prob = (1.0 - medium_prob) * 0.7
        else:
            # High security level
            high_prob = 0.9 - ((1.0 - score) / (1.0 - self.thresholds['high'])) * 0.2
            medium_prob = 1.0 - high_prob - 0.01
            low_prob = 0.01
        
        return {
            'low': max(0, min(1, low_prob)),
            'medium': max(0, min(1, medium_prob)),
            'high': max(0, min(1, high_prob))
        }

def get_simplified_security_level(features):
    """
    Calculate security level using the simplified ML model
    
    Args:
        features (dict): Dict with risk features
        
    Returns:
        int: Security level (1=Low, 2=Medium, 3=High)
    """
    classifier = SimplifiedMLClassifier()
    prediction = classifier.predict(features)
    
    if prediction == 'low':
        return SECURITY_LEVEL_LOW
    elif prediction == 'medium':
        return SECURITY_LEVEL_MEDIUM
    else:
        return SECURITY_LEVEL_HIGH
