#!/usr/bin/env python3
"""Quick test of intent interpretation"""

import os
import sys
import json

# Add jarvis directory to path
jarvis_path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, jarvis_path)

from tools import interpret_file_intent

def test_intent():
    """Quick test of intent interpretation"""
    test_commands = [
        "list files in my documents",
        "show me PDFs from my econ 306 class", 
        "open the cartoon file",
        "what's the weather like"
    ]
    
    for command in test_commands:
        print(f"\nCommand: '{command}'")
        try:
            intent = interpret_file_intent(command)
            print(f"Intent: {json.dumps(intent, indent=2)}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    test_intent()
