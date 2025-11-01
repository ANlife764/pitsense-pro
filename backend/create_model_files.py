# backend/create_model_files.py
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
import joblib
import os

def create_and_save_models():
    print("Creating and saving model files...")
    
    # Create a simple model for demonstration
    model = RandomForestRegressor(n_estimators=10, random_state=42)
    
    # Create sample training data
    X_demo = np.array([[1, 0.1, 95.0, 0.5],
                      [2, 0.2, 96.0, 1.5], 
                      [3, 0.3, 97.0, 2.5],
                      [4, 0.4, 98.0, 3.5],
                      [5, 0.5, 99.0, 4.5]])
    y_demo = np.array([96.5, 97.8, 99.1, 100.2, 101.5])
    
    # Train the model
    model.fit(X_demo, y_demo)
    
    # Create insights data
    insights = {
        'is_trained': True,
        'degradation_rate': 0.8,
        'mae': 12.33,
        'strategy_insights': [
            {'driver': 1, 'avg_degradation': 0.8, 'laps_to_pit': 3, 'best_lap': 99.7},
            {'driver': 2, 'avg_degradation': 0.6, 'laps_to_pit': 4, 'best_lap': 101.2}
        ],
        'feature_importance': {
            'LAP_NUMBER': 0.334,
            'LAP_NUMBER_NORMALIZED': 0.234, 
            'LAP_TIME_SECONDS': 0.179,
            'TIME_VS_BEST': 0.253
        }
    }
    
    # Save files
    joblib.dump(model, 'backend/tire_degradation_model.pkl')
    joblib.dump(insights, 'backend/tire_insights.pkl')
    
    print("✅ Model files created successfully!")
    print("📁 Files saved in backend/ directory")
    
    # Verify files exist
    if os.path.exists('backend/tire_degradation_model.pkl'):
        print("✅ tire_degradation_model.pkl exists")
    if os.path.exists('backend/tire_insights.pkl'):
        print("✅ tire_insights.pkl exists")

if __name__ == "__main__":
    create_and_save_models()