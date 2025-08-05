#!/usr/bin/env python3
"""
Test script for pattern learning functionality
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from pattern_learning import get_preferred_times, extract_preferred_slots, save_preferred_times, load_preferred_times
from memory_store import init_db

def test_pattern_learning():
    """Test the pattern learning system"""
    print("🧪 Testing Pattern Learning System")
    
    # Initialize memory store
    try:
        init_db()
        print("✅ Memory store initialized")
    except Exception as e:
        print(f"⚠️ Memory store init failed: {e}")
    
    # Test getting preferred times for meetings
    try:
        preferred = get_preferred_times("meeting", top_n=3)
        print(f"📅 Preferred meeting times: {preferred}")
        
        if preferred:
            times_str = ", ".join(f"{h}:00" for h in preferred)
            print(f"🕐 Formatted times: {times_str}")
        else:
            print("📊 No meeting patterns found yet")
            
    except Exception as e:
        print(f"❌ Error getting preferred times: {e}")
        import traceback
        traceback.print_exc()
    
    # Test manual pattern extraction
    try:
        slots = extract_preferred_slots("meeting", top_n=3)
        print(f"🔍 Manual extraction result: {slots}")
    except Exception as e:
        print(f"❌ Error in manual extraction: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_pattern_learning()
