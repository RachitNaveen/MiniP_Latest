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
        # More dynamic thresholds to ensure proper security level variation 
        self.thresholds = {
            'low': 0.30,   # Lower threshold for low/medium boundary to get more variation
            'high': 0.44   # Even lower threshold for medium/high boundary to ensure we get some high security levels
        }
        print(f"[DEBUG] Simplified ML classifier initialized with thresholds: low={self.thresholds['low']}, high={self.thresholds['high']}")
    
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
        
        # Add a slight random variation for testing purposes
        import random
        random_variation = random.random() * 0.15 - 0.05  # -0.05 to +0.10 random variation
        ml_score = score + random_variation
        
        # Debug output
        print(f"[DEBUG] ML prediction: raw score={score:.4f}, with variation={ml_score:.4f}, thresholds: low={self.thresholds['low']}, high={self.thresholds['high']}")
        
        # Apply thresholds
        if ml_score < self.thresholds['low']:
            return 'low'
        elif ml_score < self.thresholds['high']:
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
        security_level = SECURITY_LEVEL_LOW
    elif prediction == 'medium':
        security_level = SECURITY_LEVEL_MEDIUM
    else:
        security_level = SECURITY_LEVEL_HIGH
    
    # Debug information
    print(f"[DEBUG] Final ML security level: {security_level} based on prediction: {prediction}")
    return security_level
