#!/usr/bin/env python3
"""
Test Step 4C: Multi-Step File Workflows (Improved)
Tests the enhanced workflow planning and execution system.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agent_core import chat_with_agent_enhanced

def test_workflow_planning():
    """Test enhanced workflow planning and execution"""
    print("🧪 Testing Step 4C: Multi-Step File Workflows (Enhanced)")
    print("=" * 60)
    
    # Initialize conversation history for each test
    conversation_history = []
    
    test_cases = [
        {
            "name": "Simple workflow - organize Python files",
            "command": "Create a python_files folder and move all .py files into it",
            "expected": "workflow planning and execution"
        },
        {
            "name": "Archive workflow - backup JSON configs", 
            "command": "Archive all JSON config files to a backup folder",
            "expected": "multi-step backup workflow"
        },
        {
            "name": "Cleanup workflow - organize test files",
            "command": "Organize test files: create test_archive folder and move all test_*.py files there",
            "expected": "cleanup and organization workflow"
        },
        {
            "name": "Multi-step search and move",
            "command": "Find all log files and move them to an archive directory",
            "expected": "search-then-move workflow"
        }
    ]
    
    results = []
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n📋 Test {i}: {test['name']}")
        print(f"Command: '{test['command']}'")
        
        try:
            # Use a fresh conversation for each test
            test_history = []
            response = chat_with_agent_enhanced(test_history, test['command'])
            
            # Check if response indicates workflow execution
            is_workflow = any(keyword in response.lower() for keyword in [
                "workflow", "step", "executing", "created", "moved", "archived"
            ])
            
            results.append({
                "test": test['name'], 
                "success": is_workflow,
                "response": response[:200] + "..." if len(response) > 200 else response
            })
            
            print(f"Response: {response}")
            
        except Exception as e:
            print(f"❌ Error in test {i}: {e}")
            results.append({
                "test": test['name'],
                "success": False, 
                "response": f"Error: {e}"
            })
    
    # Summary
    print(f"\n🎯 Step 4C Enhanced Workflow Test Results:")
    successful_tests = sum(1 for r in results if r['success'])
    total_tests = len(results)
    
    for result in results:
        status = "✅" if result['success'] else "❌"
        print(f"{status} {result['test']}")
        if not result['success']:
            print(f"   Response: {result['response']}")
    
    print(f"\n📊 Overall: {successful_tests}/{total_tests} tests passed")
    
    if successful_tests == total_tests:
        print("🎉 All workflow tests passed! Step 4C is working correctly.")
    else:
        print("⚠️ Some workflow tests failed. Check the responses above.")

if __name__ == "__main__":
    test_workflow_planning()
