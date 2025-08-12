#!/usr/bin/env python3
"""
Test script for the enhanced smart fallback system in open_website.
Tests various scenarios to ensure proper escalation to Playwright when needed.
"""

from tools import open_website

def test_smart_fallback():
    """Test the smart fallback system with different types of URLs"""
    
    print("=" * 60)
    print("TESTING SMART FALLBACK SYSTEM")
    print("=" * 60)
    
    # Test 1: Regular website (should use Tier 0 fast path)
    print("\n1. Testing regular website (should use Tier 0 fast path):")
    print("-" * 50)
    result1 = open_website(query="Python programming language documentation", summary_only=True)
    print(f"Result type: {type(result1)}")
    print(f"Result preview: {str(result1)[:200]}...")
    
    # Test 2: LinkedIn URL (should escalate to Playwright immediately)
    print("\n2. Testing LinkedIn URL (should escalate to Playwright immediately):")
    print("-" * 50)
    result2 = open_website(url="https://linkedin.com/in/example", summary_only=True)
    print(f"Result type: {type(result2)}")
    print(f"Result preview: {str(result2)[:200]}...")
    
    # Test 3: Query that might return LinkedIn results
    print("\n3. Testing query that might return LinkedIn (should auto-escalate):")
    print("-" * 50)
    result3 = open_website(query="LinkedIn profile search", summary_only=True)
    print(f"Result type: {type(result3)}")
    print(f"Result preview: {str(result3)[:200]}...")
    
    # Test 4: Regular news site (should use Tier 0)
    print("\n4. Testing regular news site (should use Tier 0):")
    print("-" * 50)
    result4 = open_website(query="BBC news today", summary_only=True)
    print(f"Result type: {type(result4)}")
    print(f"Result preview: {str(result4)[:200]}...")
    
    print("\n" + "=" * 60)
    print("SMART FALLBACK TESTING COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    test_smart_fallback()
