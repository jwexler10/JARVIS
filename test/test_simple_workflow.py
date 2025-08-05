#!/usr/bin/env python3
"""
Simple Test for Step 4C Workflow Fixes
Tests the core workflow functionality with simple operations.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agent_core import chat_with_agent_enhanced

def test_simple_workflow():
    """Test basic workflow functionality"""
    print("🧪 Testing Step 4C: Simple Workflow Fixes")
    print("=" * 50)
    
    # Test 1: Simple file organization
    print("\n📋 Test 1: Create folder and organize txt files")
    print("Command: 'Create a text_files folder and move any .txt files into it'")
    
    try:
        test_history = []
        response = chat_with_agent_enhanced(test_history, "Create a text_files folder and move any .txt files into it")
        print(f"Response: {response}")
        
        # Check for success indicators
        has_success = "✅" in response and ("created" in response.lower() or "moved" in response.lower())
        print(f"Status: {'✅ Success' if has_success else '❌ Failed'}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: Simple pattern matching
    print("\n📋 Test 2: List Python files")
    print("Command: 'Show me all the .py files in the current directory'")
    
    try:
        test_history = []
        response = chat_with_agent_enhanced(test_history, "Show me all the .py files in the current directory")
        print(f"Response: {response[:200]}...")
        
        # Check for success indicators
        has_files = ".py" in response and ("files" in response.lower() or "agent_core.py" in response)
        print(f"Status: {'✅ Success' if has_files else '❌ Failed'}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_simple_workflow()
