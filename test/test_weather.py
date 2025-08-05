#!/usr/bin/env python3
"""
Test script for the improved weather functionality
"""

from weather import get_intelligent_weather, extract_location_from_query

def test_location_extraction():
    """Test the location extraction from various queries"""
    print("🧪 Testing location extraction...")
    
    test_queries = [
        "what's the weather in stone harbor new jersey this weekend?",
        "weather in NYC tomorrow",
        "how's the weather in Philadelphia",
        "weather for where I'm going this weekend",
        "what's it looking like this weekend",
        "weather in Miami this week"
    ]
    
    for query in test_queries:
        location = extract_location_from_query(query)
        print(f"Query: '{query}'")
        print(f"Extracted: {location}\n")

def test_intelligent_weather():
    """Test the intelligent weather function"""
    print("🌤️ Testing intelligent weather...")
    
    test_queries = [
        "what's the weather in stone harbor new jersey this weekend?",
        "weather in Philadelphia tomorrow",
        "how's the weather today"
    ]
    
    for query in test_queries:
        print(f"\nQuery: '{query}'")
        try:
            result = get_intelligent_weather(query)
            print(f"Result: {result}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    test_location_extraction()
    print("\n" + "="*50 + "\n")
    test_intelligent_weather()
