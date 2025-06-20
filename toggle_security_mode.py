#!/usr/bin/env python3
"""
Toggle between ML-based and rule-based security systems
"""
import os
import sys
import argparse
from flask import Flask, session, request

# Add the project directory to the path
sys.path.insert(0, os.path.abspath('.'))

def toggle_security_mode(mode=None):
    """
    Toggle or set the security mode (ML or rule-based)
    
    Args:
        mode (str): Mode to set ('ml' or 'rule')
    """
    # Create a simple config file to store the mode
    config_dir = os.path.join(os.path.dirname(__file__), 'instance')
    config_file = os.path.join(config_dir, 'security_mode.txt')
    
    # Ensure directory exists
    os.makedirs(config_dir, exist_ok=True)
    
    # If mode is specified, set it
    if mode:
        with open(config_file, 'w') as f:
            f.write(mode)
        print(f"Security mode set to: {'ML-based' if mode == 'ml' else 'Rule-based'}")
    else:
        # Toggle mode if file exists
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                current_mode = f.read().strip()
            
            new_mode = 'rule' if current_mode == 'ml' else 'ml'
            
            with open(config_file, 'w') as f:
                f.write(new_mode)
                
            print(f"Security mode toggled from {current_mode} to {new_mode}")
        else:
            # Default to ML if file doesn't exist
            with open(config_file, 'w') as f:
                f.write('ml')
            print("Security mode set to ML-based (default)")
    
    # Show current status
    try:
        # Make sure Python can find the ml_mfa module
        ml_mfa_path = os.path.join(os.path.dirname(__file__), 'ml_mfa')
        if ml_mfa_path not in sys.path:
            sys.path.insert(0, os.path.dirname(__file__))
        
        # Try loading full ML model first    
        try:
            from ml_mfa.ml_security import MLSecurityClassifier
            ml_available = True
            simplified = False
            
            # Check if model exists
            classifier = MLSecurityClassifier()
            model_loaded = classifier._load_model()
            
            print(f"Full ML security model {'loaded successfully' if model_loaded else 'not found'}")
        except ImportError:
            # Try simplified model
            try:
                from ml_mfa.simplified_ml import SimplifiedMLClassifier
                ml_available = True
                simplified = True
                
                print("Simplified ML security model available")
            except ImportError as e:
                ml_available = False
                simplified = False
                print(f"ML security module not available: {e}")
    except Exception as e:
        ml_available = False
        print(f"Error checking ML availability: {e}")
    
    # Read current mode
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            current_mode = f.read().strip()
        
        print(f"\nCurrent security mode: {'ML-based' if current_mode == 'ml' else 'Rule-based'}")
        
        if current_mode == 'ml' and not ml_available:
            print("Warning: ML mode selected but ML module not available")

def main():
    """Parse command line arguments and toggle mode"""
    parser = argparse.ArgumentParser(description='Toggle security mode between ML and rule-based')
    parser.add_argument('--mode', choices=['ml', 'rule'], help='Set security mode (ml or rule)')
    
    args = parser.parse_args()
    
    toggle_security_mode(args.mode)

if __name__ == '__main__':
    main()
