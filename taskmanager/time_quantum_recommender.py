import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
import joblib
import os
from scheduler.scheduler import round_robin

class TimeQuantumRecommender:
    def __init__(self):
        self.model = None
        self.scaler = None
        self.dataset_path = os.path.join(os.path.dirname(__file__), 'data', 'time_quantum_dataset.csv')
        self.load_or_create_dataset()
        self.train_model()

    def load_or_create_dataset(self):
        if not os.path.exists(self.dataset_path):
            self.create_synthetic_dataset()
        self.dataset = pd.read_csv(self.dataset_path)

    def create_synthetic_dataset(self):
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(self.dataset_path), exist_ok=True)
        
        # Generate synthetic data
        np.random.seed(42)
        n_samples = 1000
        
        data = {
            'num_processes': np.random.randint(1, 20, n_samples),
            'total_burst_time': np.random.randint(10, 500, n_samples),
            'average_burst_time': np.random.randint(1, 50, n_samples),
            'optimal_time_quantum': np.random.randint(1, 20, n_samples),
            'throughput': np.random.uniform(0.1, 1.0, n_samples)
        }
        
        df = pd.DataFrame(data)
        df.to_csv(self.dataset_path, index=False)

    def train_model(self):
        # Prepare features and targets
        X = self.dataset[['num_processes', 'total_burst_time', 'average_burst_time', 'throughput']]
        y = self.dataset['optimal_time_quantum']
        
        # Scale features
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)
        
        # Train model
        self.model = RandomForestRegressor(n_estimators=100, random_state=42)
        self.model.fit(X_scaled, y)

    def get_optimal_time_quantum(self, processes, user_time_quantum):
        num_processes = len(processes)
        total_burst_time = sum(proc.get('execution_time', proc.get('burst_time', 0)) for proc in processes)
        average_burst_time = total_burst_time / num_processes if num_processes else 0

        # Run simulation with user's time quantum to get throughput
        user_result = round_robin(processes, user_time_quantum)
        user_metrics = user_result.get('metrics', [])
        print("DEBUG: user_metrics =", user_metrics)
        if user_metrics and isinstance(user_metrics, list) and user_metrics[-1].get('ct', 0):
            user_throughput = len(user_metrics) / user_metrics[-1]['ct']
        else:
            user_throughput = 0
        print("DEBUG: user_throughput =", user_throughput)

        # Prepare input data for ML model (fix sklearn warning)
        X = pd.DataFrame([[num_processes, total_burst_time, average_burst_time, user_throughput]],
            columns=['num_processes', 'total_burst_time', 'average_burst_time', 'throughput'])
        X_scaled = self.scaler.transform(X)
        optimal_time_quantum = int(round(self.model.predict(X_scaled)[0]))
        optimal_time_quantum = max(1, min(20, optimal_time_quantum))
        print("DEBUG: optimal_time_quantum =", optimal_time_quantum)

        # Simulate with recommended quantum
        recommended_result = round_robin(processes, optimal_time_quantum)
        recommended_metrics = recommended_result.get('metrics', [])
        print("DEBUG: recommended_metrics =", recommended_metrics)
        if recommended_metrics and isinstance(recommended_metrics, list) and recommended_metrics[-1].get('ct', 0):
            recommended_throughput = len(recommended_metrics) / recommended_metrics[-1]['ct']
        else:
            recommended_throughput = 0
        print("DEBUG: recommended_throughput =", recommended_throughput)

        print("DEBUG: processes =", processes)
        print("DEBUG: user_time_quantum =", user_time_quantum)
        if recommended_throughput > user_throughput:
            return {
                'optimal_time_quantum': optimal_time_quantum,
                'user_time_quantum': user_time_quantum,
                'throughput': recommended_throughput,
                'user_throughput': user_throughput
            }
        else:
            return {
                'optimal_time_quantum': None,
                'user_time_quantum': user_time_quantum,
                'throughput': None,
                'user_throughput': user_throughput
            }