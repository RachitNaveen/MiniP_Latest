#!/usr/bin/env python3
"""
Test script to compare ML-based and rule-based security level determination
"""
import os
import sys
import argparse
import json
from flask import Flask, request, session
from flask.ctx import AppContext

# Add the parent directory to the path
sys.path.insert(0, os.path.abspath('.'))

# Try importing pandas and numpy, but we can work without them
try:
    import pandas as pd
    import numpy as np
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    print("Warning: pandas or numpy not available, limited functionality") python3
"""
Test script to compare ML-based and rule-based security level determination
"""
import os
import sys
import argparse
import pandas as pd
import numpy as np
from flask import Flask, request, session
from flask.ctx import AppContext

# Add the parent directory to the path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Create a simple Flask app for testing
app = Flask(__name__)
app.config['SECRET_KEY'] = 'test-key'

# Import security modules
from app import create_app
from app.models.models import User
from app.security.security_ai import calculate_security_level, get_risk_details
from ml_mfa.ml_security import get_ml_security_level, get_ml_risk_details

def compare_security_levels(username=None, n_samples=10, random_samples=True):
    """
    Compare ML-based and rule-based security level determination
    
    Args:
        username (str): Username to test with (optional)
        n_samples (int): Number of random samples to test
        random_samples (bool): Whether to test with random samples
    """
    print("Comparing ML-based and rule-based security level determination")
    print("=" * 80)
    
    # Create app context for testing
    flask_app = create_app()
    with flask_app.app_context():
        # If username provided, test with real user
        if username:
            user = User.query.filter_by(username=username).first()
            if user:
                print(f"Testing with user: {username}")
                
                # Get rule-based security level
                request.environ['USE_RULE_BASED_SECURITY'] = True
                rule_security_level = calculate_security_level(username)
                rule_risk_details = get_risk_details(username)
                
                # Get ML-based security level
                request.environ.pop('USE_RULE_BASED_SECURITY', None)
                ml_security_level = calculate_security_level(username)
                ml_risk_details = get_risk_details(username)
                
                # Display results
                print("\nRule-based assessment:")
                print(f"Security level: {rule_risk_details['security_level']} ({rule_security_level})")
                print(f"Risk score: {rule_risk_details['risk_score']:.4f}")
                print("Risk factors:")
                for factor, details in rule_risk_details['risk_factors'].items():
                    print(f"  {factor}: {details['score']:.2f} - {details.get('description', '')}")
                
                print("\nML-based assessment:")
                print(f"Security level: {ml_risk_details['security_level']} ({ml_security_level})")
                print(f"Risk score: {ml_risk_details['risk_score']:.4f}")
                if 'ml_confidence' in ml_risk_details:
                    print(f"ML confidence: {ml_risk_details['ml_confidence']:.2f}%")
                print("Risk factors:")
                for factor, details in ml_risk_details['risk_factors'].items():
                    print(f"  {factor}: {details['score']:.2f} - {details.get('description', '')}")
                
                # Show ML probabilities if available
                if 'ml_probabilities' in ml_risk_details:
                    print("\nML classification probabilities:")
                    for level, prob in ml_risk_details['ml_probabilities'].items():
                        print(f"  {level}: {prob:.2f}%")
            else:
                print(f"User {username} not found")
        
        # Test with random samples
        if random_samples:
            if not PANDAS_AVAILABLE:
                print("\nCannot test with random samples: pandas not available")
                print("Generating random test cases instead...")
                
                # Generate a few random test cases
                import random
                
                # Compare results
                results = {'match': 0, 'mismatch': 0}
                
                print("\n{:<60} | {:<15} | {:<15}".format("Features", "Rule-Based", "ML-Based"))
                print("-" * 95)
                
                for _ in range(n_samples):
                    # Generate random features
                    features = {
                        'failed_attempts': random.uniform(0, 1),
                        'location_risk': random.choice([0.1, 0.5, 0.9]),
                        'time_risk': random.choice([0.2, 0.5, 0.8]),
                        'breach_risk': random.choice([0.2, 0.5, 0.8]),
                        'device_risk': random.choice([0.3, 0.6, 0.7])
                    }
            else:
                # Try to load synthetic data
                try:
                    df = pd.read_csv('synthetic_login_data.csv')
                    print(f"\nTesting with {min(n_samples, len(df))} random samples from synthetic data")
                    
                    # Select random samples
                    samples = df.sample(min(n_samples, len(df)))
                    
                    # Compare results
                    results = {'match': 0, 'mismatch': 0}
                    
                    print("\n{:<60} | {:<15} | {:<15}".format("Features", "Rule-Based", "ML-Based"))
                    print("-" * 95)
                    
                    for _, row in samples.iterrows():
                        # Extract features
                        features = {
                            'failed_attempts': row['failed_attempts'],
                            'location_risk': row['location_risk'],
                            'time_risk': row['time_risk'],
                            'breach_risk': row['breach_risk'],
                            'device_risk': row['device_risk']
                        }
                    
                    # Calculate rule-based security level
                    risk_score = sum(value * weight for value, weight in zip(
                        features.values(), 
                        [0.3, 0.2, 0.15, 0.2, 0.15]
                    ))
                    
                    if risk_score < 0.3:
                        rule_level = 'low'
                    elif risk_score < 0.7:
                        rule_level = 'medium'
                    else:
                        rule_level = 'high'
                    
                    # Get ML prediction
                    from ml_mfa.ml_security import MLSecurityClassifier
                    classifier = MLSecurityClassifier()
                    ml_level = classifier.predict(features)
                    
                    # Update match/mismatch count
                    if rule_level == ml_level:
                        results['match'] += 1
                    else:
                        results['mismatch'] += 1
                    
                    # Format feature string
                    features_str = ", ".join([f"{k[:5]}:{v:.2f}" for k, v in features.items()])
                    
                    # Print comparison
                    print("{:<60} | {:<15} | {:<15}".format(
                        features_str, rule_level, ml_level
                    ))
                
                # Print summary
                print("\nSummary:")
                print(f"Total samples: {len(samples)}")
                print(f"Matches: {results['match']} ({results['match']/len(samples)*100:.1f}%)")
                print(f"Mismatches: {results['mismatch']} ({results['mismatch']/len(samples)*100:.1f}%)")
                
            except Exception as e:
                print(f"Error testing with random samples: {str(e)}")

def main():
    """Main function to run the comparison"""
    parser = argparse.ArgumentParser(description='Compare ML-based and rule-based security level determination')
    parser.add_argument('--username', help='Username to test with')
    parser.add_argument('--samples', type=int, default=10, help='Number of random samples to test')
    parser.add_argument('--no-random', action='store_true', help='Skip testing with random samples')
    
    args = parser.parse_args()
    
    compare_security_levels(
        username=args.username,
        n_samples=args.samples,
        random_samples=not args.no_random
    )

if __name__ == '__main__':
    main()
