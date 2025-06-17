#!/usr/bin/env python3
"""
Data Collection Module for ML-based MFA
This module extracts and processes data for training a machine learning model
for security level determination.
"""
import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import argparse
from sqlalchemy import create_engine, text
import ipaddress
from tqdm import tqdm

# Add the parent directory to Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from app import create_app, db
from app.models.models import User, FaceVerificationLog
from app.security.security_ai import (
    calculate_security_level,
    calculate_risk_score,
    get_risk_details,
    get_failed_attempts_risk,
    get_location_risk,
    get_time_risk,
    get_previous_breaches_risk,
    get_device_risk,
    SECURITY_LEVEL_LOW,
    SECURITY_LEVEL_MEDIUM,
    SECURITY_LEVEL_HIGH
)

class DataCollector:
    """Class to collect and prepare data for ML training"""
    
    def __init__(self, app=None, db_path=None):
        """
        Initialize the data collector
        
        Args:
            app: Flask app instance
            db_path: Path to database file
        """
        self.app = app or create_app()
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        # If db_path provided, use it to connect directly to the database
        if db_path:
            self.engine = create_engine(f'sqlite:///{db_path}')
        else:
            self.engine = None

    def __del__(self):
        """Clean up resources"""
        if hasattr(self, 'app_context'):
            self.app_context.pop()
    
    def collect_from_logs(self, output_file='login_data.csv', sample_size=1000):
        """
        Collect real login data from logs
        
        Args:
            output_file: CSV file to save the data
            sample_size: Number of samples to collect
        
        Returns:
            DataFrame with collected data
        """
        print(f"Collecting {sample_size} samples of login data...")
        
        # Use existing database connection through SQLAlchemy
        users = User.query.all()
        data = []
        
        # Progress bar
        with tqdm(total=sample_size) as pbar:
            for user in users:
                # Skip users without login history
                if not user.last_login:
                    continue
                
                # Get all face verification logs for this user
                face_logs = FaceVerificationLog.query.filter_by(user_id=user.id).order_by(
                    FaceVerificationLog.timestamp.desc()).all()
                
                # Generate samples for this user
                for _ in range(min(sample_size // len(users), 50)):  # Limit samples per user
                    # Get risk details with the current data
                    risk_details = get_risk_details(user.username)
                    
                    # Calculate features
                    failed_attempts = get_failed_attempts_risk(user)
                    location_risk = np.random.choice([0.1, 0.5, 0.9])  # Simulate location risk
                    time_risk = get_time_risk()
                    breach_risk = get_previous_breaches_risk(user)
                    device_risk = np.random.choice([0.3, 0.6, 0.7])  # Simulate device risk
                    
                    # Calculate overall risk score
                    risk_score = risk_details['risk_score']
                    
                    # Determine security level
                    security_level = calculate_security_level(user.username)
                    
                    # Convert security level to label
                    if security_level == SECURITY_LEVEL_LOW:
                        label = 'low'
                    elif security_level == SECURITY_LEVEL_MEDIUM:
                        label = 'medium'
                    else:
                        label = 'high'
                    
                    # Save sample
                    data.append({
                        'username': user.username,
                        'failed_attempts': failed_attempts,
                        'location_risk': location_risk,
                        'time_risk': time_risk,
                        'breach_risk': breach_risk,
                        'device_risk': device_risk,
                        'risk_score': risk_score,
                        'security_level': label
                    })
                    
                    pbar.update(1)
                    
                    if len(data) >= sample_size:
                        break
                
                if len(data) >= sample_size:
                    break
        
        # Convert to DataFrame
        df = pd.DataFrame(data)
        
        # Save to CSV
        df.to_csv(output_file, index=False)
        print(f"Data saved to {output_file}")
        
        return df
    
    def generate_synthetic_data(self, output_file='synthetic_login_data.csv', n_samples=5000):
        """
        Generate synthetic data for ML training based on the rules in security_ai.py
        
        Args:
            output_file: CSV file to save the data
            n_samples: Number of samples to generate
        
        Returns:
            DataFrame with synthetic data
        """
        print(f"Generating {n_samples} samples of synthetic data...")
        
        data = []
        
        # Generate random samples
        for _ in tqdm(range(n_samples)):
            # Generate random features
            failed_attempts = np.random.choice(
                [0.0, 0.2, 0.4, 0.6, 0.8, 1.0], 
                p=[0.4, 0.2, 0.15, 0.1, 0.1, 0.05]  # More weight to lower values
            )
            
            location_risk = np.random.choice(
                [0.1, 0.5, 0.9],  # Common values from the rule-based system
                p=[0.6, 0.3, 0.1]  # Most logins from known locations
            )
            
            # Time risk based on hour distribution
            hour = np.random.randint(0, 24)
            if 9 <= hour <= 18:
                time_risk = 0.2  # Business hours
            elif 5 <= hour < 9 or 18 < hour <= 23:
                time_risk = 0.5  # Early morning or evening
            else:
                time_risk = 0.8  # Late night/early morning
            
            # Previous breach risk based on days since login
            days_since_login = np.random.choice(
                [0, 1, 3, 7, 14, 30, 45, 60],
                p=[0.2, 0.2, 0.15, 0.15, 0.1, 0.1, 0.05, 0.05]
            )
            
            if days_since_login > 30:
                breach_risk = 0.8
            elif days_since_login > 7:
                breach_risk = 0.5
            else:
                breach_risk = 0.2
            
            # Device risk
            device_risk = np.random.choice(
                [0.3, 0.6, 0.7],  # Values from get_device_risk()
                p=[0.7, 0.2, 0.1]  # Most users on common browsers
            )
            
            # Calculate risk score using the same weights as in security_ai.py
            risk_score = (
                failed_attempts * 0.3 +
                location_risk * 0.2 +
                time_risk * 0.15 +
                breach_risk * 0.2 +
                device_risk * 0.15
            )
            
            # Determine security level based on risk score thresholds
            if risk_score < 0.3:
                security_level = 'low'
            elif risk_score < 0.7:
                security_level = 'medium'
            else:
                security_level = 'high'
            
            # Save sample
            data.append({
                'failed_attempts': failed_attempts,
                'location_risk': location_risk,
                'time_risk': time_risk,
                'breach_risk': breach_risk,
                'device_risk': device_risk,
                'risk_score': risk_score,
                'security_level': security_level
            })
        
        # Convert to DataFrame
        df = pd.DataFrame(data)
        
        # Add some noise to make it more realistic (optional)
        df['failed_attempts'] = np.clip(df['failed_attempts'] + np.random.normal(0, 0.05, n_samples), 0, 1)
        df['location_risk'] = np.clip(df['location_risk'] + np.random.normal(0, 0.05, n_samples), 0, 1)
        df['time_risk'] = np.clip(df['time_risk'] + np.random.normal(0, 0.05, n_samples), 0, 1)
        df['breach_risk'] = np.clip(df['breach_risk'] + np.random.normal(0, 0.05, n_samples), 0, 1)
        df['device_risk'] = np.clip(df['device_risk'] + np.random.normal(0, 0.05, n_samples), 0, 1)
        
        # Recalculate risk score after adding noise
        df['risk_score'] = (
            df['failed_attempts'] * 0.3 +
            df['location_risk'] * 0.2 +
            df['time_risk'] * 0.15 +
            df['breach_risk'] * 0.2 +
            df['device_risk'] * 0.15
        )
        
        # Save to CSV
        df.to_csv(output_file, index=False)
        print(f"Data saved to {output_file}")
        
        # Print class distribution
        print("\nClass distribution:")
        print(df['security_level'].value_counts(normalize=True))
        
        return df
    
    def combine_data(self, real_data='login_data.csv', synthetic_data='synthetic_login_data.csv', 
                    output_file='combined_data.csv'):
        """
        Combine real and synthetic data
        
        Args:
            real_data: Path to real data CSV
            synthetic_data: Path to synthetic data CSV
            output_file: Path to save combined data
            
        Returns:
            DataFrame with combined data
        """
        if not os.path.exists(real_data):
            print(f"Warning: {real_data} not found, using only synthetic data")
            return pd.read_csv(synthetic_data)
        
        df_real = pd.read_csv(real_data)
        df_synthetic = pd.read_csv(synthetic_data)
        
        # Drop username column from real data if it exists
        if 'username' in df_real.columns:
            df_real = df_real.drop(columns=['username'])
        
        # Combine the data
        df_combined = pd.concat([df_real, df_synthetic], ignore_index=True)
        
        # Save to CSV
        df_combined.to_csv(output_file, index=False)
        print(f"Combined data saved to {output_file}")
        
        return df_combined

def main():
    """Main function to collect and prepare data"""
    parser = argparse.ArgumentParser(description='Collect and prepare data for ML-based MFA')
    parser.add_argument('--real', action='store_true', help='Collect real data from logs')
    parser.add_argument('--synthetic', action='store_true', help='Generate synthetic data')
    parser.add_argument('--combine', action='store_true', help='Combine real and synthetic data')
    parser.add_argument('--samples', type=int, default=5000, help='Number of samples to generate')
    
    args = parser.parse_args()
    
    collector = DataCollector()
    
    if args.real:
        collector.collect_from_logs(sample_size=min(args.samples, 1000))
    
    if args.synthetic or not (args.real or args.combine):
        collector.generate_synthetic_data(n_samples=args.samples)
    
    if args.combine:
        collector.combine_data()
    
if __name__ == '__main__':
    main()