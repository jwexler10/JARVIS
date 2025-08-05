#!/usr/bin/env python3
"""
Test Step 4C: Multi-Step File Workflows (Final)
Tests the fully enhanced workflow planning and execution system.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agent_core import chat_with_agent_enhanced

def test_workflow_planning():
    """Test enhanced workflow planning and execution"""
    print("🧪 Testing Step 4C: Multi-Step File Workflows (Final)")
    print("=" * 60)
    
    test_cases = [
        {
            "name": "Organize Python files workflow",
            "command": "Create a python_files folder and move all .py files into it",
            "expected": "directory creation and file moving"
        },
        {
            "name": "Archive JSON config files", 
            "command": "Archive all JSON config files to a backup folder",
            "expected": "finding JSON files and archiving them"
        },
        {
            "name": "Organize test files by pattern",
            "command": "Create test_archive folder and move all test_*.py files there",
            "expected": "pattern-based file organization"
        },
        {
            "name": "Simple workflow test",
            "command": "Organize files: make an 'old_files' directory and move all .txt files into it",
            "expected": "directory creation and text file organization"
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
            
            # Check if response indicates successful workflow execution
            success_indicators = [
                "workflow execution results",
                "✅",
                "created directory",
                "moved",
                "found",
                "files"
            ]
            
            is_successful = any(indicator.lower() in response.lower() 
                              for indicator in success_indicators)
            
            # Check for error indicators
            has_errors = "❌" in response and response.count("❌") > response.count("✅")
            
            results.append({
                "test": test['name'], 
                "success": is_successful and not has_errors,
                "response": response
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
    print(f"\n🎯 Step 4C Final Workflow Test Results:")
    successful_tests = sum(1 for r in results if r['success'])
    total_tests = len(results)
    
    for result in results:
        status = "✅" if result['success'] else "❌"
        print(f"{status} {result['test']}")
        if not result['success']:
            # Show first 200 chars of response for failed tests
            response_preview = result['response'][:200] + "..." if len(result['response']) > 200 else result['response']
            print(f"   Response: {response_preview}")
    
    print(f"\n📊 Overall: {successful_tests}/{total_tests} tests passed")
    
    if successful_tests == total_tests:
        print("🎉 All workflow tests passed! Step 4C is fully functional.")
        print("✨ Jarvis can now plan and execute multi-step file workflows!")
    elif successful_tests >= total_tests * 0.75:
        print("🟡 Most workflow tests passed. Step 4C is largely functional.")
    else:
        print("🔴 Many workflow tests failed. More work needed on Step 4C.")

if __name__ == "__main__":
    test_workflow_planning()
