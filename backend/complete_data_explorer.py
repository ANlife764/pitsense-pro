# backend/complete_data_explorer.py
import pandas as pd
import os
from pathlib import Path

def explore_all_data():
    print("=== PITSENSE PRO - COMPLETE DATA EXPLORATION ===\n")
    
    # 1. LAP TIME DATA (Most Important)
    print("1. 🏁 LAP TIME DATA ANALYSIS")
    print("=" * 50)
    
    lap_time_files = [
        'data/lap_data/R1_barber_lap_time.csv',
        'data/lap_data/R2_barber_lap_time.csv'
    ]
    
    for file_path in lap_time_files:
        if os.path.exists(file_path):
            print(f"\n📊 Analyzing: {Path(file_path).name}")
            df = pd.read_csv(file_path)
            print(f"   Shape: {df.shape}")
            print(f"   Columns: {df.columns.tolist()}")
            print(f"   Data Types:\n{df.dtypes}")
            print(f"   Sample Data:")
            print(df.head(2).to_string())
            
            # Key metrics
            if 'LapTime' in df.columns:
                print(f"   LapTime range: {df['LapTime'].min()} to {df['LapTime'].max()}")
            if 'LapNumber' in df.columns:
                print(f"   Laps: {df['LapNumber'].min()} to {df['LapNumber'].max()}")

    # 2. TELEMETRY DATA (AI Goldmine)
    print("\n2. 🔬 TELEMETRY DATA ANALYSIS")
    print("=" * 50)
    
    telemetry_files = [
        'data/telemetry/R1_barber_telemetry_data.csv',
        'data/telemetry/R2_barber_telemetry_data.csv'
    ]
    
    for file_path in telemetry_files:
        if os.path.exists(file_path):
            print(f"\n📡 Analyzing: {Path(file_path).name}")
            df = pd.read_csv(file_path)
            print(f"   Shape: {df.shape}")
            print(f"   Columns: {df.columns.tolist()}")
            print(f"   Sample Data:")
            print(df.head(3).to_string())
            
            # Check for key parameters
            if 'Parameter' in df.columns:
                print(f"\n   Unique Parameters: {df['Parameter'].unique()}")
            if 'Value' in df.columns:
                print(f"   Value range: {df['Value'].min()} to {df['Value'].max()}")

    # 3. ANALYSIS DATA (Race Stints)
    print("\n3. 📈 RACE ANALYSIS DATA")
    print("=" * 50)
    
    analysis_files = list(Path('data/analysis').glob('*.CSV'))
    for file_path in analysis_files[:2]:  # Just first 2 to avoid overload
        print(f"\n📈 Analyzing: {file_path.name}")
        df = pd.read_csv(file_path)
        print(f"   Shape: {df.shape}")
        print(f"   Columns: {df.columns.tolist()}")
        print(f"   Sample:")
        print(df.head(2).to_string())

    # 4. QUICK CHECK OTHER CATEGORIES
    print("\n4. 📋 DATA SUMMARY")
    print("=" * 50)
    
    categories = {
        'lap_data': 'Lap Timing Files',
        'telemetry': 'Telemetry Sensor Files', 
        'results': 'Race Results Files',
        'analysis': 'Race Analysis Files'
    }
    
    for folder, description in categories.items():
        files = list(Path(f'data/{folder}').glob('*.*'))
        print(f"\n{description}: {len(files)} files")
        for f in files[:3]:  # Show first 3 files
            print(f"   - {f.name}")

def check_data_relationships():
    """Check how different datasets connect"""
    print("\n5. 🔗 DATA RELATIONSHIPS")
    print("=" * 50)
    
    # Check common identifiers across datasets
    lap_time = pd.read_csv('data/lap_data/R1_barber_lap_time.csv')
    telemetry = pd.read_csv('data/telemetry/R1_barber_telemetry_data.csv')
    
    print("Lap Time columns:", lap_time.columns.tolist())
    print("Telemetry columns:", telemetry.columns.tolist())
    
    # Look for common keys (Driver, LapNumber, Session, etc.)
    common_cols = set(lap_time.columns) & set(telemetry.columns)
    print(f"Common columns between lap time and telemetry: {common_cols}")

if __name__ == "__main__":
    explore_all_data()
    check_data_relationships()