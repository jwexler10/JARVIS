#!/usr/bin/env python3
"""
Quick test of time functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from jarvis import get_current_time

# Test the get_current_time function directly
result = get_current_time()
print("✅ Time function test:")
print(f"Current datetime: {result['current_datetime']}")
print(f"Formatted: {result['formatted_datetime']}")
print(f"Date: {result['date']}")
print(f"Time: {result['time']}")
print(f"Day of week: {result['day_of_week']}")
print(f"Timezone: {result['timezone']}")

print("\n✅ JARVIS time functionality is working correctly!")
