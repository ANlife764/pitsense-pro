# backend/multi_track_analyzer.py
import pandas as pd
import numpy as np
import os
from pathlib import Path
import joblib

class MultiTrackAnalyzer:
    def __init__(self):
        self.track_data = {}
        self.track_profiles = {}
    
    def analyze_all_tracks(self):
        """Analyze data from all available tracks"""
        print("COMPREHENSIVE TRACK ANALYSIS")
        print("=" * 50)
        
        # Discover all tracks with data
        tracks = self.discover_tracks()
        print(f"Found {len(tracks)} tracks with data: {list(tracks.keys())}")
        
        for track_name, track_info in tracks.items():
            if track_name == '__MACOSX':  # Skip system files
                continue
            print(f"\n📊 Analyzing {track_name.upper()}...")
            profile = self.analyze_track(track_name, track_info)
            if profile:
                self.track_profiles[track_name] = profile
    
    def discover_tracks(self):
        """Discover all tracks that have data"""
        tracks = {}
        data_path = Path("data")
        
        for item in data_path.iterdir():
            if item.is_dir() and item.name not in ['analysis', 'lap_data', 'telemetry', 'results', 'raw_files']:
                track_name = item.name
                tracks[track_name] = {
                    'path': item,
                    'has_lap_times': len(list(item.glob('*lap_time*.csv'))) > 0,
                    'has_telemetry': len(list(item.glob('*telemetry*.csv'))) > 0,
                    'has_analysis': len(list(item.glob('*Analysis*.csv'))) > 0,
                    'races': []
                }
        
        return tracks
    
    def analyze_track(self, track_name, track_info):
        """Analyze a specific track's characteristics"""
        print(f"  📁 Data available:")
        print(f"     - Lap times: {track_info['has_lap_times']}")
        print(f"     - Telemetry: {track_info['has_telemetry']}")
        print(f"     - Analysis files: {track_info['has_analysis']}")
        
        # Initialize default values
        avg_lap_time = 100.0
        degradation_rate = 0.8
        pit_start, pit_end = 15, 18
        data_points = 0
        status = 'ESTIMATED'
        
        # Try to get actual data
        lap_time_data = self.get_lap_time_data(track_info['path'])
        analysis_data = self.get_analysis_data(track_info['path'])
        
        if lap_time_data is not None:
            avg_lap_time = lap_time_data['lap_time_seconds'].mean()
            degradation_rate = self.calculate_degradation_rate(lap_time_data)
            data_points = len(lap_time_data)
            status = 'ANALYZED'
        elif analysis_data is not None:
            avg_lap_time = analysis_data['LAP_TIME_SECONDS'].mean()
            degradation_rate = self.calculate_degradation_rate(analysis_data)
            data_points = len(analysis_data)
            status = 'ANALYZED'
        else:
            # Use track-specific estimates
            track_estimates = {
                'barber': (105.0, 0.8, 15, 18),
                'cota': (135.0, 1.2, 12, 15),
                'road america': (145.0, 0.6, 18, 22),
                'sebring': (125.0, 1.5, 10, 13),
                'sonoma': (95.0, 0.9, 14, 17),
                'vir': (115.0, 0.7, 16, 20)
            }
            
            estimate = track_estimates.get(track_name.lower(), (100.0, 0.8, 15, 18))
            avg_lap_time = estimate[0]
            degradation_rate = estimate[1]
            pit_start, pit_end = estimate[2], estimate[3]
            status = 'ESTIMATED'
        
        profile = {
            'track_name': track_name,
            'avg_lap_time': avg_lap_time,
            'degradation_rate': degradation_rate,
            'pit_window_start': pit_start,
            'pit_window_end': pit_end,
            'data_points': data_points,
            'status': status,
            'has_lap_times': track_info['has_lap_times'],
            'has_telemetry': track_info['has_telemetry'],
            'races': track_info['races']
        }
        
        print(f"  📈 Track profile:")
        print(f"     - Avg lap: {profile['avg_lap_time']:.1f}s")
        print(f"     - Degradation: {profile['degradation_rate']:.2f}s/lap")
        print(f"     - Pit window: Lap {profile['pit_window_start']}-{profile['pit_window_end']}")
        print(f"     - Data quality: {profile['status']} ({data_points} laps)")
        
        return profile
    
    def get_lap_time_data(self, track_path):
        """Extract lap time data from track folder"""
        lap_files = list(track_path.glob('*lap_time*.csv'))
        if not lap_files:
            return None
        
        try:
            # Use the first lap time file found
            lap_file = lap_files[0]
            print(f"     📄 Reading lap time file: {lap_file.name}")
            df = pd.read_csv(lap_file)
            
            # Different file might have different structures - try to find lap time column
            time_columns = [col for col in df.columns if 'time' in col.lower() or 'lap' in col.lower()]
            
            if time_columns:
                # Simple conversion - assume first time-like column is lap time
                time_col = time_columns[0]
                sample_value = str(df[time_col].iloc[0]) if len(df) > 0 else ""
                
                if ':' in sample_value:
                    # Convert MM:SS.sss to seconds
                    df['lap_time_seconds'] = df[time_col].apply(
                        lambda x: float(x.split(':')[0]) * 60 + float(x.split(':')[1]) if ':' in str(x) else float(x)
                    )
                else:
                    df['lap_time_seconds'] = pd.to_numeric(df[time_col], errors='coerce')
                
                result = df.dropna(subset=['lap_time_seconds'])
                print(f"     ✅ Found {len(result)} lap times")
                return result
        
        except Exception as e:
            print(f"     ⚠️  Error reading lap time file: {e}")
        
        return None
    
    def get_analysis_data(self, track_path):
        """Extract data from analysis files"""
        analysis_files = list(track_path.glob('*Analysis*.csv'))
        if not analysis_files:
            return None
        
        try:
            analysis_file = analysis_files[0]
            print(f"     📄 Reading analysis file: {analysis_file.name}")
            df = pd.read_csv(analysis_file, sep=';')
            df.columns = [col.strip() for col in df.columns]
            
            if 'LAP_TIME' in df.columns:
                df['LAP_TIME_SECONDS'] = df['LAP_TIME'].apply(
                    lambda x: float(x.split(':')[0]) * 60 + float(x.split(':')[1]) if ':' in str(x) else float(x)
                )
                result = df.dropna(subset=['LAP_TIME_SECONDS'])
                print(f"     ✅ Found {len(result)} analysis records")
                return result
        
        except Exception as e:
            print(f"     ⚠️  Error reading analysis file: {e}")
        
        return None
    
    def calculate_degradation_rate(self, df):
        """Calculate tire degradation rate from lap times"""
        if 'lap_time_seconds' in df.columns:
            times = df['lap_time_seconds'].values
        elif 'LAP_TIME_SECONDS' in df.columns:
            times = df['LAP_TIME_SECONDS'].values
        else:
            return 0.8
        
        if len(times) < 3:
            return 0.8
        
        # Calculate degradation as average increase per lap
        diffs = np.diff(times)
        positive_diffs = diffs[diffs > 0]  # Only consider performance drops
        
        if len(positive_diffs) > 0:
            return np.mean(positive_diffs)
        
        return 0.8
    
    def generate_comprehensive_report(self):
        """Generate detailed multi-track report"""
        print("\n" + "=" * 70)
        print("COMPREHENSIVE MULTI-TRACK RACING ANALYTICS REPORT")
        print("=" * 70)
        
        if not self.track_profiles:
            print("❌ No track profiles generated")
            return None
        
        report_data = []
        for track, profile in self.track_profiles.items():
            report_data.append({
                'Track': track.upper(),
                'Status': profile['status'],
                'Lap Data': '✅' if profile['has_lap_times'] else '❌',
                'Telemetry': '✅' if profile['has_telemetry'] else '❌',
                'Avg Lap Time': f"{profile['avg_lap_time']:.1f}s",
                'Tire Degradation': f"{profile['degradation_rate']:.2f}s/lap",
                'Optimal Pit Window': f"Lap {profile['pit_window_start']}-{profile['pit_window_end']}",
                'Data Quality': f"{profile['data_points']} laps"
            })
        
        report_df = pd.DataFrame(report_data)
        print(report_df.to_string(index=False))
        
        # Strategy insights
        print("\n🎯 STRATEGY INSIGHTS ACROSS TRACKS:")
        if len(self.track_profiles) > 1:
            fastest_track = min(self.track_profiles.values(), key=lambda x: x['avg_lap_time'])
            highest_degradation = max(self.track_profiles.values(), key=lambda x: x['degradation_rate'])
            
            print(f"• Fastest Track: {fastest_track['track_name'].upper()} ({fastest_track['avg_lap_time']:.1f}s avg)")
            print(f"• Highest Tire Wear: {highest_degradation['track_name'].upper()} ({highest_degradation['degradation_rate']:.2f}s/lap)")
            print(f"• Most Aggressive Strategy: {highest_degradation['track_name'].upper()} - pit every {max(3, int(2.0/highest_degradation['degradation_rate']))} laps")
        
        return report_df

def main():
    analyzer = MultiTrackAnalyzer()
    analyzer.analyze_all_tracks()
    
    if analyzer.track_profiles:
        report = analyzer.generate_comprehensive_report()
        
        # Save for dashboard
        joblib.dump(analyzer.track_profiles, 'backend/multi_track_profiles.pkl')
        print(f"\n💾 Multi-track profiles saved to 'backend/multi_track_profiles.pkl'")
        
        # Show what we have
        print(f"\n📁 Available for demo: {len(analyzer.track_profiles)} tracks")
        for track in analyzer.track_profiles:
            print(f"   - {track.upper()}")
    else:
        print("❌ No tracks were successfully analyzed")

if __name__ == "__main__":
    main()