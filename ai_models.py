import pandas as pd
import numpy as np
from sklearn.linear_model import Ridge
import joblib
import random
from datetime import datetime, timedelta

DEMAND_MODEL_FILE = 'demand_model.pkl'
ETA_MODEL_FILE = 'eta_model.pkl'

def generate_historical_data(days=60):
    """Generates synthetic data for training models."""
    data = []
    start_date = datetime.now() - timedelta(days=days)
    for i in range(days * 24 * 4): # 15-min intervals
        time_point = start_date + timedelta(minutes=i * 15)
        hour = time_point.hour
        day_of_week = time_point.weekday()

        base_demand = random.randint(100, 300)
        multiplier = 2.0 if 8 <= hour <= 9 or 17 <= hour <= 18 else 0.8
        total_ridership = int(base_demand * multiplier)
        
        data.append({
            'day_of_week': day_of_week,
            'hour_of_day': hour,
            'ridership': total_ridership,
            'avg_speed_kmh': random.uniform(20, 45)
        })
    return pd.DataFrame(data)

def train_eta_predictor():
    """Trains a Ridge Regression model for ETA prediction (Time = Distance / Speed)."""
    print("Training ETA Prediction Model...")
    df = generate_historical_data(days=90) 
    
    # X: [Speed, Dummy_Distance=1]
    X = df[['avg_speed_kmh']].values
    X_eta = np.hstack((X, np.ones((len(X), 1))))
    
    # y: Time to cover 1 km (in minutes)
    y_eta = (1 / df['avg_speed_kmh']) * 60 

    model = Ridge(alpha=1.0) 
    model.fit(X_eta, y_eta)
    
    joblib.dump(model, ETA_MODEL_FILE)
    print(f"ETA model trained and saved to {ETA_MODEL_FILE}")

def predict_eta(model, speed_kmh, distance_km):
    """Predicts ETA in minutes based on real-time speed and distance."""
    if not model:
        return max(1, round(60 * distance_km / max(1, speed_kmh)))
        
    input_data_1km = np.array([[speed_kmh, 1]])
    time_for_1km = model.predict(input_data_1km)[0]
    predicted_time = time_for_1km * distance_km
    
    return max(0.5, predicted_time)

if __name__ == '__main__':
    # When run directly, train both models
    train_eta_predictor()
