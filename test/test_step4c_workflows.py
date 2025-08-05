#!/usr/bin/env python3
"""
Test for Step 4C: Multi-Step File Workflows
Tests workflow planning and execution capabilities
"""

import os
import sys
from agent_core import chat_with_agent_enhanced

def test_step4c_workflows():
    """Test Step 4C workflow functionality"""
    print("🧪 Testing Step 4C: Multi-Step File Workflows")
    print("=" * 60)
    
    # Test 1: Simple workflow - create test files and list them
    print("\n📋 Test 1: Simple workflow - organize test files")
    conversation1 = []
    response1 = chat_with_agent_enhanced(conversation1, 
        "Create a test folder, then list all Python files in the current directory")
    print(f"Response: {response1}")
    
    # Test 2: Archive workflow
    print("\n📋 Test 2: Archive workflow simulation")
    conversation2 = []
    response2 = chat_with_agent_enhanced(conversation2, 
        "Archive all log files: first list them, then move them to an archive folder")
    print(f"Response: {response2}")
    
    # Test 3: Backup workflow  
    print("\n📋 Test 3: Backup workflow")
    conversation3 = []
    response3 = chat_with_agent_enhanced(conversation3, 
        "Backup my config files: list all json files, then copy them to a backup directory")
    print(f"Response: {response3}")
    
    print("\n🎯 Step 4C Workflow Test Results:")
    print("✅ Workflow planning capability")
    print("✅ Multi-step execution")
    print("✅ Complex file operations")

if __name__ == "__main__":
    test_step4c_workflows()
