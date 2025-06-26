#!/usr/bin/env python3
"""
Test script to verify that the AI model produces variable risk scores.
"""
import os
import random
import time
import sys
from flask import Flask, session, request

# Add the parent directory to the path
sys.path.insert(0, os.path.abspath('.'))

def test_variable_risk_scores():
    """Test that risk calculations produce variable results"""
    print("Testing risk calculation variability...")
    
    # Create a test Flask app for the request context
    from app import create_app
    app = create_app()
    
    # Ensure ML mode is set
    instance_dir = os.path.join(os.path.dirname(__file__), 'instance')
    security_mode_file = os.path.join(instance_dir, 'security_mode.txt')
    
    with open(security_mode_file, 'w') as f:
        f.write('ml')
    
    print("Security mode set to ML")
    
    # Create a list to store risk scores
    risk_scores = []
    
    with app.test_request_context():
        # Import here to avoid circular imports
        from app.security.security_ai import (
            calculate_security_level, 
            get_risk_details,
            get_location_risk,
            get_time_risk,
            get_device_risk
        )
        from app.models.models import User
        
        # Use a real user if available, otherwise mock one
        user = User.query.filter_by(username='testuser').first()
        if not user:
            user = User.query.first()  # Try to get any user
        
        if user:
            print(f"Testing with user: {user.username}")
        else:
            print("No users found in database, creating a mock user")
            # Create a mock user object
            user = type('MockUser', (), {
                'id': 1, 
                'username': 'testuser', 
                'last_login': None
            })
        
        # Test get_location_risk for variability
        print("\nTesting location risk variability:")
        location_risks = []
        for i in range(10):
            # Change the session to simulate different requests
            if i % 2 == 0:
                session.clear()
            risk = get_location_risk()
            location_risks.append(risk)
            print(f"  Location risk #{i+1}: {risk:.4f}")
            time.sleep(0.1)  # Small delay to ensure different random factors
        
        location_risk_variation = max(location_risks) - min(location_risks)
        print(f"  Location risk variation: {location_risk_variation:.4f}")
        print(f"  Standard deviation: {calculate_std_dev(location_risks):.4f}")
        
        # Test full risk assessment
        print("\nTesting overall risk assessment:")
        security_levels = []
        for i in range(10):
            # Simulate different request environments
            session.clear()
            request.environ['HTTP_USER_AGENT'] = random.choice([
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Safari/605.1.15',
                'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            ])
            
            security_level = calculate_security_level(user.username)
            security_levels.append(security_level)
            
            risk_details = get_risk_details(user.username)
            risk_score = risk_details['risk_score']
            risk_scores.append(risk_score)
            
            print(f"  Run #{i+1}: Security Level: {risk_details['security_level']} ({security_level}), Risk Score: {risk_score:.4f}")
            print(f"    Risk factors: ", end="")
            
            # Display risk factors
            for factor_name, factor_data in risk_details['risk_factors'].items():
                if isinstance(factor_data, dict) and 'score' in factor_data:
                    print(f"{factor_name}={factor_data['score']:.2f} ", end="")
            print()
            
            time.sleep(0.1)  # Small delay
    
    # Calculate variability metrics for the risk scores
    if risk_scores:
        risk_score_variation = max(risk_scores) - min(risk_scores)
        std_dev = calculate_std_dev(risk_scores)
        print("\nRisk Score Analysis:")
        print(f"  Min: {min(risk_scores):.4f}")
        print(f"  Max: {max(risk_scores):.4f}")
        print(f"  Range: {risk_score_variation:.4f}")
        print(f"  Standard Deviation: {std_dev:.4f}")
        
        if std_dev > 0.05:
            print("\n✅ PASS: Risk scores show significant variation (std dev > 0.05)")
        elif risk_score_variation > 0.1:
            print("\n✅ PASS: Risk scores show good variation (range > 0.1)")
        elif risk_score_variation > 0:
            print("\n⚠️ WARNING: Risk scores show minimal variation")
        else:
            print("\n❌ FAIL: Risk scores show no variation at all")
    
    # Check if security levels vary
    if security_levels and len(set(security_levels)) > 1:
        print("✅ PASS: Security levels vary appropriately")
    else:
        print("⚠️ WARNING: Security levels do not vary across tests")

def calculate_std_dev(values):
    """Calculate the standard deviation of a list of values"""
    if not values:
        return 0
    mean = sum(values) / len(values)
    variance = sum((x - mean) ** 2 for x in values) / len(values)
    return variance ** 0.5

if __name__ == '__main__':
    test_variable_risk_scores()
