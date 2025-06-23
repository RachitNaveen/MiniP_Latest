#!/usr/bin/env python3
"""
Test the ML integration in the security module
"""
import os
import sys
import argparse
from flask import request

# Add the project directory to the path
sys.path.insert(0, os.path.abspath('.'))

from app import create_app
from app.models.models import User
from app.security.security_ai import calculate_security_level, get_risk_details

def test_with_user(username='testuser'):
    """
    Test ML integration with a real user
    
    Args:
        username (str): Username to test with
    """
    print(f"Testing ML integration with user: {username}")
    print("=" * 80)
    
    app = create_app()
    with app.app_context():
        user = User.query.filter_by(username=username).first()
        
        if not user:
            print(f"User {username} not found")
            return
        
        print(f"User found: {username}")
        
        # ML first 
        print("\n*** Using ML-based approach ***")
        # Set security mode to ML
        instance_dir = os.path.join(os.path.dirname(__file__), 'instance')
        mode_file = os.path.join(instance_dir, 'security_mode.txt')
        with open(mode_file, 'w') as f:
            f.write('ml')
        
        # Get security level and details
        security_level = calculate_security_level(username)
        risk_details = get_risk_details(username)
        
        # Print results
        print(f"Security level: {risk_details['security_level']} ({security_level})")
        print(f"Risk score: {risk_details['risk_score']:.4f}")
        if 'ml_assessment' in risk_details and risk_details['ml_assessment']:
            print("Using ML-based assessment")
            if 'ml_simplified' in risk_details and risk_details['ml_simplified']:
                print("Using simplified ML model")
            if 'ml_confidence' in risk_details:
                print(f"ML confidence: {risk_details['ml_confidence']:.2f}%")
            if 'ml_probabilities' in risk_details:
                print("ML probabilities:")
                for level, prob in risk_details['ml_probabilities'].items():
                    print(f"  {level}: {prob:.2f}%")
        print("\nRisk factors:")
        for factor, details in risk_details['risk_factors'].items():
            if isinstance(details, dict) and 'score' in details:
                print(f"  {factor}: {details['score']:.2f} - {details.get('description', '')}")
        
        # Rule-based next
        print("\n*** Using rule-based approach ***")
        # Set security mode to rule-based
        with open(mode_file, 'w') as f:
            f.write('rule')
        
        # Also set environment variable to force rule-based
        request.environ['USE_RULE_BASED_SECURITY'] = True
        
        # Get security level and details
        security_level = calculate_security_level(username)
        risk_details = get_risk_details(username)
        
        # Print results
        print(f"Security level: {risk_details['security_level']} ({security_level})")
        print(f"Risk score: {risk_details['risk_score']:.4f}")
        print("\nRisk factors:")
        for factor, details in risk_details['risk_factors'].items():
            if isinstance(details, dict) and 'score' in details:
                print(f"  {factor}: {details['score']:.2f} - {details.get('description', '')}")

def main():
    """Parse arguments and run test"""
    parser = argparse.ArgumentParser(description='Test ML integration in security module')
    parser.add_argument('--username', default='testuser', help='Username to test with')
    
    args = parser.parse_args()
    
    test_with_user(args.username)

if __name__ == '__main__':
    main()
