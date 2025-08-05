#!/usr/bin/env python3
"""
Test script for Step 3B: Disambiguation & Conversational State
Tests the multi-turn disambiguation flow for ambiguous file commands.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import agent_core
from agent_core import chat_with_agent_enhanced, handle_clarification

def test_disambiguation_flow():
    """Test the complete disambiguation workflow"""
    print("🧪 Testing Step 3B: Disambiguation & Conversational State")
    print("=" * 60)
    
    # Reset pending action
    agent_core.pending_action = None
    
    # Test 1: Ambiguous file open command
    print("\n📋 Test 1: Ambiguous file open command")
    print("Command: 'Open the econ 306 PDF'")
    
    conversation_history = [
        {"role": "system", "content": "You are JARVIS with enhanced file operation capabilities."}
    ]
    
    # This should trigger disambiguation if multiple files match
    response1 = chat_with_agent_enhanced(conversation_history, "Open the econ 306 PDF")
    print(f"Response: {response1}")
    print(f"Pending action set: {agent_core.pending_action is not None}")
    if agent_core.pending_action:
        print(f"Pending action details: {agent_core.pending_action}")
    
    # Test 2: Clarification by number
    if agent_core.pending_action:
        print("\n📋 Test 2: Clarification by number")
        print("Follow-up: '1'")
        
        response2 = handle_clarification("1")
        print(f"Response: {response2}")
        print(f"Pending action cleared: {agent_core.pending_action is None}")
    
    print("\n" + "=" * 60)
    
    # Reset pending action between tests
    agent_core.pending_action = None
    
    # Test 3: Ambiguous file read command  
    print("\n📋 Test 3: Ambiguous file read command")
    print("Command: 'Read the python file'")
    
    conversation_history = [
        {"role": "system", "content": "You are JARVIS with enhanced file operation capabilities."}
    ]
    
    response3 = chat_with_agent_enhanced(conversation_history, "Read the python file")
    print(f"Response: {response3}")
    print(f"Pending action set: {agent_core.pending_action is not None}")
    if agent_core.pending_action:
        print(f"Pending action details: {agent_core.pending_action}")
    
    # Test 4: Clarification by keyword
    if agent_core.pending_action:
        print("\n📋 Test 4: Clarification by keyword")
        print("Follow-up: 'the main jarvis one'")
        
        response4 = handle_clarification("the main jarvis one")
        print(f"Response: {response4}")
        print(f"Pending action cleared: {agent_core.pending_action is None}")
    
    print("\n" + "=" * 60)
    
    # Reset pending action between tests
    agent_core.pending_action = None
    
    # Test 5: Delete with confirmation
    print("\n📋 Test 5: Delete with confirmation")
    print("Command: 'Delete test file'")
    
    conversation_history = [
        {"role": "system", "content": "You are JARVIS with enhanced file operation capabilities."}
    ]
    
    response5 = chat_with_agent_enhanced(conversation_history, "Delete test file")
    print(f"Response: {response5}")
    print(f"Pending action set: {agent_core.pending_action is not None}")
    if agent_core.pending_action:
        print(f"Pending action details: {agent_core.pending_action}")
    
    # Test 6: Confirmation response
    if agent_core.pending_action:
        print("\n📋 Test 6: Confirmation response")
        print("Follow-up: 'yes'")
        
        response6 = handle_clarification("yes")
        print(f"Response: {response6}")
        print(f"Pending action cleared: {agent_core.pending_action is None}")
    
    print("\n" + "=" * 60)
    print("✅ Step 3B disambiguation testing complete!")

def test_no_matches():
    """Test behavior when no files match"""
    print("\n🧪 Testing no matches scenario")
    print("=" * 60)
    
    # Reset pending action
    agent_core.pending_action = None
    
    conversation_history = [
        {"role": "system", "content": "You are JARVIS with enhanced file operation capabilities."}
    ]
    
    response = chat_with_agent_enhanced(conversation_history, "Open the nonexistent xyz file")
    print(f"Command: 'Open the nonexistent xyz file'")
    print(f"Response: {response}")
    print(f"Pending action set: {agent_core.pending_action is not None}")

def test_single_match():
    """Test behavior when exactly one file matches"""
    print("\n🧪 Testing single match scenario")
    print("=" * 60)
    
    # Reset pending action
    agent_core.pending_action = None
    
    conversation_history = [
        {"role": "system", "content": "You are JARVIS with enhanced file operation capabilities."}
    ]
    
    response = chat_with_agent_enhanced(conversation_history, "Open jarvis.py")
    print(f"Command: 'Open jarvis.py'")
    print(f"Response: {response}")
    print(f"Pending action set: {agent_core.pending_action is not None}")

if __name__ == "__main__":
    try:
        test_disambiguation_flow()
        test_no_matches()
        test_single_match()
        print("\n🎉 All Step 3B tests completed!")
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
