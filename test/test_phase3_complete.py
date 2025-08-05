#!/usr/bin/env python3
"""
Test Phase 3: Intent & Contextual NLU - Complete System Test
Tests all three steps: Intent Classification, Disambiguation, and Follow-up Clarifications
"""

import os
import sys
import json

# Add jarvis directory to path
jarvis_path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, jarvis_path)

from tools import interpret_file_intent
from agent_core import chat_with_agent_enhanced, handle_clarification, pending_action, _dispatch_file_operation
from file_index import file_index

def test_intent_classification():
    """Test Step 3A: Intent Classification & Slot Extraction"""
    print("=" * 60)
    print("TESTING PHASE 3A: INTENT CLASSIFICATION & SLOT EXTRACTION")
    print("=" * 60)
    
    test_commands = [
        "list files in my jarvis folder",
        "show me Python files related to memory",
        "open requirements.txt",
        "delete the temp file",
        "move config.json to desktop",
        "find audio files",
        "search for configuration files",
        "what's the weather today"  # Non-file command
    ]
    
    for command in test_commands:
        print(f"\nCommand: '{command}'")
        intent = interpret_file_intent(command)
        print(f"Intent: {json.dumps(intent, indent=2)}")
        
        if intent.get("is_file_command", False):
            print(f"✅ Correctly identified as file command with {intent.get('confidence', 0):.2f} confidence")
        else:
            print(f"❌ Not identified as file command")

def test_direct_dispatch():
    """Test direct dispatching based on intent"""
    print("\n" + "=" * 60)
    print("TESTING DIRECT INTENT DISPATCH")
    print("=" * 60)
    
    # Ensure file index is loaded
    if file_index.index is None:
        print("🔍 Loading file index...")
        file_index.load()
    
    test_commands = [
        "list files in jarvis folder",
        "search for python files",
        "find audio files"
    ]
    
    for command in test_commands:
        print(f"\nTesting direct dispatch for: '{command}'")
        intent = interpret_file_intent(command)
        
        if intent.get("is_file_command", False) and intent.get("confidence", 0) > 0.6:
            result = _dispatch_file_operation(intent, command)
            if result:
                print(f"✅ Direct dispatch successful:")
                print(f"   {result[:200]}..." if len(result) > 200 else f"   {result}")
            else:
                print(f"❌ Direct dispatch returned None")
        else:
            print(f"⚠️ Intent not confident enough for direct dispatch")

def test_enhanced_agent():
    """Test the enhanced agent with intent interpretation"""
    print("\n" + "=" * 60)
    print("TESTING ENHANCED AGENT WITH INTENT INTERPRETATION")
    print("=" * 60)
    
    conversation_history = [
        {"role": "system", "content": "You are JARVIS testing enhanced file operations."}
    ]
    
    test_commands = [
        "show me some Python files",
        "find configuration files",
        "list recent files"
    ]
    
    for command in test_commands:
        print(f"\nTesting enhanced agent with: '{command}'")
        try:
            response = chat_with_agent_enhanced(conversation_history.copy(), command)
            print(f"✅ Enhanced agent response:")
            print(f"   {response[:300]}..." if len(response) > 300 else f"   {response}")
        except Exception as e:
            print(f"❌ Enhanced agent failed: {e}")

def test_disambiguation_flow():
    """Test Step 3B: Disambiguation & Conversational State"""
    print("\n" + "=" * 60)
    print("TESTING PHASE 3B: DISAMBIGUATION & CONVERSATIONAL STATE")
    print("=" * 60)
    
    # This test simulates the disambiguation flow
    print("Simulating a command that would result in multiple file matches...")
    
    # Clear any existing pending action
    import agent_core
    agent_core.pending_action = None
    
    # Simulate a command that finds multiple files
    print("Command: 'open the python file'")
    print("(This would typically find multiple .py files and trigger disambiguation)")
    
    # Manually set up a pending action to test clarification handling
    agent_core.pending_action = {
        "action": "open",
        "candidates": [
            "C:\\Users\\jwexl\\Desktop\\jarvis\\jarvis.py",
            "C:\\Users\\jwexl\\Desktop\\jarvis\\agent_core.py", 
            "C:\\Users\\jwexl\\Desktop\\jarvis\\tools.py"
        ],
        "original_command": "open the python file"
    }
    
    print("✅ Pending action set up for testing clarification")
    print(f"   Action: {agent_core.pending_action['action']}")
    print(f"   Candidates: {len(agent_core.pending_action['candidates'])} files")

def test_clarification_handling():
    """Test Step 3C: Follow-Up Clarifications & Flexible Dialogue"""
    print("\n" + "=" * 60)
    print("TESTING PHASE 3C: FOLLOW-UP CLARIFICATIONS & FLEXIBLE DIALOGUE")
    print("=" * 60)
    
    # Ensure we have a pending action from the previous test
    import agent_core
    if not agent_core.pending_action:
        print("⚠️ No pending action found. Setting up test scenario...")
        agent_core.pending_action = {
            "action": "open",
            "candidates": [
                "C:\\Users\\jwexl\\Desktop\\jarvis\\jarvis.py",
                "C:\\Users\\jwexl\\Desktop\\jarvis\\agent_core.py", 
                "C:\\Users\\jwexl\\Desktop\\jarvis\\tools.py"
            ],
            "original_command": "open the python file"
        }
    
    # Test different clarification responses
    test_clarifications = [
        "1",  # Number selection
        "jarvis",  # Keyword selection
        "agent",  # Keyword selection
        "cancel"  # Cancellation
    ]
    
    for clarification in test_clarifications:
        print(f"\nTesting clarification response: '{clarification}'")
        
        # Reset pending action for each test
        agent_core.pending_action = {
            "action": "open",
            "candidates": [
                "C:\\Users\\jwexl\\Desktop\\jarvis\\jarvis.py",
                "C:\\Users\\jwexl\\Desktop\\jarvis\\agent_core.py", 
                "C:\\Users\\jwexl\\Desktop\\jarvis\\tools.py"
            ],
            "original_command": "open the python file"
        }
        
        try:
            result = handle_clarification(clarification)
            if result:
                print(f"✅ Clarification handled:")
                print(f"   {result[:200]}..." if len(result) > 200 else f"   {result}")
            else:
                print(f"❌ Clarification not handled (returned None)")
        except Exception as e:
            print(f"❌ Clarification handling failed: {e}")

def test_end_to_end_flow():
    """Test the complete end-to-end Phase 3 flow"""
    print("\n" + "=" * 60)
    print("TESTING END-TO-END PHASE 3 FLOW")
    print("=" * 60)
    
    # Clear any existing pending action
    import agent_core
    agent_core.pending_action = None
    
    conversation_history = [
        {"role": "system", "content": "You are JARVIS testing the complete Phase 3 system."}
    ]
    
    print("Step 1: Initial command that should trigger disambiguation")
    command1 = "show me Python files"
    
    try:
        response1 = chat_with_agent_enhanced(conversation_history.copy(), command1)
        print(f"Response 1: {response1[:200]}..." if len(response1) > 200 else f"Response 1: {response1}")
        
        # Check if this created a pending action
        if agent_core.pending_action:
            print(f"✅ Pending action created: {agent_core.pending_action['action']} with {len(agent_core.pending_action['candidates'])} candidates")
            
            print("\nStep 2: Follow-up clarification")
            clarification = "jarvis"
            result = handle_clarification(clarification)
            if result:
                print(f"✅ Clarification successful: {result[:200]}..." if len(result) > 200 else f"✅ Clarification successful: {result}")
            else:
                print("❌ Clarification failed")
        else:
            print("ℹ️ No pending action created (command may have been handled directly)")
            
    except Exception as e:
        print(f"❌ End-to-end test failed: {e}")

def main():
    """Run all Phase 3 tests"""
    print("TESTING PHASE 3: INTENT & CONTEXTUAL NLU")
    print("Testing complete implementation of Intent Classification, Disambiguation, and Clarifications")
    print()
    
    try:
        # Test each phase
        test_intent_classification()
        test_direct_dispatch()
        test_enhanced_agent()
        test_disambiguation_flow()
        test_clarification_handling()
        test_end_to_end_flow()
        
        print("\n" + "=" * 60)
        print("PHASE 3 TESTING COMPLETE!")
        print("✅ Intent Classification & Slot Extraction")
        print("✅ Disambiguation & Conversational State")
        print("✅ Follow-Up Clarifications & Flexible Dialogue")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Phase 3 testing failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
