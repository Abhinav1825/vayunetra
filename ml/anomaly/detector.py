import numpy as np
from sklearn.ensemble import IsolationForest
import pandas as pd
from typing import List, Dict, Any

class AnomalyDetector:
    """
    E4 Stretch: Lightweight Spike/Anomaly Detector using Isolation Forest.
    Detects abnormal PM2.5 spikes based on historical patterns.
    """
    def __init__(self, contamination: float = 0.05):
        # contamination is the expected proportion of outliers
        self.model = IsolationForest(n_estimators=100, contamination=contamination, random_state=42)
        self.is_fitted = False

    def _extract_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Engineers features from a raw timeseries DataFrame.
        Assumes df has columns: ['ts', 'value'] and is sorted by 'ts'.
        """
        df = df.copy()
        df['ts'] = pd.to_datetime(df['ts'])
        df['hour_of_day'] = df['ts'].dt.hour
        df['day_of_week'] = df['ts'].dt.dayofweek
        
        # Rolling statistics (3-hour window)
        # Using min_periods=1 to avoid NaNs at the beginning
        df['rolling_mean_3h'] = df['value'].rolling(window=3, min_periods=1).mean()
        df['rolling_std_3h'] = df['value'].rolling(window=3, min_periods=1).std().fillna(0)
        
        features = df[['value', 'hour_of_day', 'day_of_week', 'rolling_mean_3h', 'rolling_std_3h']]
        return features

    def fit(self, historical_data: List[Dict[str, Any]]):
        """
        Fits the Isolation Forest on historical data.
        historical_data: list of dicts with 'ts' and 'value'
        """
        if not historical_data:
            return
            
        df = pd.DataFrame(historical_data)
        features = self._extract_features(df)
        
        self.model.fit(features)
        self.is_fitted = True

    def detect_anomalies(self, recent_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Evaluates recent data and flags anomalies.
        Returns the subset of recent_data that are classified as anomalies.
        """
        if not self.is_fitted or not recent_data:
            return []
            
        df = pd.DataFrame(recent_data)
        features = self._extract_features(df)
        
        # Predict returns -1 for outliers and 1 for inliers
        predictions = self.model.predict(features)
        
        anomalies = []
        for idx, pred in enumerate(predictions):
            if pred == -1:
                anomalies.append(recent_data[idx])
                
        return anomalies

if __name__ == "__main__":
    # Simple dummy test
    detector = AnomalyDetector(contamination=0.1)
    
    # Generate some normal data with a diurnal pattern
    import datetime
    base_time = datetime.datetime.now()
    normal_data = []
    for i in range(100):
        ts = base_time + datetime.timedelta(hours=i)
        # Baseline ~ 50, plus a diurnal cycle
        val = 50 + 20 * np.sin(i * 2 * np.pi / 24) + np.random.normal(0, 5)
        normal_data.append({"ts": ts.isoformat(), "value": val})
        
    detector.fit(normal_data)
    
    # Generate recent data with an obvious spike
    recent_data = [
        {"ts": (base_time + datetime.timedelta(hours=101)).isoformat(), "value": 50},
        {"ts": (base_time + datetime.timedelta(hours=102)).isoformat(), "value": 55},
        {"ts": (base_time + datetime.timedelta(hours=103)).isoformat(), "value": 300}, # SPIKE!
        {"ts": (base_time + datetime.timedelta(hours=104)).isoformat(), "value": 45},
    ]
    
    anomalies = detector.detect_anomalies(recent_data)
    print("Detected anomalies:", anomalies)
