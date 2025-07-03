#!/usr/bin/env python3
"""
Training Script for ML-based MFA Security Model
This module trains a machine learning model to predict security levels
based on risk factors.
"""
import os
import sys
import argparse
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split, learning_curve
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score

# Add the parent directory to the path
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

# Import ML security module
from ml_mfa.ml_security import MLSecurityClassifier
from ml_mfa.data_collection import DataCollector

def train_model(data_file, model_type='rf', test_size=0.2, random_state=42):
    """
    Train an ML security model
    
    Args:
        data_file (str): Path to CSV data file
        model_type (str): Model type: 'rf', 'gb', or 'mlp'
        test_size (float): Test size for train/test split
        random_state (int): Random state for reproducibility
        
    Returns:
        dict: Training results
    """
    # Create the classifier
    classifier = MLSecurityClassifier()
    
    # Train the model
    results = classifier.train(data_file, model_type=model_type, 
                            test_size=test_size, random_state=random_state)
    
    return results

def plot_learning_curves(data_file, model_types=['rf', 'gb', 'mlp'], random_state=42):
    """
    Plot learning curves for different models
    
    Args:
        data_file (str): Path to CSV data file
        model_types (list): List of model types to train
        random_state (int): Random state for reproducibility
    """
    # Load data
    df = pd.read_csv(data_file)
    
    # Split features and target
    feature_names = ['failed_attempts', 'location_risk', 'time_risk', 'breach_risk', 'device_risk']
    X = df[feature_names]
    y = df['security_level']
    
    # Create figure
    fig, axes = plt.subplots(1, len(model_types), figsize=(20, 5))
    
    # Train and plot learning curves for each model type
    for i, model_type in enumerate(model_types):
        # Initialize classifier
        classifier = MLSecurityClassifier()
        
        # Get the model pipeline
        from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
        from sklearn.neural_network import MLPClassifier
        from sklearn.pipeline import Pipeline
        from sklearn.preprocessing import StandardScaler
        
        if model_type == 'rf':
            model = Pipeline([
                ('scaler', StandardScaler()),
                ('classifier', RandomForestClassifier(random_state=random_state))
            ])
            title = 'Random Forest'
        elif model_type == 'gb':
            model = Pipeline([
                ('scaler', StandardScaler()),
                ('classifier', GradientBoostingClassifier(random_state=random_state))
            ])
            title = 'Gradient Boosting'
        else:  # mlp
            model = Pipeline([
                ('scaler', StandardScaler()),
                ('classifier', MLPClassifier(random_state=random_state, max_iter=1000))
            ])
            title = 'Neural Network (MLP)'
            
        # Calculate learning curve
        train_sizes, train_scores, test_scores = learning_curve(
            model, X, y, cv=5, n_jobs=-1, 
            train_sizes=np.linspace(0.1, 1.0, 10),
            random_state=random_state
        )
        
        # Calculate mean and std for train and test scores
        train_mean = np.mean(train_scores, axis=1)
        train_std = np.std(train_scores, axis=1)
        test_mean = np.mean(test_scores, axis=1)
        test_std = np.std(test_scores, axis=1)
        
        # Plot learning curve
        ax = axes[i] if len(model_types) > 1 else axes
        ax.fill_between(train_sizes, train_mean - train_std, train_mean + train_std, alpha=0.1, color='blue')
        ax.fill_between(train_sizes, test_mean - test_std, test_mean + test_std, alpha=0.1, color='orange')
        ax.plot(train_sizes, train_mean, 'o-', color='blue', label='Training score')
        ax.plot(train_sizes, test_mean, 'o-', color='orange', label='Cross-validation score')
        ax.set_title(f'Learning Curve: {title}')
        ax.set_xlabel('Training examples')
        ax.set_ylabel('Accuracy')
        ax.legend(loc='best')
        ax.grid(True)
    
    plt.tight_layout()
    
    # Save the figure
    output_dir = os.path.join(os.path.dirname(__file__), 'models')
    os.makedirs(output_dir, exist_ok=True)
    plt.savefig(os.path.join(output_dir, 'learning_curves.png'))
    print(f"Learning curves saved to {os.path.join(output_dir, 'learning_curves.png')}")

def compare_models(data_file, model_types=['rf', 'gb', 'mlp'], random_state=42):
    """
    Train and compare multiple models
    
    Args:
        data_file (str): Path to CSV data file
        model_types (list): List of model types to train
        random_state (int): Random state for reproducibility
    """
    # Create output directory
    output_dir = os.path.join(os.path.dirname(__file__), 'models')
    os.makedirs(output_dir, exist_ok=True)
    
    # Initialize results dataframe
    results_df = pd.DataFrame(columns=['model_type', 'accuracy', 'low_precision', 'medium_precision', 
                                      'high_precision', 'low_recall', 'medium_recall', 'high_recall'])
    
    # Load data
    df = pd.read_csv(data_file)
    
    # Split features and target
    feature_names = ['failed_attempts', 'location_risk', 'time_risk', 'breach_risk', 'device_risk']
    X = df[feature_names]
    y = df['security_level']
    
    # Train-test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=random_state, stratify=y
    )
    
    # Train and evaluate each model
    for model_type in model_types:
        print(f"\n{'='*80}")
        print(f"Training {model_type} model...")
        print(f"{'='*80}")
        
        # Train model
        classifier = MLSecurityClassifier()
        results = classifier.train(data_file, model_type=model_type, 
                                  test_size=0.2, random_state=random_state)
        
        # Get metrics
        accuracy = results['accuracy']
        report = results['classification_report']
        
        # Add to results dataframe
        results_df = pd.concat([results_df, pd.DataFrame({
            'model_type': [model_type],
            'accuracy': [accuracy],
            'low_precision': [report['low']['precision']],
            'medium_precision': [report['medium']['precision']],
            'high_precision': [report['high']['precision']],
            'low_recall': [report['low']['recall']],
            'medium_recall': [report['medium']['recall']],
            'high_recall': [report['high']['recall']]
        })])
    
    # Save results
    results_csv = os.path.join(output_dir, 'model_comparison.csv')
    results_df.to_csv(results_csv, index=False)
    print(f"Model comparison results saved to {results_csv}")
    
    # Plot results
    plt.figure(figsize=(12, 8))
    
    # Plot accuracy
    plt.subplot(2, 2, 1)
    sns.barplot(x='model_type', y='accuracy', data=results_df)
    plt.title('Model Accuracy')
    plt.ylim(0.8, 1.0)
    
    # Plot precision
    plt.subplot(2, 2, 2)
    precision_df = pd.melt(results_df, 
                         id_vars=['model_type'], 
                         value_vars=['low_precision', 'medium_precision', 'high_precision'],
                         var_name='security_level', value_name='precision')
    precision_df['security_level'] = precision_df['security_level'].str.replace('_precision', '')
    sns.barplot(x='model_type', y='precision', hue='security_level', data=precision_df)
    plt.title('Precision by Security Level')
    plt.ylim(0.8, 1.0)
    
    # Plot recall
    plt.subplot(2, 2, 3)
    recall_df = pd.melt(results_df, 
                       id_vars=['model_type'], 
                       value_vars=['low_recall', 'medium_recall', 'high_recall'],
                       var_name='security_level', value_name='recall')
    recall_df['security_level'] = recall_df['security_level'].str.replace('_recall', '')
    sns.barplot(x='model_type', y='recall', hue='security_level', data=recall_df)
    plt.title('Recall by Security Level')
    plt.ylim(0.8, 1.0)
    
    plt.tight_layout()
    
    # Save figure
    comparison_plot = os.path.join(output_dir, 'model_comparison.png')
    plt.savefig(comparison_plot)
    print(f"Model comparison plot saved to {comparison_plot}")
    
    # Return the best model type based on accuracy
    best_model = results_df.loc[results_df['accuracy'].idxmax()]
    print(f"\nBest model: {best_model['model_type']} with accuracy {best_model['accuracy']:.4f}")
    
    return best_model['model_type']

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Train ML security models')
    parser.add_argument('--generate-data', action='store_true', help='Generate synthetic training data')
    parser.add_argument('--collect-data', action='store_true', help='Collect real data from logs')
    parser.add_argument('--train', action='store_true', help='Train a new model')
    parser.add_argument('--compare', action='store_true', help='Compare different model types')
    parser.add_argument('--model-type', default='rf', choices=['rf', 'gb', 'mlp'], 
                       help='Model type (rf=Random Forest, gb=Gradient Boosting, mlp=Neural Network)')
    parser.add_argument('--learning-curves', action='store_true', help='Plot learning curves')
    parser.add_argument('--samples', type=int, default=5000, help='Number of samples to generate')
    parser.add_argument('--data-file', default='combined_data.csv', help='Path to data file')
    
    args = parser.parse_args()
    
    # Create the ml_mfa/models directory if it doesn't exist
    models_dir = os.path.join(os.path.dirname(__file__), 'models')
    os.makedirs(models_dir, exist_ok=True)
    
    # Generate data if requested
    if args.generate_data:
        collector = DataCollector()
        collector.generate_synthetic_data(n_samples=args.samples)
    
    # Collect real data if requested
    if args.collect_data:
        collector = DataCollector()
        collector.collect_from_logs(sample_size=min(args.samples, 1000))
        collector.combine_data()
    
    # Set data file paths
    data_dir = os.path.dirname(__file__)
    if not os.path.isabs(args.data_file):
        data_file = os.path.join(data_dir, args.data_file)
    else:
        data_file = args.data_file
    
    # Check if data file exists
    if not os.path.exists(data_file):
        if args.generate_data:
            # We just generated data, so look for the synthetic data file
            data_file = os.path.join(data_dir, 'synthetic_login_data.csv')
            if not os.path.exists(data_file):
                print(f"Error: Data file {args.data_file} not found and synthetic data generation failed")
                return
        else:
            print(f"Error: Data file {data_file} not found. Please generate data first with --generate-data")
            return
    
    # Compare models if requested
    if args.compare:
        best_model = compare_models(data_file, model_types=['rf', 'gb', 'mlp'])
        
        # Train the best model
        if args.train:
            print(f"\nTraining the best model ({best_model})...")
            train_model(data_file, model_type=best_model)
    
    # Train a model if requested
    elif args.train:
        train_model(data_file, model_type=args.model_type)
    
    # Plot learning curves if requested
    if args.learning_curves:
        plot_learning_curves(data_file, model_types=['rf', 'gb', 'mlp'])

if __name__ == "__main__":
    main()