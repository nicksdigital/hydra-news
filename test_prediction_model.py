#!/usr/bin/env python3
# Comprehensive test for the prediction model in the Hydra News system
# This script tests the news event prediction model with different parameters

import os
import sys
import argparse
import logging
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/prediction_test.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("prediction_test")

# Set path to include the src directory
sys.path.append(os.path.join(os.path.dirname(__file__), 'python'))

# Import the necessary modules (adjust imports based on actual module structure)
try:
    from python.src.gdelt.analyzer.prediction.predictor import NewsEventPredictor
    from python.src.gdelt.analyzer.prediction.models import TimeSeriesModel
    from python.src.gdelt.analyzer.prediction.report_generator import PredictionReportGenerator
    from python.src.gdelt.analyzer.prediction.visualizer import PredictionVisualizer
    logger.info("Successfully imported prediction modules")
except ImportError as e:
    logger.error(f"Failed to import prediction modules: {e}")
    sys.exit(1)

def load_test_data(data_dir, entity_name=None):
    """
    Load test data from a directory. If entity_name is provided,
    load data only for that entity, otherwise load data for all entities
    """
    logger.info(f"Loading test data from {data_dir}")
    
    try:
        # Load historical mentions data
        mentions_file = os.path.join(data_dir, 'entity_mentions.csv')
        if os.path.exists(mentions_file):
            df = pd.read_csv(mentions_file)
            logger.info(f"Loaded {len(df)} rows from {mentions_file}")
            
            if entity_name:
                df = df[df['entity_name'] == entity_name]
                logger.info(f"Filtered to {len(df)} rows for entity '{entity_name}'")
            
            return df
        else:
            # Try to find any suitable data files
            json_files = [f for f in os.listdir(data_dir) if f.endswith('.json')]
            if json_files:
                for json_file in json_files:
                    with open(os.path.join(data_dir, json_file), 'r') as f:
                        data = json.load(f)
                    logger.info(f"Loaded alternative data from {json_file}")
                    return data
            else:
                logger.error(f"No suitable data files found in {data_dir}")
                return None
    except Exception as e:
        logger.error(f"Error loading data: {e}")
        return None

def evaluate_prediction(actual, predicted):
    """
    Evaluate prediction accuracy using various metrics
    """
    if len(actual) != len(predicted):
        logger.warning(f"Length mismatch: actual={len(actual)}, predicted={len(predicted)}")
        min_len = min(len(actual), len(predicted))
        actual = actual[:min_len]
        predicted = predicted[:min_len]
    
    # Calculate error metrics
    mse = np.mean((np.array(actual) - np.array(predicted)) ** 2)
    mae = np.mean(np.abs(np.array(actual) - np.array(predicted)))
    
    # Calculate correlation
    corr = np.corrcoef(actual, predicted)[0, 1] if len(actual) > 1 else 0
    
    return {
        'mse': mse,
        'mae': mae,
        'correlation': corr
    }

def visualize_predictions(actual, predicted, entity_name, output_dir):
    """
    Generate visualization of actual vs predicted values
    """
    os.makedirs(output_dir, exist_ok=True)
    
    plt.figure(figsize=(12, 6))
    plt.plot(actual, label='Actual', marker='o')
    plt.plot(predicted, label='Predicted', marker='x')
    plt.title(f'Prediction Results for {entity_name}')
    plt.xlabel('Time')
    plt.ylabel('Mention Count')
    plt.legend()
    plt.grid(True)
    
    output_file = os.path.join(output_dir, f'{entity_name.replace(" ", "_")}_prediction.png')
    plt.savefig(output_file)
    plt.close()
    
    logger.info(f"Visualization saved to {output_file}")

def test_prediction_model(dataset_dir, output_dir, entity_name=None, days_to_predict=7, 
                         training_days=30, models=None, test_all_entities=False):
    """
    Test the prediction model with various parameters
    """
    logger.info("Starting prediction model test")
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Load test data
    df = load_test_data(dataset_dir, entity_name)
    if df is None:
        logger.error("Failed to load test data")
        return False
    
    results = {}
    
    # If testing all entities, get list of entities
    if test_all_entities:
        if isinstance(df, pd.DataFrame) and 'entity_name' in df.columns:
            entities = df['entity_name'].unique()
        else:
            logger.error("Cannot test all entities with the provided data format")
            return False
    else:
        entities = [entity_name] if entity_name else ['default_entity']
    
    # Default models if not specified
    if not models:
        models = ['arima', 'prophet', 'lstm']
    
    for entity in entities:
        logger.info(f"Testing prediction for entity: {entity}")
        
        # Filter data for this entity
        if isinstance(df, pd.DataFrame) and 'entity_name' in df.columns:
            entity_df = df[df['entity_name'] == entity]
        else:
            entity_df = df
        
        entity_results = {}
        
        # Test each model
        for model_name in models:
            logger.info(f"Testing model: {model_name}")
            
            try:
                # Create and configure the predictor
                predictor = NewsEventPredictor(
                    training_days=training_days,
                    days_to_predict=days_to_predict,
                    model_type=model_name
                )
                
                # Train the model
                predictor.train(entity_df)
                
                # Make predictions
                predictions = predictor.predict()
                
                # Split data for evaluation
                if isinstance(entity_df, pd.DataFrame):
                    # Assuming the last days_to_predict rows are for testing
                    test_data = entity_df.iloc[-days_to_predict:]['count'].values
                else:
                    # Mock test data if we don't have the right format
                    test_data = np.random.rand(days_to_predict) * 10
                
                # Evaluate the predictions
                evaluation = evaluate_prediction(test_data, predictions)
                
                # Save the results
                entity_results[model_name] = {
                    'predictions': predictions.tolist() if isinstance(predictions, np.ndarray) else predictions,
                    'evaluation': evaluation
                }
                
                # Visualize the predictions
                visualize_predictions(
                    test_data, 
                    predictions, 
                    f"{entity} - {model_name}", 
                    os.path.join(output_dir, 'visualizations')
                )
                
                logger.info(f"Model {model_name} evaluation: MSE={evaluation['mse']:.4f}, MAE={evaluation['mae']:.4f}, Corr={evaluation['correlation']:.4f}")
                
            except Exception as e:
                logger.error(f"Error testing model {model_name}: {e}")
                entity_results[model_name] = {'error': str(e)}
        
        results[entity] = entity_results
    
    # Save overall results
    results_file = os.path.join(output_dir, 'prediction_test_results.json')
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Test results saved to {results_file}")
    
    return True

def main():
    parser = argparse.ArgumentParser(description='Test Hydra News prediction models')
    parser.add_argument('--dataset-dir', type=str, default='analysis_gdelt_enhanced',
                        help='Directory containing the dataset')
    parser.add_argument('--output-dir', type=str, default='test_results/prediction',
                        help='Directory to save test results')
    parser.add_argument('--entity', type=str, default=None,
                        help='Entity name to test (default: test all entities)')
    parser.add_argument('--days-to-predict', type=int, default=7,
                        help='Number of days to predict (default: 7)')
    parser.add_argument('--training-days', type=int, default=30,
                        help='Number of days to use for training (default: 30)')
    parser.add_argument('--models', type=str, default='arima,prophet',
                        help='Comma-separated list of models to test (default: arima,prophet)')
    parser.add_argument('--test-all-entities', action='store_true',
                        help='Test all entities in the dataset')
    
    args = parser.parse_args()
    
    # Split comma-separated models into a list
    models = args.models.split(',')
    
    # Run the test
    success = test_prediction_model(
        dataset_dir=args.dataset_dir,
        output_dir=args.output_dir,
        entity_name=args.entity,
        days_to_predict=args.days_to_predict,
        training_days=args.training_days,
        models=models,
        test_all_entities=args.test_all_entities
    )
    
    if success:
        logger.info("Prediction model test completed successfully")
        return 0
    else:
        logger.error("Prediction model test failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
