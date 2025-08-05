#!/usr/bin/env python3
"""
Test script to check what variations of Stone Harbor work with OpenWeather API
"""

import json
import requests

def load_config(path="config.json"):
    with open(path, "r") as f:
        return json.load(f)

def test_stone_harbor_variations():
    """Test different Stone Harbor variations with OpenWeather API"""
    cfg = load_config()
    key = cfg.get("openweather_api_key")
    
    if not key:
        print("❌ No API key found")
        return
    
    variations = [
        "Stone Harbor, NJ",
        "Stone Harbor, New Jersey", 
        "Stone Harbor NJ",
        "Stone Harbor",
        "Stone Harbor, NJ, US",
        "Stone Harbor, New Jersey, US",
        "Cape May, NJ",  # Nearby town
        "Avalon, NJ",    # Nearby town
        "Cape May Point, NJ",
        "Wildwood, NJ",  # Larger nearby beach town
        "Ocean City, NJ" # Another nearby beach town
    ]
    
    print("Testing Stone Harbor variations with OpenWeather API...")
    print("=" * 60)
    
    for city in variations:
        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {"q": city, "appid": key, "units": "imperial"}
        
        try:
            resp = requests.get(url, params=params, timeout=5)
            data = resp.json()
            
            if resp.status_code == 200:
                location_name = data.get("name", "Unknown")
                country = data.get("sys", {}).get("country", "Unknown")
                print(f"✅ {city:<25} -> Found: {location_name}, {country}")
            else:
                print(f"❌ {city:<25} -> {data.get('message', 'Not found')}")
                
        except Exception as e:
            print(f"❌ {city:<25} -> Error: {e}")

if __name__ == "__main__":
    test_stone_harbor_variations()
