#!/usr/bin/env python3
"""
Machine Learning Security Module for SecureChat
This module provides ML-based security level determination for multi-factor authentication.
"""
import os
import sys
import numpy as np
import pandas as pd
import pickle
import joblib
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
from sklearn.pipeline import Pipeline
import matplotlib.pyplot as plt
import seaborn as sns
from flask import request, session
from datetime import datetime, timedelta

# Add the parent directory to Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from app.models.models import User, FaceVerificationLog
from app.security.security_ai import (
    get_failed_attempts_risk,
    get_location_risk,
    get_time_risk,
    get_previous_breaches_risk,
    get_device_risk,
    SECURITY_LEVEL_LOW,
    SECURITY_LEVEL_MEDIUM,
    SECURITY_LEVEL_HIGH
)

# Path to save trained model
MODEL_DIR = os.path.join(os.path.dirname(__file__), 'models')
DEFAULT_MODEL_PATH = os.path.join(MODEL_DIR, 'security_model.pkl')

class MLSecurityClassifier:
    """Machine Learning classifier for security level determination"""
    
    def __init__(self, model_path=None):
        """
        Initialize the ML security classifier
        
        Args:
            model_path (str): Path to the trained model file
        """
        self.model_path = model_path or DEFAULT_MODEL_PATH
        self.model = None
        self.scaler = None
        self.feature_names = [
            'failed_attempts',
            'location_risk',
            'time_risk',
            'breach_risk',
            'device_risk'
        ]
        
        # Try to load the model if it exists
        self._load_model()
    
    def _load_model(self):
        """Load the trained model from disk"""
        try:
            if os.path.exists(self.model_path):
                print(f"Loading model from {self.model_path}")
                self.model = joblib.load(self.model_path)
                # If model is a pipeline, extract the scaler
                if hasattr(self.model, 'steps'):
                    for step_name, step in self.model.steps:
                        if isinstance(step, StandardScaler):
                            self.scaler = step
                            break
                return True
            else:
                print(f"Model file {self.model_path} not found")
                return False
        except Exception as e:
            print(f"Error loading model: {e}")
            return False
    
    def train(self, data_file, model_type='rf', test_size=0.2, random_state=42):
        """
        Train a new security level prediction model
        
        Args:
            data_file (str): Path to CSV data file
            model_type (str): Model type: 'rf' for Random Forest, 'gb' for Gradient Boosting, 'mlp' for Neural Network
            test_size (float): Fraction of data to use for testing
            random_state (int): Random seed for reproducibility
            
        Returns:
            dict: Training results including accuracy and classification report
        """
        print(f"Training new model using {data_file}")
        
        # Create models directory if it doesn't exist
        if not os.path.exists(MODEL_DIR):
            os.makedirs(MODEL_DIR)
        
        # Load data
        df = pd.read_csv(data_file)
        
        # Split features and target
        X = df[self.feature_names]
        y = df['security_level']
        
        # Train-test split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state, stratify=y
        )
        
        # Create and train the selected model
        if model_type == 'rf':
            # Random Forest with GridSearch
            param_grid = {
                'classifier__n_estimators': [50, 100, 200],
                'classifier__max_depth': [None, 10, 20],
                'classifier__min_samples_split': [2, 5, 10]
            }
            base_model = RandomForestClassifier(random_state=random_state)
            
        elif model_type == 'gb':
            # Gradient Boosting
            param_grid = {
                'classifier__n_estimators': [50, 100, 200],
                'classifier__learning_rate': [0.01, 0.1, 0.2],
                'classifier__max_depth': [3, 5, 7]
            }
            base_model = GradientBoostingClassifier(random_state=random_state)
            
        else:  # MLP Neural Network
            # Multi-layer Perceptron
            param_grid = {
                'classifier__hidden_layer_sizes': [(10,), (20,), (10, 10)],
                'classifier__activation': ['relu', 'tanh'],
                'classifier__alpha': [0.0001, 0.001, 0.01]
            }
            base_model = MLPClassifier(random_state=random_state, max_iter=1000)
        
        # Create a pipeline with scaling
        pipeline = Pipeline([
            ('scaler', StandardScaler()),
            ('classifier', base_model)
        ])
        
        # Grid search
        print("Running grid search for hyperparameter tuning...")
        grid_search = GridSearchCV(
            pipeline, param_grid, cv=5, scoring='accuracy', verbose=1, n_jobs=-1
        )
        grid_search.fit(X_train, y_train)
        
        # Get the best model
        print(f"Best parameters: {grid_search.best_params_}")
        self.model = grid_search.best_estimator_
        
        # Evaluate the model
        y_pred = self.model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        report = classification_report(y_test, y_pred, output_dict=True)
        
        print(f"Model accuracy: {accuracy:.4f}")
        print(classification_report(y_test, y_pred))
        
        # Plot confusion matrix
        cm = confusion_matrix(y_test, y_pred, labels=['low', 'medium', 'high'])
        plt.figure(figsize=(8, 6))
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                    xticklabels=['low', 'medium', 'high'],
                    yticklabels=['low', 'medium', 'high'])
        plt.ylabel('True Label')
        plt.xlabel('Predicted Label')
        plt.title('Confusion Matrix')
        
        # Save confusion matrix
        cm_path = os.path.join(MODEL_DIR, 'confusion_matrix.png')
        plt.savefig(cm_path)
        print(f"Confusion matrix saved to {cm_path}")
        
        # Plot feature importance for tree-based models
        if model_type in ['rf', 'gb']:
            # Extract the classifier from the pipeline
            classifier = self.model.named_steps['classifier']
            importances = classifier.feature_importances_
            indices = np.argsort(importances)[::-1]
            
            plt.figure(figsize=(10, 6))
            plt.title('Feature Importances')
            plt.bar(range(X.shape[1]), importances[indices], align='center')
            plt.xticks(range(X.shape[1]), [self.feature_names[i] for i in indices], rotation=45)
            plt.tight_layout()
            
            # Save feature importance
            feat_path = os.path.join(MODEL_DIR, 'feature_importance.png')
            plt.savefig(feat_path)
            print(f"Feature importance plot saved to {feat_path}")
        
        # Save the model
        joblib.dump(self.model, self.model_path)
        print(f"Model saved to {self.model_path}")
        
        # Save evaluation results
        results = {
            'accuracy': accuracy,
            'classification_report': report,
            'best_params': grid_search.best_params_,
            'model_type': model_type,
            'confusion_matrix': cm.tolist()
        }
        
        return results
    
    def predict(self, features):
        """
        Predict security level based on input features
        
        Args:
            features (dict): Dictionary containing risk factors
            
        Returns:
            str: Predicted security level ('low', 'medium', or 'high')
        """
        if self.model is None:
            print("Warning: Model not loaded. Using rule-based fallback.")
            # Use rule-based fallback
            risk_score = (
                features['failed_attempts'] * 0.3 +
                features['location_risk'] * 0.2 +
                features['time_risk'] * 0.15 +
                features['breach_risk'] * 0.2 +
                features['device_risk'] * 0.15
            )
            
            if risk_score < 0.3:
                return 'low'
            elif risk_score < 0.7:
                return 'medium'
            else:
                return 'high'
        
        # Extract features in the correct order
        X = np.array([
            features['failed_attempts'],
            features['location_risk'],
            features['time_risk'],
            features['breach_risk'],
            features['device_risk']
        ]).reshape(1, -1)
        
        # Predict
        security_level = self.model.predict(X)[0]
        
        return security_level
    
    def predict_proba(self, features):
        """
        Predict security level probabilities
        
        Args:
            features (dict): Dictionary containing risk factors
            
        Returns:
            dict: Probabilities for each security level
        """
        if self.model is None:
            print("Warning: Model not loaded. Using rule-based fallback.")
            # Use rule-based fallback
            risk_score = (
                features['failed_attempts'] * 0.3 +
                features['location_risk'] * 0.2 +
                features['time_risk'] * 0.15 +
                features['breach_risk'] * 0.2 +
                features['device_risk'] * 0.15
            )
            
            # Convert risk score to probabilities
            if risk_score < 0.3:
                probs = {'low': 0.8, 'medium': 0.15, 'high': 0.05}
            elif risk_score < 0.7:
                probs = {'low': 0.1, 'medium': 0.8, 'high': 0.1}
            else:
                probs = {'low': 0.05, 'medium': 0.15, 'high': 0.8}
                
            return probs
        
        # Extract features in the correct order
        X = np.array([
            features['failed_attempts'],
            features['location_risk'],
            features['time_risk'],
            features['breach_risk'],
            features['device_risk']
        ]).reshape(1, -1)
        
        # Get probabilities
        probs = self.model.predict_proba(X)[0]
        
        # Convert to dictionary
        classes = self.model.classes_
        probs_dict = {class_name: prob for class_name, prob in zip(classes, probs)}
        
        return probs_dict

def get_ml_security_level(username):
    """
    Calculate the security level required for a user based on ML prediction.
    This function is designed as a drop-in replacement for calculate_security_level
    
    Args:
        username (str): The username attempting to log in
        
    Returns:
        int: The security level required (1=Low, 2=Medium, 3=High)
    """
    try:
        user = User.query.filter_by(username=username).first()
        
        # If user doesn't exist, require medium security by default
        if not user:
            return SECURITY_LEVEL_MEDIUM
        
        # Calculate risk factors
        features = {
            'failed_attempts': get_failed_attempts_risk(user),
            'location_risk': get_location_risk(),
            'time_risk': get_time_risk(),
            'breach_risk': get_previous_breaches_risk(user),
            'device_risk': get_device_risk()
        }
        
        # Get ML model instance
        classifier = MLSecurityClassifier()
        
        # Predict security level
        security_level = classifier.predict(features)
        
        # Map string level to numeric constant
        if security_level == 'low':
            return SECURITY_LEVEL_LOW
        elif security_level == 'medium':
            return SECURITY_LEVEL_MEDIUM
        else:
            return SECURITY_LEVEL_HIGH
            
    except Exception as e:
        print(f"Error in ML security assessment: {str(e)}")
        # Fall back to medium security level
        return SECURITY_LEVEL_MEDIUM

def get_ml_risk_details(username):
    """
    Get detailed risk assessment information for a user using ML model predictions.
    This function is designed as a potential replacement for get_risk_details
    
    Args:
        username (str): The username to assess
        
    Returns:
        dict: Dictionary containing risk assessment details
    """
    try:
        user = User.query.filter_by(username=username).first()
        
        if not user:
            # Return default medium risk details
            return {
                'security_level': 'Medium',
                'security_level_num': SECURITY_LEVEL_MEDIUM,
                'risk_score': 0.5,
                'risk_factors': {
                    'failed_attempts': {'score': 0.0, 'description': 'Unknown user'},
                    'unusual_location': {'score': 0.5, 'description': 'New login location'},
                    'time_risk': {'score': float(get_time_risk()), 'description': 'Time of login risk'},
                    'previous_breaches': {'score': 0.5, 'description': 'Unknown user history'},
                    'device_risk': {'score': float(get_device_risk()), 'description': 'Device type risk'}
                },
                'required_factors': ['Password', 'CAPTCHA'],
                'ml_assessment': True
            }
        
        # Calculate risk factors
        features = {
            'failed_attempts': get_failed_attempts_risk(user),
            'location_risk': get_location_risk(),
            'time_risk': get_time_risk(),
            'breach_risk': get_previous_breaches_risk(user),
            'device_risk': get_device_risk()
        }
        
        # Calculate risk score (weighted average)
        weighted_score = (
            features['failed_attempts'] * 0.3 +
            features['location_risk'] * 0.2 +
            features['time_risk'] * 0.15 +
            features['breach_risk'] * 0.2 +
            features['device_risk'] * 0.15
        )
        
        # Get ML model instance
        classifier = MLSecurityClassifier()
        
        # Predict security level
        security_level = classifier.predict(features)
        
        # Get probabilities for each level
        level_probs = classifier.predict_proba(features)
        
        # Get risk factor descriptions
        from app.security.security_ai import (
            get_failed_attempts_description,
            get_location_description,
            get_time_risk_description,
            get_breach_description,
            get_device_description
        )
        
        risk_factors = {
            'failed_attempts': {
                'score': float(features['failed_attempts']),
                'description': get_failed_attempts_description(features['failed_attempts']),
                'confidence': level_probs.get('high', 0) * 100 if features['failed_attempts'] > 0.5 else 
                             level_probs.get('low', 0) * 100
            },
            'unusual_location': {
                'score': float(features['location_risk']),
                'description': get_location_description(features['location_risk']),
                'confidence': level_probs.get('high', 0) * 100 if features['location_risk'] > 0.5 else 
                             level_probs.get('low', 0) * 100
            },
            'time_risk': {
                'score': float(features['time_risk']),
                'description': get_time_risk_description(),
                'confidence': level_probs.get('high', 0) * 100 if features['time_risk'] > 0.5 else 
                             level_probs.get('low', 0) * 100
            },
            'previous_breaches': {
                'score': float(features['breach_risk']),
                'description': get_breach_description(user),
                'confidence': level_probs.get('high', 0) * 100 if features['breach_risk'] > 0.5 else 
                             level_probs.get('low', 0) * 100
            },
            'device_risk': {
                'score': float(features['device_risk']),
                'description': get_device_description(),
                'confidence': level_probs.get('high', 0) * 100 if features['device_risk'] > 0.5 else 
                             level_probs.get('low', 0) * 100
            }
        }
        
        # Map security level to required factors
        if security_level == 'low':
            security_level_num = SECURITY_LEVEL_LOW
            required_factors = ['Password']
        elif security_level == 'medium':
            security_level_num = SECURITY_LEVEL_MEDIUM
            required_factors = ['Password', 'CAPTCHA']
        else:
            security_level_num = SECURITY_LEVEL_HIGH
            required_factors = ['Password', 'CAPTCHA', 'Face Verification']
            
        # Capitalize the security level for display
        display_level = security_level.capitalize()
            
        return {
            'security_level': display_level,
            'security_level_num': security_level_num,
            'risk_score': float(weighted_score),
            'risk_factors': risk_factors,
            'required_factors': required_factors,
            'ml_assessment': True,
            'ml_confidence': max(level_probs.values()) * 100,  # Confidence percentage
            'ml_probabilities': {k: v*100 for k, v in level_probs.items()}  # Probabilities as percentages
        }
        
    except Exception as e:
        print(f"Error in ML risk assessment: {str(e)}")
        # Return a default medium security level
        return {
            'security_level': 'Medium',
            'security_level_num': SECURITY_LEVEL_MEDIUM,
            'risk_score': 0.5,
            'risk_factors': {
                'error': {'score': 0.5, 'description': 'Error in ML assessment'}
            },
            'required_factors': ['Password', 'CAPTCHA'],
            'ml_assessment': False
        }

def main():
    """Main function to train and test the ML security model"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Train and evaluate ML security models')
    parser.add_argument('--train', action='store_true', help='Train a new model')
    parser.add_argument('--data', default='combined_data.csv', help='Data file for training (CSV)')
    parser.add_argument('--model', default='rf', choices=['rf', 'gb', 'mlp'], help='Model type')
    parser.add_argument('--test', action='store_true', help='Test model on sample data')
    parser.add_argument('--compare', action='store_true', help='Compare ML and rule-based predictions')
    
    args = parser.parse_args()
    
    classifier = MLSecurityClassifier()
    
    if args.train:
        # Train new model
        print(f"Training {args.model} model using {args.data}")
        classifier.train(args.data, model_type=args.model)
    
    if args.test:
        # Test on sample data
        sample_features = {
            'failed_attempts': 0.8,
            'location_risk': 0.9,
            'time_risk': 0.8,
            'breach_risk': 0.7,
            'device_risk': 0.6
        }
        
        prediction = classifier.predict(sample_features)
        probabilities = classifier.predict_proba(sample_features)
        
        print("\nTest prediction on high-risk sample:")
        print(f"Security level: {prediction}")
        print(f"Probabilities: {probabilities}")
        
        sample_features = {
            'failed_attempts': 0.2,
            'location_risk': 0.5,
            'time_risk': 0.5,
            'breach_risk': 0.5,
            'device_risk': 0.3
        }
        
        prediction = classifier.predict(sample_features)
        probabilities = classifier.predict_proba(sample_features)
        
        print("\nTest prediction on medium-risk sample:")
        print(f"Security level: {prediction}")
        print(f"Probabilities: {probabilities}")
        
        sample_features = {
            'failed_attempts': 0.0,
            'location_risk': 0.1,
            'time_risk': 0.2,
            'breach_risk': 0.2,
            'device_risk': 0.3
        }
        
        prediction = classifier.predict(sample_features)
        probabilities = classifier.predict_proba(sample_features)
        
        print("\nTest prediction on low-risk sample:")
        print(f"Security level: {prediction}")
        print(f"Probabilities: {probabilities}")
    
    if args.compare:
        # Compare with rule-based model on sample data
        import pandas as pd
        
        if os.path.exists(args.data):
            # Load a few samples from the data
            df = pd.read_csv(args.data).sample(5)
            
            print("\nComparing ML and rule-based predictions:")
            print("-" * 80)
            print("| Features | Rule-Based | ML Prediction | ML Probabilities |")
            print("-" * 80)
            
            for _, row in df.iterrows():
                features = {col: row[col] for col in classifier.feature_names}
                
                # Rule-based prediction
                risk_score = (
                    features['failed_attempts'] * 0.3 +
                    features['location_risk'] * 0.2 +
                    features['time_risk'] * 0.15 +
                    features['breach_risk'] * 0.2 +
                    features['device_risk'] * 0.15
                )
                
                if risk_score < 0.3:
                    rule_based = 'low'
                elif risk_score < 0.7:
                    rule_based = 'medium'
                else:
                    rule_based = 'high'
                
                # ML prediction
                ml_pred = classifier.predict(features)
                ml_probs = classifier.predict_proba(features)
                
                # Format the features for display
                features_str = " ".join([f"{k[:5]}:{v:.2f}" for k, v in features.items()])
                probs_str = " ".join([f"{k}:{v:.2f}" for k, v in ml_probs.items()])
                
                print(f"| {features_str} | {rule_based:10} | {ml_pred:13} | {probs_str:30} |")
            
            print("-" * 80)
        else:
            print(f"Error: Data file {args.data} not found")

if __name__ == "__main__":
    main()