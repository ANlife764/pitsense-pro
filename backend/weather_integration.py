# backend/weather_integration.py
import requests
import pandas as pd
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

class RacingWeatherIntegration:
    def __init__(self):
        self.api_key = os.getenv('OPENWEATHER_API_KEY')
        self.track_coordinates = {
            'barber': (33.565, -86.655),  # Barber Motorsports Park
            'cota': (30.133, -97.641),     # Circuit of the Americas
            'road america': (43.799, -87.990),
            'sebring': (27.455, -81.354),
            'sonoma': (38.160, -122.455),
            'vir': (36.758, -78.967)
        }
    
    def get_track_weather(self, track_name):
        """Get current weather for specific track"""
        lat, lon = self.track_coordinates.get(track_name, (0, 0))
        
        try:
            url = f"http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={self.api_key}&units=metric"
            response = requests.get(url).json()
            
            return {
                'track': track_name.upper(),
                'temperature': response['main']['temp'],
                'track_temp': response['main']['temp'] + 15,  # Track is hotter than air
                'humidity': response['main']['humidity'],
                'conditions': response['weather'][0]['main'],
                'wind_speed': response['wind']['speed'],
                'rain_1h': response.get('rain', {}).get('1h', 0),
                'last_updated': datetime.now().strftime("%H:%M")
            }
        except:
            return self.get_fallback_weather(track_name)
    
    def get_weather_impact(self, weather_data, track_profile):
        """Calculate weather impact on strategy"""
        base_degradation = track_profile['degradation_rate']
        
        # Temperature impact (hot = more degradation)
        temp_impact = max(0.1, (weather_data['track_temp'] - 25) * 0.02)
        
        # Rain impact
        rain_impact = 0
        if weather_data['rain_1h'] > 0:
            rain_impact = 0.3  # Significant strategy change
        
        adjusted_degradation = base_degradation * (1 + temp_impact + rain_impact)
        
        return {
            'original_degradation': base_degradation,
            'adjusted_degradation': adjusted_degradation,
            'temperature_impact': f"+{temp_impact:.2f}s/lap",
            'rain_risk': "HIGH" if rain_impact > 0 else "LOW",
            'recommendation': self.generate_weather_recommendation(weather_data)
        }
    
    def generate_weather_recommendation(self, weather_data):
        """Generate strategy recommendations based on weather"""
        if weather_data['rain_1h'] > 2:
            return "Switch to wet tires. Pit window becomes unpredictable."
        elif weather_data['track_temp'] > 40:
            return "High track temp. Consider harder compound or earlier pit."
        elif weather_data['track_temp'] < 15:
            return "Cool conditions. Extended stints possible with softer tires."
        else:
            return "Ideal conditions. Stick to standard strategy."