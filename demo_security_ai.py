#!/usr/bin/env python3
"""
Demo script for AI MFA Risk Assessment in SecureChat
This script demonstrates how different risk factors affect security level determination.
"""
import sys
import os
from datetime import datetime, timedelta
from flask import Flask, session, request
import json

# Add the parent directory to the Python path for imports
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import db
from app.models.models import User, FaceVerificationLog
from app.security.security_ai import (
    calculate_risk_score,
    get_risk_details,
    SECURITY_LEVEL_LOW,
    SECURITY_LEVEL_MEDIUM,
    SECURITY_LEVEL_HIGH
)

def create_demo_app():
    """Create a minimal Flask app for demo purposes"""
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.abspath(os.path.join(os.path.dirname(__file__), "instance", "db.db"))}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'demo-key'

    with app.app_context():
        db.init_app(app)
        return app

def print_risk_assessment(username, scenario_name):
    """Print risk assessment details for a user"""
    user = User.query.filter_by(username=username).first()
    
    if not user:
        print(f"User '{username}' not found")
        return
    
    risk_details = get_risk_details(username)
    
    print(f"\n--- SCENARIO: {scenario_name} ---")
    print(f"Security Level: {risk_details['security_level']}")
    print(f"Risk Score: {risk_details['risk_score']:.2f}")
    print(f"Required Factors: {', '.join(risk_details['required_factors'])}")
    
    print("\nRisk Factor Breakdown:")
    for factor_name, factor_data in risk_details['risk_factors'].items():
        print(f"  • {factor_name.replace('_', ' ').title()}: {factor_data['score']:.2f}")
        print(f"    {factor_data['description']}")
    
    print("\n")

def setup_scenarios(username):
    """Setup different risk scenarios for a user"""
    app = create_demo_app()

    with app.app_context():
        user = User.query.filter_by(username=username).first()

        if not user:
            print(f"User '{username}' not found. Please create this user first.")
            return

        # Clear any existing logs
        FaceVerificationLog.query.filter_by(user_id=user.id).delete()
        db.session.commit()

        # Scenario 1: Low Risk - Regular user with recent login
        user.last_login = datetime.utcnow() - timedelta(hours=2)
        db.session.commit()

        with app.test_request_context('/'):  # Ensure session context
            session['known_ip'] = request.remote_addr
            print_risk_assessment(username, "Low Risk - Regular User")

        # Scenario 2: Medium Risk - Few failed logins and older account activity
        for _ in range(2):
            log = FaceVerificationLog(
                user_id=user.id, 
                success=False,
                timestamp=datetime.utcnow() - timedelta(hours=5)
            )
            db.session.add(log)

        user.last_login = datetime.utcnow() - timedelta(days=10)
        db.session.commit()

        with app.test_request_context('/'):  # Ensure session context
            session['known_ip'] = request.remote_addr
            print_risk_assessment(username, "Medium Risk - Some Failed Logins")

        # Scenario 3: High Risk - Many failed logins, old account, unusual time
        FaceVerificationLog.query.filter_by(user_id=user.id).delete()

        for _ in range(4):
            log = FaceVerificationLog(
                user_id=user.id, 
                success=False,
                timestamp=datetime.utcnow() - timedelta(hours=2)
            )
            db.session.add(log)

        user.last_login = datetime.utcnow() - timedelta(days=40)
        db.session.commit()

        with app.test_request_context('/'):  # Ensure session context
            session['known_ip'] = '1.2.3.4'
            print_risk_assessment(username, "High Risk - Multiple Risk Factors")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python demo_security_ai.py <username>")
        sys.exit(1)
    
    username = sys.argv[1]
    setup_scenarios(username)
