#!/usr/bin/env python3
"""
Test JARVIS with a simple command to see what's happening
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from jarvis import ask_jarvis
    
    print("🧪 Testing JARVIS with a simple command...")
    response = ask_jarvis("hello jarvis!", text_mode=True, speaker="Jason")
    print(f"✅ Response: {response}")
    
except Exception as e:
    print(f"❌ Error testing JARVIS: {e}")
    import traceback
    traceback.print_exc()
