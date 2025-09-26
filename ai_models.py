import pandas as pd
import numpy as np
from sklearn.linear_model import Ridge
import joblib
import random
from datetime import datetime, timedelta

# File paths for saving the trained models
DEMAND_MODEL_FILE = 'demand_model.pkl'
ETA_MODEL_FILE = 'eta_model.pkl'

def generate_historical_data(days=60):
    """
    Generates synthetic historical data for training the ETA model.
    This simulates speed, time of day, and ridership patterns.
    """
    data = []
    start_date = datetime.now() - timedelta(days=days)
    
    # Generate data points in 15-minute intervals
    for i in range(days * 24 * 4): 
        time_point = start_date + timedelta(minutes=i * 15)
        hour = time_point.hour
        day_of_week = time_point.weekday()

        base_demand = random.randint(100, 300)
        # Apply a multiplier for simulated peak hours (Morning/Evening)
        multiplier = 2.0 if 8 <= hour <= 9 or 17 <= hour <= 18 else 0.8
        total_ridership = int(base_demand * multiplier)
        
        data.append({
            'day_of_week': day_of_week,
            'hour_of_day': hour,
            'ridership': total_ridership,
            # Simulated average speed (feature for ETA)
            'avg_speed_kmh': random.uniform(20, 45)
        })
    return pd.DataFrame(data)

def train_eta_predictor():
    """
    Trains a Ridge Regression model to predict travel time per kilometer.
    """
    print("Training ETA Prediction Model...")
    df = generate_historical_data(days=90) 
    
    # X: Features array, combining speed and a dummy constant (1) 
    X = df[['avg_speed_kmh']].values
    X_eta = np.hstack((X, np.ones((len(X), 1))))
    
    # y: Target variable is the time to cover 1 km (in minutes)
    # Calculation: (1 km / Speed km/h) * 60 min/hour
    y_eta = (1 / df['avg_speed_kmh']) * 60 

    # Use Ridge Regression for robust prediction
    model = Ridge(alpha=1.0) 
    model.fit(X_eta, y_eta)
    
    # Save the model object to disk for the Flask app to load
    joblib.dump(model, ETA_MODEL_FILE)
    print(f"ETA model trained and saved to {ETA_MODEL_FILE}")

def predict_eta(model, speed_kmh, distance_km):
    """
    Predicts Estimated Time of Arrival (ETA) in minutes based on 
    the current speed and remaining distance.
    """
    # Fallback to simple calculation if model failed to load
    if not model:
        return max(1, round(60 * distance_km / max(1, speed_kmh)))
        
    # Predict time needed to cover 1km using the model
    input_data_1km = np.array([[speed_kmh, 1]])
    time_for_1km = model.predict(input_data_1km)[0]
    
    # Scale the predicted time by the actual remaining distance
    predicted_time = time_for_1km * distance_km
    
    return max(0.5, predicted_time)

if __name__ == '__main__':
    # This block runs when you execute `py ai_models.py`
    train_eta_predictor()
