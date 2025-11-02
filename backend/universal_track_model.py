import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
import joblib
import os
from pathlib import Path

class UniversalTrackModel:
    def __init__(self, track_name):
        self.track_name = track_name
        self.sector_models = {}
        self.track_characteristics = self.get_track_characteristics(track_name)
    
    def get_track_characteristics(self, track_name):
        """Define characteristics for each track"""
        characteristics = {
            'barber': {
                'sector_1': {'length': 0.64, 'turns': ['T1', 'T2', 'T3'], 'type': 'Technical', 'tire_stress': 'High'},
                'sector_2': {'length': 0.98, 'turns': ['T4', 'T5'], 'type': 'High Speed', 'tire_stress': 'Medium'},
                'sector_3': {'length': 0.66, 'turns': ['T6', 'T7'], 'type': 'Mixed', 'tire_stress': 'Low-Medium'}
            },
            'cota': {
                'sector_1': {'length': 1.2, 'turns': ['T1', 'T2', 'T3'], 'type': 'High Speed', 'tire_stress': 'Medium'},
                'sector_2': {'length': 1.1, 'turns': ['T4', 'T5', 'T6'], 'type': 'Technical', 'tire_stress': 'High'},
                'sector_3': {'length': 0.9, 'turns': ['T7', 'T8'], 'type': 'Mixed', 'tire_stress': 'Medium'}
            },
            'road america': {
                'sector_1': {'length': 1.8, 'turns': ['T1', 'T2', 'T3'], 'type': 'High Speed', 'tire_stress': 'Low'},
                'sector_2': {'length': 1.5, 'turns': ['T4', 'T5'], 'type': 'Technical', 'tire_stress': 'High'},
                'sector_3': {'length': 1.2, 'turns': ['T6', 'T7', 'T8'], 'type': 'Mixed', 'tire_stress': 'Medium'}
            },
            'sebring': {
                'sector_1': {'length': 1.1, 'turns': ['T1', 'T2'], 'type': 'Bumpy', 'tire_stress': 'Very High'},
                'sector_2': {'length': 1.3, 'turns': ['T3', 'T4', 'T5'], 'type': 'High Speed', 'tire_stress': 'Medium'},
                'sector_3': {'length': 0.9, 'turns': ['T6', 'T7'], 'type': 'Technical', 'tire_stress': 'High'}
            },
            'sonoma': {
                'sector_1': {'length': 0.8, 'turns': ['T1', 'T2', 'T3'], 'type': 'Elevation', 'tire_stress': 'High'},
                'sector_2': {'length': 0.7, 'turns': ['T4', 'T5'], 'type': 'Technical', 'tire_stress': 'Very High'},
                'sector_3': {'length': 0.9, 'turns': ['T6', 'T7', 'T8'], 'type': 'Mixed', 'tire_stress': 'Medium'}
            },
            'vir': {
                'sector_1': {'length': 1.2, 'turns': ['T1', 'T2'], 'type': 'High Speed', 'tire_stress': 'Low'},
                'sector_2': {'length': 1.0, 'turns': ['T3', 'T4', 'T5'], 'type': 'Technical', 'tire_stress': 'High'},
                'sector_3': {'length': 0.8, 'turns': ['T6', 'T7'], 'type': 'Elevation', 'tire_stress': 'Medium'}
            }
        }
        return characteristics.get(track_name, characteristics['barber'])  # Default to Barber
    
    def generate_demo_data(self):
        """Generate realistic demo data for any track"""
        np.random.seed(42)
        
        data = []
        base_times = {
            'barber': {'sector_1': 42.5, 'sector_2': 38.2, 'sector_3': 40.1},
            'cota': {'sector_1': 48.2, 'sector_2': 45.1, 'sector_3': 42.3},
            'road america': {'sector_1': 52.8, 'sector_2': 48.5, 'sector_3': 44.5},
            'sebring': {'sector_1': 46.3, 'sector_2': 43.8, 'sector_3': 41.2},
            'sonoma': {'sector_1': 38.7, 'sector_2': 36.2, 'sector_3': 34.8},
            'vir': {'sector_1': 44.5, 'sector_2': 41.3, 'sector_3': 39.2}
        }
        
        track_base = base_times.get(self.track_name, base_times['barber'])
        
        for lap in range(1, 51):
            for sector in ['sector_1', 'sector_2', 'sector_3']:
                base_time = track_base[sector] + np.random.normal(0, 0.5)
                
                # Add degradation over laps
                degraded_time = base_time + (lap * 0.03)
                
                data.append({
                    'lap_number': lap,
                    'sector': sector,
                    'sector_time': degraded_time,
                    'air_temp': 25 + np.random.normal(0, 2),
                    'track_temp': 40 + np.random.normal(0, 3),
                    'tire_compound_code': np.random.choice([1, 2, 3])  # 1=Soft, 2=Medium, 3=Hard
                })
        
        return pd.DataFrame(data)
    
    def train_sector_models(self, historical_data=None):
        """Train separate models for each sector"""
        print(f"🏎️ Training {self.track_name.upper()}-Specific Sector Models...")
        
        if historical_data is None:
            historical_data = self.generate_demo_data()
        
        for sector in ['sector_1', 'sector_2', 'sector_3']:
            # Filter data for this sector
            sector_data = historical_data[historical_data['sector'] == sector]
            
            if len(sector_data) < 10:
                print(f"⚠️  Insufficient data for {sector}, using fallback")
                continue
            
            features = ['lap_number', 'air_temp', 'track_temp', 'tire_compound_code']
            X = sector_data[features]
            y = sector_data['sector_time']
            
            print(f"📊 Training {sector} with {len(sector_data)} samples")
            
            # Train model
            model = RandomForestRegressor(n_estimators=50, random_state=42)
            model.fit(X, y)
            
            self.sector_models[sector] = model
            print(f"✅ {sector} model trained on {len(sector_data)} samples")
    
    def predict_sector_performance(self, current_conditions):
        """Predict performance for each sector based on current conditions"""
        predictions = {}
        
        for sector, characteristics in self.track_characteristics.items():
            if sector in self.sector_models:
                # Prepare input features
                features = np.array([[
                    current_conditions['lap_number'],
                    current_conditions['air_temp'],
                    current_conditions['track_temp'],
                    current_conditions['tire_compound_code']
                ]])
                
                # Make prediction
                predicted_time = self.sector_models[sector].predict(features)[0]
                predictions[sector] = {
                    'predicted_time': predicted_time,
                    'characteristics': characteristics,
                    'risk_level': self.assess_sector_risk(sector, current_conditions)
                }
            else:
                # Fallback prediction
                predictions[sector] = self.fallback_sector_prediction(sector, current_conditions)
        
        return predictions
    
    def assess_sector_risk(self, sector, conditions):
        """Assess risk level for each sector"""
        base_risk = {
            'sector_1': 'Medium',
            'sector_2': 'Medium', 
            'sector_3': 'Low'
        }
        
        # Track-specific risk adjustments
        risk_adjustments = {
            'sebring': {'sector_1': 'Very High'},  # Bumpy section
            'sonoma': {'sector_2': 'Very High'},   # Very technical
            'barber': {'sector_1': 'High'}         # Technical start
        }
        
        track_risk = risk_adjustments.get(self.track_name, {})
        risk_level = track_risk.get(sector, base_risk[sector])
        
        # Weather adjustments
        if conditions['track_temp'] > 35 and 'Technical' in self.track_characteristics[sector]['type']:
            return 'High'
        elif conditions['track_temp'] < 20 and 'High Speed' in self.track_characteristics[sector]['type']:
            return 'High'
        
        return risk_level
    
    def fallback_sector_prediction(self, sector, conditions):
        """Provide intelligent fallback predictions"""
        base_times = {
            'barber': {'sector_1': 42.5, 'sector_2': 38.2, 'sector_3': 40.1},
            'cota': {'sector_1': 48.2, 'sector_2': 45.1, 'sector_3': 42.3},
            'road america': {'sector_1': 52.8, 'sector_2': 48.5, 'sector_3': 44.5},
            'sebring': {'sector_1': 46.3, 'sector_2': 43.8, 'sector_3': 41.2},
            'sonoma': {'sector_1': 38.7, 'sector_2': 36.2, 'sector_3': 34.8},
            'vir': {'sector_1': 44.5, 'sector_2': 41.3, 'sector_3': 39.2}
        }
        
        track_base = base_times.get(self.track_name, base_times['barber'])
        base_time = track_base[sector]
        
        # Adjust for conditions
        temp_adjustment = (conditions['track_temp'] - 25) * 0.1
        lap_adjustment = conditions['lap_number'] * 0.05
        
        predicted_time = base_time + temp_adjustment + lap_adjustment
        
        return {
            'predicted_time': predicted_time,
            'characteristics': self.track_characteristics[sector],
            'risk_level': self.assess_sector_risk(sector, conditions),
            'note': 'Fallback prediction'
        }
    
    def get_track_strategy_insights(self, predictions):
        """Generate track-specific strategy insights"""
        insights = []
        
        # Analyze sector predictions
        sector_times = [predictions[s]['predicted_time'] for s in predictions.keys()]
        total_time = sum(sector_times)
        
        # Track-specific insights
        track_insights = {
            'barber': self.get_barber_insights,
            'cota': self.get_cota_insights,
            'road america': self.get_road_america_insights,
            'sebring': self.get_sebring_insights,
            'sonoma': self.get_sonoma_insights,
            'vir': self.get_vir_insights
        }
        
        insights_generator = track_insights.get(self.track_name, self.get_generic_insights)
        insights.extend(insights_generator(predictions, total_time))
        
        return insights
    
    def get_barber_insights(self, predictions, total_time):
        insights = []
        s1, s2, s3 = predictions['sector_1']['predicted_time'], predictions['sector_2']['predicted_time'], predictions['sector_3']['predicted_time']
        
        if s1 > 44.0: insights.append("🚨 **Sector 1 Alert**: High tire wear in technical section")
        if s2 > 39.5: insights.append("💨 **Sector 2 Opportunity**: Check wing settings for high-speed section")
        if s3 < 39.8: insights.append("🎯 **Sector 3 Strength**: Good final sector for overtaking")
        if total_time > 122.0: insights.append("🛑 **Overall**: Consider earlier pit stop")
        
        return insights
    
    def get_cota_insights(self, predictions, total_time):
        insights = []
        s1, s2, s3 = predictions['sector_1']['predicted_time'], predictions['sector_2']['predicted_time'], predictions['sector_3']['predicted_time']
        
        if s1 > 50.0: insights.append("🚨 **Sector 1**: High-speed section losing time - check aero")
        if s2 > 47.0: insights.append("⚠️ **Sector 2**: Technical section needs smoother inputs")
        if total_time > 136.0: insights.append("🛑 **Overall**: High degradation in technical sections")
        
        return insights
    
    def get_road_america_insights(self, predictions, total_time):
        insights = []
        s1, s2, s3 = predictions['sector_1']['predicted_time'], predictions['sector_2']['predicted_time'], predictions['sector_3']['predicted_time']
        
        if s1 > 54.0: insights.append("💨 **Sector 1**: Long straight efficiency low")
        if s2 > 50.0: insights.append("🚨 **Sector 2**: Carousel section tire wear high")
        if total_time < 146.0: insights.append("✅ **Overall**: Excellent long-track performance")
        
        return insights
    
    def get_sebring_insights(self, predictions, total_time):
        insights = []
        s1, s2, s3 = predictions['sector_1']['predicted_time'], predictions['sector_2']['predicted_time'], predictions['sector_3']['predicted_time']
        
        if s1 > 48.0: insights.append("🔄 **Sector 1**: Bumpy section - adjust suspension")
        if s3 > 43.0: insights.append("⚠️ **Sector 3**: Technical section losing time")
        if total_time > 128.0: insights.append("🛑 **Overall**: High bump-induced degradation")
        
        return insights
    
    def get_sonoma_insights(self, predictions, total_time):
        insights = []
        s1, s2, s3 = predictions['sector_1']['predicted_time'], predictions['sector_2']['predicted_time'], predictions['sector_3']['predicted_time']
        
        if s2 > 38.0: insights.append("🚨 **Sector 2**: Very technical section - smooth inputs needed")
        if s3 < 36.0: insights.append("🎯 **Sector 3**: Excellent elevation management")
        if total_time < 110.0: insights.append("🏆 **Overall**: Great short-track pace")
        
        return insights
    
    def get_vir_insights(self, predictions, total_time):
        insights = []
        s1, s2, s3 = predictions['sector_1']['predicted_time'], predictions['sector_2']['predicted_time'], predictions['sector_3']['predicted_time']
        
        if s1 > 46.0: insights.append("💨 **Sector 1**: High-speed section optimization needed")
        if s2 > 43.0: insights.append("🚨 **Sector 2**: Technical esses losing time")
        if total_time > 118.0: insights.append("⚠️ **Overall**: Monitor elevation changes")
        
        return insights
    
    def get_generic_insights(self, predictions, total_time):
        return ["📊 Track analysis loaded - monitor sector times for optimal strategy"]

def create_all_track_models():
    """Create and save models for all tracks"""
    tracks = ['barber', 'cota', 'road america', 'sebring', 'sonoma', 'vir']
    
    for track in tracks:
        print(f"\n🎯 Creating model for {track.upper()}...")
        model = UniversalTrackModel(track)
        model.train_sector_models()
        
        # Save model
        filename = f'backend/{track}_specific_model.pkl'
        joblib.dump(model, filename)
        print(f"💾 Saved {track} model to {filename}")

if __name__ == "__main__":
    create_all_track_models()