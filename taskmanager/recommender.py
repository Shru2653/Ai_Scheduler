import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
import joblib
import os
from .time_quantum_recommender import TimeQuantumRecommender

class ProcessRecommender:
    def __init__(self):
        self.models = {}
        self.scalers = {}
        self.time_quantum_recommender = TimeQuantumRecommender()
        self.dataset_path = os.path.join(os.path.dirname(__file__), 'data', 'process_dataset.csv')
        self.load_or_create_dataset()
        self.train_models()

    def load_or_create_dataset(self):
        if not os.path.exists(self.dataset_path):
            # Create synthetic dataset if it doesn't exist
            self.create_synthetic_dataset()
        self.dataset = pd.read_csv(self.dataset_path)

    def create_synthetic_dataset(self):
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(self.dataset_path), exist_ok=True)
        
        # Generate synthetic data
        np.random.seed(42)
        n_samples = 1000
        
        data = {
            'algorithm': np.random.choice(['round_robin', 'priority', 'ai', 'mlfq', 'deadline', 'sjf'], n_samples),
            'arrival_time': np.random.randint(0, 100, n_samples),
            'burst_time': np.random.randint(1, 50, n_samples),
            'priority': np.random.randint(1, 10, n_samples),
            'deadline': np.random.randint(1, 100, n_samples),
            'optimal_arrival': np.random.randint(0, 100, n_samples),
            'optimal_burst': np.random.randint(1, 50, n_samples),
            'optimal_priority': np.random.randint(1, 10, n_samples),
            'optimal_deadline': np.random.randint(1, 100, n_samples)
        }
        
        df = pd.DataFrame(data)
        df.to_csv(self.dataset_path, index=False)

    def train_models(self):
        algorithms = self.dataset['algorithm'].unique()
        
        for algo in algorithms:
            # Filter data for current algorithm
            algo_data = self.dataset[self.dataset['algorithm'] == algo]
            
            # Prepare features and targets
            if algo in ['priority', 'ai']:
                X = algo_data[['arrival_time', 'burst_time', 'priority']]
                y = algo_data[['optimal_arrival', 'optimal_burst', 'optimal_priority']]
            elif algo == 'deadline':
                X = algo_data[['arrival_time', 'burst_time', 'deadline']]
                y = algo_data[['optimal_arrival', 'optimal_burst', 'optimal_deadline']]
            else:
                X = algo_data[['arrival_time', 'burst_time']]
                y = algo_data[['optimal_arrival', 'optimal_burst']]
            
            # Scale features
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
            
            # Train model
            model = RandomForestRegressor(n_estimators=100, random_state=42)
            model.fit(X_scaled, y)
            
            # Store model and scaler
            self.models[algo] = model
            self.scalers[algo] = scaler

    def get_recommendations(self, algorithm, process_data, time_quantum=None):
        if algorithm not in self.models:
            return None
        
        # Prepare input data
        if algorithm in ['priority', 'ai']:
            X = np.array([[process_data['arrival_time'], 
                          process_data['burst_time'], 
                          process_data.get('priority', 1)]])
        elif algorithm == 'deadline':
            X = np.array([[process_data['arrival_time'], 
                          process_data['burst_time'], 
                          process_data.get('deadline', 1)]])
        else:
            X = np.array([[process_data['arrival_time'], 
                          process_data['burst_time']]])
        
        # Scale input
        X_scaled = self.scalers[algorithm].transform(X)
        
        # Get predictions
        predictions = self.models[algorithm].predict(X_scaled)[0]
        
        # Format recommendations
        recommendations = {
            'optimal_arrival_time': int(round(predictions[0])),
            'optimal_burst_time': int(round(predictions[1]))
        }
        
        if algorithm in ['priority', 'ai']:
            recommendations['optimal_priority'] = int(round(predictions[2]))
        elif algorithm == 'deadline':
            recommendations['optimal_deadline'] = int(round(predictions[2]))
        
        # If time quantum is provided and algorithm is round_robin, add time quantum recommendation
        if algorithm == 'round_robin' and time_quantum is not None:
            time_quantum_recommendation = self.time_quantum_recommender.get_optimal_time_quantum(
                [process_data],
                time_quantum
            )
            recommendations.update(time_quantum_recommendation)
        
        return recommendations