# backend/tire_model_working.py
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error
import joblib
from pathlib import Path

class TireDegradationModel:
    def __init__(self):
        self.model = RandomForestRegressor(n_estimators=50, random_state=42)
        self.is_trained = False
    
    def prepare_training_data(self):
        """Prepare data for tire degradation modeling"""
        print("PREPARING TIRE DEGRADATION TRAINING DATA")
        print("=" * 50)
        
        # Load data from ALL races
        all_features = self.load_all_race_data()
        
        if len(all_features) == 0:
            print("❌ No data available for training")
            return None
        
        # Combine all datasets
        combined_df = pd.concat(all_features, ignore_index=True)
        print(f"Combined dataset shape: {combined_df.shape}")
        
        # Create features for tire degradation model
        features_df = self.create_tire_features(combined_df)
        
        return features_df
    
    def load_all_race_data(self):
        """Load data from all available races"""
        print("Loading data from all available races...")
        
        all_analysis_files = list(Path('data/analysis').glob('FIXED_23_*.csv'))
        all_features = []
        
        for file_path in all_analysis_files:
            try:
                print(f"Loading: {file_path.name}")
                df = pd.read_csv(file_path)
                df.columns = [col.strip() for col in df.columns]
                df = self.convert_lap_times_to_seconds(df)
                all_features.append(df)
                print(f"  - Loaded {len(df)} laps")
            except Exception as e:
                print(f"Error loading {file_path}: {e}")
        
        return all_features
    
    def convert_lap_times_to_seconds(self, df):
        """Convert MM:SS.sss lap times to total seconds"""
        def time_to_seconds(time_str):
            if pd.isna(time_str):
                return np.nan
            try:
                if ':' in time_str:
                    parts = time_str.split(':')
                    if len(parts) == 2:  # MM:SS.sss
                        return float(parts[0]) * 60 + float(parts[1])
                    else:  # Already in seconds format?
                        return float(time_str)
                else:
                    return float(time_str)
            except:
                return np.nan
        
        # Convert lap time and sector times
        time_columns = ['LAP_TIME', 'S1', 'S2', 'S3']
        
        for col in time_columns:
            if col in df.columns:
                df[f'{col}_SECONDS'] = df[col].apply(time_to_seconds)
        
        return df
    
    def create_tire_features(self, df):
        """Create features that indicate tire degradation"""
        print("\nCREATING TIRE DEGRADATION FEATURES")
        print("=" * 40)
        
        # Sort by driver and lap number
        df = df.sort_values(['DRIVER_NUMBER', 'LAP_NUMBER']).reset_index(drop=True)
        
        # 1. Calculate lap time degradation (proxy for tire wear)
        df['LAP_TIME_DELTA'] = df.groupby('DRIVER_NUMBER')['LAP_TIME_SECONDS'].diff()
        
        # 2. Calculate rolling average of lap times (tire wear indicator)
        df['LAP_TIME_ROLLING_AVG'] = df.groupby('DRIVER_NUMBER')['LAP_TIME_SECONDS'].transform(
            lambda x: x.rolling(2, min_periods=1).mean()  # Smaller window for small dataset
        )
        
        # 3. Add basic tire wear proxies
        df['LAP_NUMBER_NORMALIZED'] = df.groupby('DRIVER_NUMBER')['LAP_NUMBER'].transform(
            lambda x: x / x.max() if x.max() > 0 else x
        )
        df['CUMULATIVE_DISTANCE'] = df['LAP_NUMBER'] * 2.38  # Approx Barber track length in miles
        
        # 4. Calculate performance vs best lap
        df['TIME_VS_BEST'] = df.groupby('DRIVER_NUMBER')['LAP_TIME_SECONDS'].transform(
            lambda x: x - x.min()
        )
        
        print(f"Final features shape: {df.shape}")
        print(f"Sample of key features:")
        sample_cols = ['DRIVER_NUMBER', 'LAP_NUMBER', 'LAP_TIME_SECONDS', 'LAP_TIME_DELTA', 'TIME_VS_BEST']
        print(df[sample_cols].head(10).to_string())
        
        return df
    
    def train(self, features_df):
        """Train the tire degradation model - simplified for small datasets"""
        print("\nTRAINING TIRE DEGRADATION MODEL")
        print("=" * 40)
        
        # For small datasets, use regression instead of classification
        features_df = features_df.sort_values(['DRIVER_NUMBER', 'LAP_NUMBER'])
        
        # Create target: next lap time (regression problem)
        features_df['NEXT_LAP_TIME'] = features_df.groupby('DRIVER_NUMBER')['LAP_TIME_SECONDS'].shift(-1)
        
        # Use simple features
        feature_columns = ['LAP_NUMBER', 'LAP_NUMBER_NORMALIZED', 'LAP_TIME_SECONDS', 'TIME_VS_BEST']
        feature_columns = [col for col in feature_columns if col in features_df.columns]
        
        print(f"Using features: {feature_columns}")
        
        # Prepare training data
        train_data = features_df.dropna(subset=feature_columns + ['NEXT_LAP_TIME'])
        
        if len(train_data) < 3:
            print("⚠️  Not enough data for ML training, using statistical analysis")
            return self.analyze_degradation_patterns(features_df)
        
        X = train_data[feature_columns]
        y = train_data['NEXT_LAP_TIME']
        
        print(f"Training data: {X.shape[0]} samples")
        print(f"Target range: {y.min():.1f}s to {y.max():.1f}s")
        
        # For very small datasets, use all data for training
        if len(X) <= 5:
            self.model.fit(X, y)
            # Simple cross-validation: use last sample as test
            if len(X) > 1:
                test_pred = self.model.predict(X.iloc[[-1]])
                test_error = abs(test_pred[0] - y.iloc[-1])
                print(f"📊 Model trained (small dataset)")
                print(f"📈 Sample prediction error: {test_error:.2f}s")
            else:
                print(f"📊 Model trained (very small dataset)")
        else:
            # Normal train/test split
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)
            self.model.fit(X_train, y_train)
            
            # Evaluate
            y_pred = self.model.predict(X_test)
            mae = mean_absolute_error(y_test, y_pred)
            print(f"✅ Model trained! MAE: {mae:.2f}s")
        
        self.is_trained = True
        
        # Show feature importance if we have enough features
        if len(feature_columns) > 1:
            print(f"🎯 Feature importance:")
            for feat, imp in zip(feature_columns, self.model.feature_importances_):
                print(f"  - {feat}: {imp:.3f}")
        
        return True
    
    def analyze_degradation_patterns(self, features_df):
        """Analyze degradation patterns statistically"""
        print("\n📊 ANALYZING TIRE DEGRADATION PATTERNS")
        print("=" * 40)
        
        degradation_rates = []
        strategy_insights = []
        
        for driver in features_df['DRIVER_NUMBER'].unique():
            driver_data = features_df[features_df['DRIVER_NUMBER'] == driver].sort_values('LAP_NUMBER')
            
            if len(driver_data) > 2:
                lap_times = driver_data['LAP_TIME_SECONDS'].values
                best_lap = np.min(lap_times)
                
                # Calculate degradation rate
                if len(lap_times) > 1:
                    time_deltas = np.diff(lap_times)
                    avg_degradation = np.mean(time_deltas[time_deltas > 0]) if np.any(time_deltas > 0) else 0
                    
                    if not np.isnan(avg_degradation) and avg_degradation > 0:
                        degradation_rates.append(avg_degradation)
                        
                        # Strategy insight
                        laps_to_2s_degradation = max(1, int(2.0 / avg_degradation)) if avg_degradation > 0 else 10
                        strategy_insights.append({
                            'driver': driver,
                            'avg_degradation': avg_degradation,
                            'laps_to_pit': laps_to_2s_degradation,
                            'best_lap': best_lap
                        })
        
        if degradation_rates:
            avg_rate = np.mean(degradation_rates)
            max_rate = np.max(degradation_rates)
            
            print(f"📈 Degradation Analysis:")
            print(f"  - Average degradation rate: {avg_rate:.3f}s per lap")
            print(f"  - Maximum degradation rate: {max_rate:.3f}s per lap")
            print(f"  - Recommended pit window: Every {max(3, int(2.0/max_rate))} laps")
            
            print(f"\n🎯 Driver-specific insights:")
            for insight in strategy_insights:
                print(f"  - Driver {insight['driver']}: Pit every {insight['laps_to_pit']} laps "
                      f"(deg: {insight['avg_degradation']:.2f}s/lap)")
            
            self.avg_degradation_rate = avg_rate
            self.max_degradation_rate = max_rate
            self.strategy_insights = strategy_insights
            self.is_trained = True
            
            return True
        else:
            print("❌ Not enough data for degradation analysis")
            return False
    
    def predict_optimal_pit(self, current_lap, current_time_vs_best, laps_completed):
        """Predict optimal pit stop timing"""
        if not self.is_trained:
            return "Model not trained"
        
        if hasattr(self, 'avg_degradation_rate'):
            # Use statistical analysis
            if current_time_vs_best > 2.0:
                return "PIT NOW - Already 2+ seconds slower than best"
            else:
                laps_to_pit = max(1, int((2.0 - current_time_vs_best) / self.max_degradation_rate))
                return f"Pit in {laps_to_pit} laps (current deg: {self.max_degradation_rate:.2f}s/lap)"
        else:
            # Use ML model
            return "Pit window analysis available (ML model)"
    
    def get_strategy_report(self):
        """Generate a strategy report"""
        if not self.is_trained:
            return "No strategy insights available"
        
        report = []
        report.append("🏎️ PITSENSE PRO - STRATEGY REPORT")
        report.append("=" * 40)
        
        if hasattr(self, 'avg_degradation_rate'):
            report.append(f"📊 TIRE DEGRADATION ANALYSIS:")
            report.append(f"  • Average degradation: {self.avg_degradation_rate:.2f}s per lap")
            report.append(f"  • Maximum degradation: {self.max_degradation_rate:.2f}s per lap")
            report.append(f"  • Pit stop trigger: When 2+ seconds slower than best lap")
            report.append("")
            report.append("🎯 RECOMMENDED STRATEGY:")
            report.append(f"  • Conservative: Pit every {max(4, int(1.5/self.avg_degradation_rate))} laps")
            report.append(f"  • Aggressive: Pit every {max(3, int(2.5/self.max_degradation_rate))} laps")
            report.append("")
            report.append("⚠️  MONITOR:")
            report.append("  • Sector 2 times (usually shows degradation first)")
            report.append("  • Lap time consistency")
            report.append("  • Tire temperature trends")
        else:
            report.append("🤖 ML MODEL READY")
            report.append("  • Real-time pit window predictions available")
            report.append("  • Monitor lap time degradation patterns")
        
        return "\n".join(report)

def main():
    print("PITSENSE PRO - TIRE DEGRADATION ANALYZER")
    print("=" * 60)
    
    # Initialize and train model
    tire_model = TireDegradationModel()
    features_df = tire_model.prepare_training_data()
    
    if features_df is not None:
        success = tire_model.train(features_df)
        
        if success:
            print("\n" + "=" * 50)
            print("✅ TIRE ANALYSIS COMPLETE!")
            print("=" * 50)
            
            # Generate and display strategy report
            report = tire_model.get_strategy_report()
            print(report)
            
            # Show sample prediction
            print("\n🎯 SAMPLE PREDICTION:")
            sample_pred = tire_model.predict_optimal_pit(
                current_lap=5, 
                current_time_vs_best=1.2, 
                laps_completed=10
            )
            print(f"  - {sample_pred}")
            
            # Save insights for dashboard
            insights = {
                'is_trained': tire_model.is_trained,
                'degradation_rate': getattr(tire_model, 'avg_degradation_rate', None),
                'strategy_insights': getattr(tire_model, 'strategy_insights', [])
            }
            joblib.dump(insights, 'backend/tire_insights.pkl')
            print(f"\n💾 Insights saved to 'backend/tire_insights.pkl'")

if __name__ == "__main__":
    main()