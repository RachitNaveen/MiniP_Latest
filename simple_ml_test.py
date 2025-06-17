#!/usr/bin/env python3
"""
Simple test script to compare ML-based and rule-based security levels
"""
import os
import sys
import random

# Add the parent directory to the path
sys.path.insert(0, os.path.abspath('.'))

def generate_test_case():
    """Generate a random test case with security features"""
    return {
        'failed_attempts': random.choice([0.0, 0.2, 0.4, 0.6, 0.8, 1.0]),
        'location_risk': random.choice([0.1, 0.5, 0.9]),
        'time_risk': random.choice([0.2, 0.5, 0.8]),
        'breach_risk': random.choice([0.2, 0.5, 0.8]),
        'device_risk': random.choice([0.3, 0.6, 0.7])
    }

def calculate_rule_based_level(features):
    """Calculate security level using rule-based approach"""
    # Apply the same weights as in security_ai.py
    weights = [0.3, 0.2, 0.15, 0.2, 0.15]
    values = list(features.values())
    
    risk_score = sum(v * w for v, w in zip(values, weights))
    
    # Apply the same thresholds as in security_ai.py
    if risk_score < 0.3:
        return 'low', risk_score
    elif risk_score < 0.7:
        return 'medium', risk_score
    else:
        return 'high', risk_score

def main():
    """Run comparison tests"""
    print("Starting ML comparison test...")
    
    # Add ml_mfa directory to path
    ml_mfa_path = os.path.join(os.path.dirname(__file__), 'ml_mfa')
    if ml_mfa_path not in sys.path:
        sys.path.insert(0, os.path.dirname(__file__))
    
    # Try to import our simplified ML classifier
    try:
        print("Importing SimplifiedMLClassifier...")
        from ml_mfa.simplified_ml import SimplifiedMLClassifier
        ml_available = True
        print("Creating classifier instance...")
        classifier = SimplifiedMLClassifier()
        print("ML classifier created successfully")
    except Exception as e:
        ml_available = False
        print(f"Error loading simplified ML module: {e}")
        print("Running rule-based tests only")
        return
    
    # Number of tests
    n_tests = 10
    print(f"\nRunning {n_tests} test cases...")
    
    # Compare results
    results = {'match': 0, 'mismatch': 0}
    
    print("\n{:<60} | {:<15} | {:<15}".format("Features", "Rule-Based", "ML-Based"))
    print("-" * 95)
    
    for i in range(n_tests):
        # Generate test case
        features = generate_test_case()
        
        # Calculate rule-based level
        rule_level, risk_score = calculate_rule_based_level(features)
        
        # Get ML prediction
        try:
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
                features_str, f"{rule_level} ({risk_score:.2f})", ml_level
            ))
        except Exception as e:
            print("{:<60} | {:<15} | Error: {}".format(
                ", ".join([f"{k[:5]}:{v:.2f}" for k, v in features.items()]),
                f"{rule_level} ({risk_score:.2f})",
                str(e)
            ))
    
    # Print summary
    if results['match'] + results['mismatch'] > 0:
        print("\nSummary:")
        print(f"Total test cases: {results['match'] + results['mismatch']}")
        print(f"Matches: {results['match']} ({results['match']/(results['match']+results['mismatch'])*100:.1f}%)")
        print(f"Mismatches: {results['mismatch']} ({results['mismatch']/(results['match']+results['mismatch'])*100:.1f}%)")

if __name__ == '__main__':
    main()
