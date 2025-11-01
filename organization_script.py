# backend/organize_data.py
import os
import shutil
import pandas as pd
from pathlib import Path

def organize_racing_data():
    base_path = Path('data')
    
    # Map file patterns to destination folders
    file_patterns = {
        'lap_time.csv': 'lap_data',
        'lap_start.csv': 'lap_data', 
        'lap_end.csv': 'lap_data',
        'telemetry_data.csv': 'telemetry',
        'Results': 'results',
        'Weather': 'analysis',
        'Analysis': 'analysis',
        'Best 10 Laps': 'results'
    }
    
    # Track what we find
    found_files = []
    
    # Scan all track folders and root
    search_folders = ['barber', 'COTA', 'Road America', 'Sebring', 'Sonoma', 'VIR', '']
    
    for folder in search_folders:
        folder_path = base_path / folder if folder else base_path
        
        if not folder_path.exists():
            continue
            
        print(f"\n=== Searching in {folder_path} ===")
        
        for file_path in folder_path.glob('*.*'):
            if file_path.is_file():
                print(f"Found: {file_path.name}")
                found_files.append(str(file_path))
                
                # Determine destination based on filename
                destination = 'raw_files'  # default
                for pattern, dest_folder in file_patterns.items():
                    if pattern.lower() in file_path.name.lower():
                        destination = dest_folder
                        break
                
                # Create destination folder
                dest_path = base_path / destination
                dest_path.mkdir(exist_ok=True)
                
                # Copy file to organized location
                try:
                    shutil.copy2(file_path, dest_path / file_path.name)
                    print(f"  → Copied to: {destination}/{file_path.name}")
                except Exception as e:
                    print(f"  → Error copying: {e}")
    
    print(f"\n=== ORGANIZATION COMPLETE ===")
    print(f"Found {len(found_files)} files total")
    
    # Show what we have in each category
    for category in ['lap_data', 'telemetry', 'results', 'analysis']:
        category_path = base_path / category
        if category_path.exists():
            files = list(category_path.glob('*.*'))
            print(f"\n{category.upper()} ({len(files)} files):")
            for f in files:
                print(f"  - {f.name}")

if __name__ == "__main__":
    organize_racing_data()