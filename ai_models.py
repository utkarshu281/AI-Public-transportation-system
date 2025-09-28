import numpy as np
import pandas as pd
import joblib
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Tuple
from sklearn.linear_model import Ridge
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
import random

class TransportAIModel:
    """
    AI Model class for transport ETA predictions using sklearn Ridge regression
    """
    
    def __init__(self, model_path: str = "eta_model.pkl"):
        """Initialize the transport AI model"""
        self.model_path = model_path
        self.model = None
        self.model_loaded = False
        self.training_data = None
        self.feature_names = ['speed_kmh', 'distance_km', 'hour_of_day', 'day_of_week', 'traffic_factor']
        
        # Load existing model or create new one
        self.load_model()
    
    def generate_synthetic_historical_data(self, n_samples: int = 10000) -> pd.DataFrame:
        """
        Generate synthetic historical data for ETA prediction training
        
        Args:
            n_samples: Number of samples to generate
            
        Returns:
            DataFrame with synthetic historical data
        """
        print(f"Generating {n_samples} synthetic historical data samples...")
        
        # Set random seed for reproducibility
        np.random.seed(42)
        random.seed(42)
        
        data = []
        
        for _ in range(n_samples):
            # Generate realistic speed data (km/h)
            # Speed varies by time of day and traffic conditions
            hour = random.randint(0, 23)
            day_of_week = random.randint(0, 6)  # 0=Monday, 6=Sunday
            
            # Base speed varies by time of day
            if 7 <= hour <= 9 or 17 <= hour <= 19:  # Rush hours
                base_speed = random.uniform(15, 35)
                traffic_factor = random.uniform(1.2, 2.0)
            elif 22 <= hour or hour <= 5:  # Night time
                base_speed = random.uniform(40, 60)
                traffic_factor = random.uniform(0.6, 0.9)
            else:  # Normal hours
                base_speed = random.uniform(25, 45)
                traffic_factor = random.uniform(0.8, 1.3)
            
            # Weekend vs weekday differences
            if day_of_week >= 5:  # Weekend
                base_speed *= random.uniform(0.9, 1.1)
                traffic_factor *= random.uniform(0.8, 1.1)
            
            # Add some noise to speed
            speed_kmh = max(5, base_speed + random.gauss(0, 5))
            
            # Generate distance (km)
            distance_km = random.uniform(1, 50)
            
            # Calculate actual travel time based on speed and distance
            # Add some realistic factors that affect travel time
            base_time_hours = distance_km / speed_kmh
            
            # Apply traffic factor
            actual_time_hours = base_time_hours * traffic_factor
            
            # Add some random delays (stops, traffic lights, etc.)
            delay_factor = random.uniform(1.05, 1.25)
            actual_time_hours *= delay_factor
            
            # Convert to minutes
            eta_minutes = max(1, int(actual_time_hours * 60))
            
            # Add some weather impact
            weather_factor = random.choice([0.9, 1.0, 1.1, 1.2, 1.3])  # clear, light rain, heavy rain, snow
            eta_minutes = int(eta_minutes * weather_factor)
            
            data.append({
                'speed_kmh': speed_kmh,
                'distance_km': distance_km,
                'hour_of_day': hour,
                'day_of_week': day_of_week,
                'traffic_factor': traffic_factor,
                'eta_minutes': eta_minutes
            })
        
        df = pd.DataFrame(data)
        print(f"Generated {len(df)} samples")
        print(f"Speed range: {df['speed_kmh'].min():.1f} - {df['speed_kmh'].max():.1f} km/h")
        print(f"Distance range: {df['distance_km'].min():.1f} - {df['distance_km'].max():.1f} km")
        print(f"ETA range: {df['eta_minutes'].min()} - {df['eta_minutes'].max()} minutes")
        
        return df
    
    def train_model(self, training_data: pd.DataFrame = None) -> Dict[str, float]:
        """
        Train Ridge regression model on historical data
        
        Args:
            training_data: DataFrame with training data, if None, generates synthetic data
            
        Returns:
            Dictionary with training metrics
        """
        print("Training Ridge regression model...")
        
        if training_data is None:
            training_data = self.generate_synthetic_historical_data()
        
        self.training_data = training_data
        
        # Prepare features and target
        X = training_data[self.feature_names]
        y = training_data['eta_minutes']
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # Train Ridge regression model
        self.model = Ridge(alpha=1.0, random_state=42)
        self.model.fit(X_train, y_train)
        
        # Make predictions
        y_pred_train = self.model.predict(X_train)
        y_pred_test = self.model.predict(X_test)
        
        # Calculate metrics
        train_mse = mean_squared_error(y_train, y_pred_train)
        test_mse = mean_squared_error(y_test, y_pred_test)
        train_r2 = r2_score(y_train, y_pred_train)
        test_r2 = r2_score(y_test, y_pred_test)
        
        metrics = {
            'train_mse': train_mse,
            'test_mse': test_mse,
            'train_r2': train_r2,
            'test_r2': test_r2,
            'n_samples': len(training_data),
            'n_features': len(self.feature_names)
        }
        
        print(f"Training completed!")
        print(f"Train MSE: {train_mse:.2f}, Train R²: {train_r2:.3f}")
        print(f"Test MSE: {test_mse:.2f}, Test R²: {test_r2:.3f}")
        
        # Save the trained model
        self.save_model()
        
        return metrics
    
    def save_model(self) -> bool:
        """
        Save the trained model using joblib
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if self.model is not None:
                joblib.dump(self.model, self.model_path)
                print(f"Model saved to {self.model_path}")
                return True
            else:
                print("No model to save")
                return False
        except Exception as e:
            print(f"Error saving model: {e}")
            return False
    
    def load_model(self) -> bool:
        """
        Load the trained model using joblib
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if os.path.exists(self.model_path):
                self.model = joblib.load(self.model_path)
                self.model_loaded = True
                print(f"Model loaded from {self.model_path}")
                return True
            else:
                print(f"No existing model found at {self.model_path}")
                # Train a new model if none exists
                self.train_model()
                return True
        except Exception as e:
            print(f"Error loading model: {e}")
            # Train a new model if loading fails
            self.train_model()
            return True
    
    def predict_eta(self, speed_kmh: float, distance_km: float, 
                   hour_of_day: int = None, day_of_week: int = None,
                   traffic_factor: float = 1.0) -> float:
        """
        Predict ETA using the trained Ridge regression model
        
        Args:
            speed_kmh: Speed in km/h
            distance_km: Distance in km
            hour_of_day: Hour of day (0-23), if None uses current hour
            day_of_week: Day of week (0-6), if None uses current day
            traffic_factor: Traffic factor (default 1.0)
            
        Returns:
            Predicted ETA in minutes
        """
        if not self.model_loaded or self.model is None:
            raise Exception("Model not loaded. Please train or load a model first.")
        
        # Use current time if not provided
        if hour_of_day is None:
            hour_of_day = datetime.now().hour
        if day_of_week is None:
            day_of_week = datetime.now().weekday()
        
        # Prepare input features
        features = np.array([[speed_kmh, distance_km, hour_of_day, day_of_week, traffic_factor]])
        
        # Make prediction
        eta_minutes = self.model.predict(features)[0]
        
        # Ensure positive prediction
        eta_minutes = max(1, eta_minutes)
        
        return round(eta_minutes, 1)
    
    def predict_eta_with_confidence(self, speed_kmh: float, distance_km: float,
                                 hour_of_day: int = None, day_of_week: int = None,
                                 traffic_factor: float = 1.0) -> Dict[str, Any]:
        """
        Predict ETA with confidence interval and additional information
        
        Args:
            speed_kmh: Speed in km/h
            distance_km: Distance in km
            hour_of_day: Hour of day (0-23), if None uses current hour
            day_of_week: Day of week (0-6), if None uses current day
            traffic_factor: Traffic factor (default 1.0)
            
        Returns:
            Dictionary with prediction and confidence information
        """
        if not self.model_loaded or self.model is None:
            raise Exception("Model not loaded. Please train or load a model first.")
        
        # Get base prediction
        eta_minutes = self.predict_eta(speed_kmh, distance_km, hour_of_day, day_of_week, traffic_factor)
        
        # Calculate confidence based on input parameters
        # Higher confidence for more typical conditions
        confidence = 0.7  # Base confidence
        
        # Adjust confidence based on speed (more typical speeds get higher confidence)
        if 20 <= speed_kmh <= 50:
            confidence += 0.1
        elif speed_kmh < 10 or speed_kmh > 70:
            confidence -= 0.1
        
        # Adjust confidence based on distance (very short or very long distances are less predictable)
        if 5 <= distance_km <= 30:
            confidence += 0.1
        elif distance_km < 1 or distance_km > 50:
            confidence -= 0.1
        
        # Adjust confidence based on traffic factor
        if 0.8 <= traffic_factor <= 1.2:
            confidence += 0.05
        elif traffic_factor > 2.0:
            confidence -= 0.1
        
        confidence = max(0.3, min(0.95, confidence))
        
        # Calculate estimated arrival time
        current_time = datetime.now()
        estimated_arrival = current_time + timedelta(minutes=eta_minutes)
        
        return {
            'eta_minutes': eta_minutes,
            'confidence_score': round(confidence, 2),
            'estimated_arrival_time': estimated_arrival.strftime("%Y-%m-%d %H:%M:%S"),
            'input_features': {
                'speed_kmh': speed_kmh,
                'distance_km': distance_km,
                'hour_of_day': hour_of_day or datetime.now().hour,
                'day_of_week': day_of_week or datetime.now().weekday(),
                'traffic_factor': traffic_factor
            }
        }
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the loaded model
        
        Returns:
            Dictionary containing model information
        """
        info = {
            'model_loaded': self.model_loaded,
            'model_type': 'Ridge Regression',
            'model_path': self.model_path,
            'feature_names': self.feature_names,
            'training_samples': len(self.training_data) if self.training_data is not None else 0
        }
        
        if self.model is not None:
            info.update({
                'model_coefficients': self.model.coef_.tolist(),
                'model_intercept': self.model.intercept_,
                'model_alpha': self.model.alpha
            })
        
        return info
    
    def retrain_model(self, new_data: pd.DataFrame = None) -> Dict[str, float]:
        """
        Retrain the model with new data
        
        Args:
            new_data: New training data, if None generates fresh synthetic data
            
        Returns:
            Dictionary with training metrics
        """
        print("Retraining model with new data...")
        return self.train_model(new_data)
