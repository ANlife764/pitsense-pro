# backend/data_fixer_v2.py
import pandas as pd
import numpy as np
from pathlib import Path

def debug_analysis_file():
    """See the raw structure of the analysis file"""
    print("DEBUGGING ANALYSIS FILE STRUCTURE")
    print("=" * 50)
    
    file_path = 'data/analysis/23_AnalysisEnduranceWithSections_Race 1_Anonymized.CSV'
    
    # Read raw file to see actual structure
    with open(file_path, 'r') as f:
        first_lines = [f.readline().strip() for _ in range(5)]
    
    print("First 3 lines of raw file:")
    for i, line in enumerate(first_lines[:3]):
        print(f"Line {i}: {line}")
    
    # Try different separators
    separators = [';', ',', '\t', '|']
    
    for sep in separators:
        try:
            df = pd.read_csv(file_path, sep=sep, nrows=5)
            print(f"\nTrying separator '{sep}': Shape = {df.shape}")
            print(f"Columns: {df.columns.tolist()}")
            if df.shape[1] > 1:
                print("SUCCESS! Found proper separator")
                return df, sep
        except:
            continue
    
    # If all separators fail, try manual parsing
    print("\nManual parsing required...")
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Split by semicolon for header
    header_line = content.split('\n')[0]
    headers = [h.strip() for h in header_line.split(';')]
    print(f"Manual headers found: {headers}")
    
    # Parse data lines
    data_lines = []
    for line in content.split('\n')[1:]:
        if line.strip():
            values = [v.strip() for v in line.split(';')]
            data_lines.append(values)
    
    df = pd.DataFrame(data_lines, columns=headers)
    print(f"Manual parsing shape: {df.shape}")
    return df, ';'

def fix_analysis_data_properly():
    """Properly fix the analysis data"""
    print("\nFIXING ANALYSIS DATA")
    print("=" * 50)
    
    analysis_files = list(Path('data/analysis').glob('23_*.CSV'))
    
    for file_path in analysis_files:
        print(f"\nProcessing: {file_path.name}")
        
        # Use the debug function to find the right format
        df, separator = debug_analysis_file()
        
        # Clean the data
        df = df.replace('', np.nan).dropna(how='all')
        
        print(f"Final shape: {df.shape}")
        print(f"Final columns: {df.columns.tolist()}")
        
        # Save fixed version
        fixed_path = f"data/analysis/FIXED_{file_path.stem}.csv"
        df.to_csv(fixed_path, index=False)
        print(f"Saved to: {fixed_path}")
        
        # Show what we actually have
        print("\nFirst 2 rows of data:")
        for col in df.columns[:8]:  # Show first 8 columns
            if col in df.columns:
                sample_vals = df[col].head(2).tolist()
                print(f"  {col}: {sample_vals}")

def explore_telemetry_quick():
    """Quick exploration of telemetry parameters"""
    print("\n" + "="*50)
    print("QUICK TELEMETRY EXPLORATION")
    print("="*50)
    
    # Just read the unique parameters first (much faster)
    telemetry_file = 'data/telemetry/R1_barber_telemetry_data.csv'
    
    # Read only the telemetry_name column to see parameters
    telemetry_params = pd.read_csv(telemetry_file, usecols=['telemetry_name'])
    
    unique_params = telemetry_params['telemetry_name'].unique()
    print(f"Found {len(unique_params)} unique telemetry parameters")
    
    print("\nAll telemetry parameters:")
    for param in sorted(unique_params):
        print(f"  - {param}")
    
    # Look for tire-related parameters
    tire_keywords = ['tire', 'tyre', 'pressure', 'temp', 'wear', 'compound']
    tire_params = [p for p in unique_params if any(kw in p.lower() for kw in tire_keywords)]
    
    print(f"\n🚨 TIRE-RELATED PARAMETERS ({len(tire_params)}):")
    for param in tire_params:
        print(f"  ★ {param}")
    
    return unique_params

def check_lap_time_sources():
    """Find where lap time data actually exists"""
    print("\n" + "="*50)
    print("FINDING LAP TIME SOURCES")
    print("="*50)
    
    # Check lap start/end files
    print("Lap start file:")
    lap_start = pd.read_csv('data/lap_data/R1_barber_lap_start.csv', nrows=3)
    print(lap_start.columns.tolist())
    
    print("\nLap end file:")
    lap_end = pd.read_csv('data/lap_data/R1_barber_lap_end.csv', nrows=3)
    print(lap_end.columns.tolist())
    
    # Check if we have timing in telemetry
    telemetry_sample = pd.read_csv('data/telemetry/R1_barber_telemetry_data.csv', nrows=1000)
    if 'session_time' in telemetry_sample.columns:
        print("\nFound session_time in telemetry")
    if 'lap_time' in telemetry_sample.columns:
        print("Found lap_time in telemetry")

if __name__ == "__main__":
    print("PITSENSE PRO - DATA FIXER V2")
    print("=" * 60)
    
    # Run in sequence
    fix_analysis_data_properly()
    telemetry_params = explore_telemetry_quick()
    check_lap_time_sources()
    
    print("\n🎯 NEXT ACTIONS:")
    print("1. We'll see the actual column names from analysis files")
    print("2. Identify ALL telemetry parameters available")
    print("3. Find the true source of lap timing data")