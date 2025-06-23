#!/usr/bin/env python3
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
        username (str): Username to compare security levels for. If None, compares for all users.
        n_samples (int): Number of samples to use for comparison.
        random_samples (bool): Whether to use random samples or not.

    Returns:
        pd.DataFrame: DataFrame containing the comparison results.
    """
    # If username is not provided, use all users
    if username is None:
        users = User.query.all()
    else:
        users = [User.query.filter_by(username=username).first()]

    results = []
    for user in users:
        if user is None:
            continue

        # Get rule-based security level
        rule_based_level = calculate_security_level(user.id)

        # Get ML-based security level
        ml_based_level = get_ml_security_level(user.id)

        # Append the results
        results.append({
            'username': user.username,
            'rule_based_level': rule_based_level,
            'ml_based_level': ml_based_level
        })

    # Create a DataFrame from the results
    df_results = pd.DataFrame(results)

    return df_results

@app.route('/compare_security_levels', methods=['GET'])
def compare_security_levels_endpoint():
    """
    API endpoint to compare security levels
    """
    # Parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--username', type=str, help='Username to compare security levels for')
    parser.add_argument('--n_samples', type=int, default=10, help='Number of samples to use for comparison')
    parser.add_argument('--random_samples', type=bool, default=True, help='Whether to use random samples or not')
    args = parser.parse_args()

    # Compare security levels
    df_results = compare_security_levels(args.username, args.n_samples, args.random_samples)

    # Return the results as JSON
    return df_results.to_json(orient='records')

def test_compare_security_levels():
    """
    Test the compare_security_levels function
    """
    # Create a test user
    user = User(username='testuser', password='testpass')
    user.set_password('testpass')
    db.session.add(user)
    db.session.commit()

    # Compare security levels for the test user
    df_results = compare_security_levels(username='testuser')

    # Check that the results DataFrame is not empty
    assert not df_results.empty

    # Check that the security levels are calculated
    assert 'rule_based_level' in df_results.columns
    assert 'ml_based_level' in df_results.columns

    # Clean up
    db.session.delete(user)
    db.session.commit()

if __name__ == '__main__':
    # Run the Flask app
    app.run(debug=True)
