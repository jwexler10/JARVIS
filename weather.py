import json
import requests
import re
from datetime import datetime, timedelta
from openai import OpenAI

def load_config(path="config.json"):
    with open(path, "r") as f:
        return json.load(f)

def extract_location_from_query(query: str) -> str:
    """
    Use OpenAI to intelligently extract a city/location from a natural language query.
    Examples:
    - "weather in stone harbor new jersey this weekend" -> "stone harbor, new jersey"
    - "what's it like in NYC tomorrow" -> "New York City"
    - "weather for where I'm going this weekend" -> None (needs calendar lookup)
    """
    try:
        cfg = load_config()
        api_key = cfg.get("openai_api_key")
        org_id = cfg.get("openai_organization")
        
        if not api_key:
            return None
            
        if org_id:
            client = OpenAI(api_key=api_key, organization=org_id)
        else:
            client = OpenAI(api_key=api_key)
        
        prompt = f"""Extract the city/location name from this weather query. Return ONLY the city name and state/country, nothing else. If no specific location is mentioned, return "NONE".

Examples:
- "weather in stone harbor new jersey this weekend" -> "Stone Harbor, New Jersey"
- "what's the weather like in NYC tomorrow" -> "New York City, New York"
- "weather for where I'm going this weekend" -> "NONE"
- "how's the weather looking this weekend" -> "NONE"

Query: "{query}"
Location:"""

        resp = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You extract location names from weather queries. Return only the clean city/location name or 'NONE'."},
                {"role": "user", "content": prompt}
            ],
            temperature=0,
            max_tokens=50
        )
        
        location = resp.choices[0].message.content.strip()
        return location if location != "NONE" else None
        
    except Exception as e:
        print(f"[Weather] Error extracting location: {e}")
        return None

def get_location_from_calendar(query: str) -> str:
    """
    Check upcoming calendar events to determine where the user will be.
    Used when queries like "weather where I'm going this weekend" are made.
    """
    try:
        # Import here to avoid circular imports
        from google_calendar import get_upcoming_events
        
        # Determine time range based on query
        days_ahead = 1  # default to tomorrow
        if "weekend" in query.lower():
            # Get events for the upcoming weekend
            today = datetime.now()
            days_until_weekend = (5 - today.weekday()) % 7  # Days until Saturday
            if days_until_weekend == 0:  # Today is Saturday
                days_ahead = 1  # Include Sunday
            else:
                days_ahead = days_until_weekend + 2  # Saturday + Sunday
        elif "week" in query.lower():
            days_ahead = 7
        
        # Get upcoming events
        events = get_upcoming_events(max_results=10)
        
        # Look for events with location information
        target_locations = []
        end_time = datetime.now() + timedelta(days=days_ahead)
        
        for event in events:
            if event.get("location"):
                event_start = event.get("start", {})
                if event_start:
                    # Parse event time - handle both dateTime and date formats
                    event_time_str = event_start.get("dateTime") or event_start.get("date")
                    if event_time_str:
                        try:
                            # Handle timezone info
                            if "T" in event_time_str:
                                event_time = datetime.fromisoformat(event_time_str.replace("Z", "+00:00"))
                            else:
                                event_time = datetime.fromisoformat(event_time_str)
                            
                            # Check if event is in our target timeframe
                            if event_time <= end_time:
                                target_locations.append(event["location"])
                        except:
                            continue
        
        if target_locations:
            # Return the most recent/relevant location
            return target_locations[0]
            
    except Exception as e:
        print(f"[Weather] Error checking calendar: {e}")
    
    return None

def is_weekend_or_future_query(query: str) -> bool:
    """Check if the query is asking about future weather (weekend, tomorrow, etc.)"""
    future_terms = ["weekend", "tomorrow", "this week", "next week", "saturday", "sunday", "monday", "tuesday", "wednesday", "thursday", "friday"]
    return any(term in query.lower() for term in future_terms)

def get_intelligent_weather(query: str, default_city: str = "Philadelphia") -> str:
    """
    Intelligently handle weather queries with natural language parsing.
    Can extract locations, check calendar for travel plans, and handle time-based requests.
    """
    try:
        # 1) Try to extract location from the query
        location = extract_location_from_query(query)
        
        # 2) If no location found and query suggests travel, check calendar
        if not location and ("where i'm going" in query.lower() or "where we're going" in query.lower()):
            location = get_location_from_calendar(query)
            if location:
                print(f"[Weather] Found travel location from calendar: {location}")
        
        # 3) Fall back to default city
        if not location:
            location = default_city
            
        # 4) Check if this is a future/weekend query
        if is_weekend_or_future_query(query):
            return get_weekend_forecast(location, query)
        else:
            return get_comprehensive_weather(location)
            
    except Exception as e:
        print(f"[Weather] Error in intelligent weather: {e}")
        return f"❌ Error getting weather information: {e}"

def normalize_city_name(city: str) -> list[str]:
    """
    Generate multiple variations of a city name to try with the weather API.
    Returns a list of city name variations to try.
    """
    variations = [city]  # Start with original
    
    # Common location mappings and variations
    city_lower = city.lower()
    
    # Handle "Stone Harbor, New Jersey" -> try different formats
    if "stone harbor" in city_lower and "new jersey" in city_lower:
        variations.extend([
            "Stone Harbor, NJ",
            "Stone Harbor,NJ", 
            "Stone Harbor NJ",
            "Stone Harbor",
            "Stone Harbor, NJ, US",
            "Stone Harbor, New Jersey, US",
            "Cape May Point, NJ",  # Sometimes smaller NJ beach towns are grouped
            "Avalon, NJ"  # Nearby larger town
        ])
    
    # Handle other NJ cities
    if "new jersey" in city_lower:
        # Replace "New Jersey" with "NJ"
        nj_version = city.replace("New Jersey", "NJ").replace("new jersey", "NJ")
        variations.append(nj_version)
        variations.append(nj_version.replace(", ", ","))
        variations.append(nj_version.replace(",", " "))
        # Add US suffix
        variations.append(f"{nj_version}, US")
    
    # Handle NYC variations
    if "new york city" in city_lower:
        variations.extend(["NYC", "New York, NY", "New York"])
    
    # Handle other common state abbreviations
    state_mappings = {
        ", Pennsylvania": ", PA",
        ", California": ", CA", 
        ", Florida": ", FL",
        ", Texas": ", TX",
        ", Maryland": ", MD",
        ", Delaware": ", DE"
    }
    
    for full_state, abbrev in state_mappings.items():
        if full_state.lower() in city_lower:
            base_name = city.replace(full_state, abbrev)
            variations.append(base_name)
            variations.append(f"{base_name}, US")
    
    # Add country suffix variations for international compatibility
    if ", US" not in city and "United States" not in city:
        variations.append(f"{city}, US")
    
    return list(set(variations))  # Remove duplicates

def get_weekend_forecast(city: str, query: str = "") -> str:
    """Get weather forecast for the weekend or specified future time."""
    cfg = load_config()
    key = cfg.get("openweather_api_key")
    
    if not key:
        return "❌ Weather API key not found in config."
    
    # Try multiple city name variations
    city_variations = normalize_city_name(city)
    forecast_data = None
    successful_city = None
    
    for city_variant in city_variations:
        try:
            # Get 5-day forecast
            forecast_url = "https://api.openweathermap.org/data/2.5/forecast"
            forecast_params = {"q": city_variant, "appid": key, "units": "imperial"}
            forecast_resp = requests.get(forecast_url, params=forecast_params, timeout=10)
            
            if forecast_resp.status_code == 200:
                forecast_data = forecast_resp.json()
                successful_city = city_variant
                break
            elif forecast_resp.status_code == 404:
                continue  # Try next variation
            else:
                # Some other error, don't continue trying
                data = forecast_resp.json()
                msg = data.get("message", "unknown error")
                return f"❌ Couldn't fetch forecast for {city}: {msg}"
        except Exception:
            continue  # Try next variation
    
    if not forecast_data:
        return f"❌ Couldn't find weather data for {city}. Tried variations: {', '.join(city_variations[:3])}..."
    
    try:
        # Determine target days based on query
        today = datetime.now()
        target_days = []
        
        if "weekend" in query.lower():
            # Find next Saturday and Sunday
            days_until_sat = (5 - today.weekday()) % 7
            if days_until_sat == 0 and today.weekday() == 5:  # Today is Saturday
                target_days = [today, today + timedelta(days=1)]  # Sat, Sun
            elif days_until_sat == 0 and today.weekday() == 6:  # Today is Sunday
                target_days = [today]  # Just Sunday
            else:
                sat = today + timedelta(days=days_until_sat)
                sun = sat + timedelta(days=1)
                target_days = [sat, sun]
        elif "tomorrow" in query.lower():
            target_days = [today + timedelta(days=1)]
        else:
            # Default to next 2-3 days
            target_days = [today + timedelta(days=i) for i in range(1, 4)]
        
        # Group forecast by day
        daily_forecasts = {}
        for item in forecast_data["list"]:
            forecast_time = datetime.fromtimestamp(item["dt"])
            date_key = forecast_time.date()
            
            if date_key not in daily_forecasts:
                daily_forecasts[date_key] = []
            daily_forecasts[date_key].append(item)
        
        # Build forecast summary
        forecast_parts = []
        
        for target_day in target_days:
            date_key = target_day.date()
            day_name = target_day.strftime("%A")
            
            if date_key in daily_forecasts:
                day_data = daily_forecasts[date_key]
                
                # Get high/low for the day
                temps = [item["main"]["temp"] for item in day_data]
                high_temp = max(temps)
                low_temp = min(temps)
                
                # Get most common weather condition
                conditions = [item["weather"][0]["description"] for item in day_data]
                main_condition = max(set(conditions), key=conditions.count).title()
                
                # Check for precipitation
                rain_chances = [item.get("pop", 0) * 100 for item in day_data if "pop" in item]
                max_rain_chance = max(rain_chances) if rain_chances else 0
                
                day_summary = f"{day_name}: {main_condition}, High {high_temp:.0f}°F, Low {low_temp:.0f}°F"
                if max_rain_chance > 20:
                    day_summary += f", {max_rain_chance:.0f}% chance of rain"
                
                forecast_parts.append(day_summary)
        
        if forecast_parts:
            period_name = "weekend" if "weekend" in query.lower() else "upcoming days"
            return f"Forecast for {successful_city} this {period_name}: " + " | ".join(forecast_parts)
        else:
            return f"No forecast data available for {successful_city} in the requested timeframe"
            
    except requests.RequestException as e:
        print(f"[Weather] Request error: {e}")
        return f"❌ Weather service temporarily unavailable for {city}"
    except Exception as e:
        print(f"[Weather] Unexpected error: {e}")
        return f"❌ Error getting forecast for {city}: {e}"
def get_weather(city: str) -> str:
    """Original simple weather function for backward compatibility."""
    # 1) Load and debug-print your key
    cfg = load_config()
    key = cfg.get("openweather_api_key")
    print(f"[DEBUG] OpenWeather Key loaded: {repr(key)}")

    if not key:
        return "❌ Weather API key not found in config."

    # Try multiple city name variations
    city_variations = normalize_city_name(city)
    
    for city_variant in city_variations:
        # 2) Make the request
        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {"q": city_variant, "appid": key, "units": "imperial"}
        resp = requests.get(url, params=params)

        # 3) Debug-print the response
        print(f"[DEBUG] Request URL: {resp.url}")
        print(f"[DEBUG] Status Code: {resp.status_code}")
        try:
            data = resp.json()
        except ValueError:
            continue  # Try next variation

        print(f"[DEBUG] Response JSON: {data}")

        # 4) Handle errors
        if resp.status_code == 200:
            # 5) Parse and return
            desc = data["weather"][0]["description"]
            temp = data["main"]["temp"]
            feels = data["main"]["feels_like"]
            return f"Right now in {city_variant}, it's {desc} with {temp:.0f}°F (feels like {feels:.0f}°F)."
        elif resp.status_code == 404:
            continue  # Try next variation
        else:
            msg = data.get("message", "unknown error")
            return f"❌ Couldn't fetch weather for {city}: {msg}"
    
    return f"❌ Couldn't find weather data for {city}. Tried variations: {', '.join(city_variations[:3])}..."

def get_comprehensive_weather(city: str) -> str:
    """Get comprehensive weather including current conditions, highs/lows, and precipitation forecast."""
    cfg = load_config()
    key = cfg.get("openweather_api_key")
    
    if not key:
        return "❌ Weather API key not found in config."
    
    # Try multiple city name variations
    city_variations = normalize_city_name(city)
    current_data = None
    successful_city = None
    
    for city_variant in city_variations:
        try:
            # Get current weather
            current_url = "https://api.openweathermap.org/data/2.5/weather"
            current_params = {"q": city_variant, "appid": key, "units": "imperial"}
            current_resp = requests.get(current_url, params=current_params, timeout=10)
            
            if current_resp.status_code == 200:
                current_data = current_resp.json()
                successful_city = city_variant
                break
            elif current_resp.status_code == 404:
                continue  # Try next variation
            else:
                return f"❌ Couldn't fetch current weather for {city}"
        except Exception:
            continue  # Try next variation
    
    if not current_data:
        return f"❌ Couldn't find weather data for {city}. Tried variations: {', '.join(city_variations[:3])}..."
    
    try:
        
        # Get 5-day forecast (includes today's highs/lows)
        forecast_url = "https://api.openweathermap.org/data/2.5/forecast"
        forecast_params = {"q": successful_city, "appid": key, "units": "imperial"}
        forecast_resp = requests.get(forecast_url, params=forecast_params, timeout=10)
        
        if forecast_resp.status_code != 200:
            # Fall back to current weather only
            desc = current_data["weather"][0]["description"]
            temp = current_data["main"]["temp"]
            feels = current_data["main"]["feels_like"]
            return f"Right now in {successful_city}: {desc}, {temp:.0f}°F (feels like {feels:.0f}°F)"
        
        forecast_data = forecast_resp.json()
        
        # Parse current conditions
        current_desc = current_data["weather"][0]["description"].title()
        current_temp = current_data["main"]["temp"]
        feels_like = current_data["main"]["feels_like"]
        humidity = current_data["main"]["humidity"]
        
        # Get today's forecast data (next 24 hours)
        today_forecasts = []
        now = datetime.now()
        
        for item in forecast_data["list"][:8]:  # Next 24 hours (8 x 3-hour periods)
            forecast_time = datetime.fromtimestamp(item["dt"])
            if forecast_time.date() == now.date():
                today_forecasts.append(item)
        
        # Calculate today's high/low from forecast
        if today_forecasts:
            temps = [item["main"]["temp"] for item in today_forecasts]
            today_high = max(temps)
            today_low = min(temps)
        else:
            # If no today forecasts, use current temp as both
            today_high = current_temp
            today_low = current_temp
        
        # Check for precipitation today
        rain_chance = 0
        will_rain = False
        precipitation_type = ""
        
        for item in today_forecasts:
            if "pop" in item:  # Probability of precipitation
                rain_chance = max(rain_chance, item["pop"] * 100)
            
            if "rain" in item:
                will_rain = True
                precipitation_type = "rain"
            elif "snow" in item:
                will_rain = True
                precipitation_type = "snow"
        
        # Build comprehensive summary
        summary = f"Currently {current_temp:.0f}°F and {current_desc.lower()}"
        summary += f" (feels like {feels_like:.0f}°F)"
        
        if today_high != today_low:
            summary += f". Today's high/low: {today_high:.0f}°F/{today_low:.0f}°F"
        
        if will_rain and rain_chance > 0:
            summary += f". {rain_chance:.0f}% chance of {precipitation_type} today"
        elif rain_chance > 20:  # Show chance even without detected precipitation
            summary += f". {rain_chance:.0f}% chance of precipitation today"
        else:
            summary += ". No rain expected today"
        
        if humidity > 70:
            summary += f". Humid at {humidity}%"
        
        return summary
        
    except requests.RequestException as e:
        print(f"[Weather] Request error: {e}")
        return f"❌ Weather service temporarily unavailable for {city}"
    except Exception as e:
        print(f"[Weather] Unexpected error: {e}")
        return f"❌ Error getting weather data for {city}"
