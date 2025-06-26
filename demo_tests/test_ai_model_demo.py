#!/usr/bin/env python3
"""
Demonstration test file for showcasing AI model performance and MFA integration.
Includes confusion matrix generation.
"""
import os
import sys
import matplotlib.pyplot as plt
from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
from app import create_app
from app.models.models import User
from ml_mfa.ml_security import get_ml_security_level

def generate_confusion_matrix():
    """Generate and display confusion matrix for the AI model"""
    # Example data (replace with actual data)
    true_labels = [0, 1, 0, 1, 1, 0]  # Replace with actual labels
    predicted_labels = [0, 1, 0, 0, 1, 1]  # Replace with model predictions

    # Generate confusion matrix
    cm = confusion_matrix(true_labels, predicted_labels)
    disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=["Low Risk", "High Risk"])
    disp.plot()

    # Show the plot
    plt.title("Confusion Matrix for AI Model")
    plt.show()

def test_ai_model_demo():
    """Demonstrate AI model performance and MFA integration"""
    app = create_app()
    with app.app_context():
        username = 'testuser'
        user = User.query.filter_by(username=username).first()
        
        if not user:
            print(f"User {username} not found")
            return
        
        print(f"Demonstrating AI model for user: {username}")
        security_level = get_ml_security_level(username)
        print(f"Predicted security level: {security_level}")

    # Generate confusion matrix
    generate_confusion_matrix()

if __name__ == "__main__":
    test_ai_model_demo()
