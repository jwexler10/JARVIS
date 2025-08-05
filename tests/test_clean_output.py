#!/usr/bin/env python3
"""
Quick test of clean output
"""
import subprocess
import sys

# Test the time function with clean output
print("Testing clean JARVIS output...")
print("=" * 50)

try:
    # Run jarvis with a simple time query
    result = subprocess.run([
        sys.executable, "jarvis.py", "--text"
    ], input="what time is it?\nexit\n", capture_output=True, text=True, timeout=30)
    
    print("STDOUT:")
    print(result.stdout)
    
    if result.stderr:
        print("\nSTDERR:")
        print(result.stderr)
        
except subprocess.TimeoutExpired:
    print("Test timed out")
except Exception as e:
    print(f"Error running test: {e}")
