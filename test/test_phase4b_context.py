#!/usr/bin/env python3
"""
Test Phase 4B: Advanced Context Understanding
- Session state tracking (current directory, last file, last action)
- Pronoun and implicit target resolution ("it", "this", "that", "here")
- Context-aware operations
"""

import sys
import os
import agent_core
from agent_core import chat_with_agent_enhanced, _current_directory, _last_file, _last_action

def test_phase4b_context():
    """Test context awareness and pronoun resolution"""
    
    print("🧪 Testing Phase 4B: Advanced Context Understanding\n")
    
    # Reset session state and pending actions
    agent_core._current_directory = os.getcwd()
    agent_core._last_file = None
    agent_core._last_action = None
    agent_core.pending_action = None  # Clear any pending actions
    
    test_cases = [
        # Test 1: Basic file operation + session state tracking
        {
            "input": "read jarvis.py",
            "description": "Read a file to establish session state",
            "expected_context": "Should track jarvis.py as last file",
            "followup": "1"  # Select first option to complete the action
        },
        
        # Test 2: Pronoun resolution - "it"
        {
            "input": "open it",
            "description": "Use pronoun 'it' to refer to last file",
            "expected_context": "Should resolve 'it' to jarvis.py"
        },
        
        # Test 3: Directory context
        {
            "input": "list files here",
            "description": "List files in current context",
            "expected_context": "Should use current directory context"
        },
        
        # Test 4: Multiple pronouns
        {
            "input": "what's in this file?",
            "description": "Use 'this file' to refer to last file",
            "expected_context": "Should resolve 'this file' to last file"
        },
        
        # Test 5: Implicit directory reference
        {
            "input": "show me files in current folder",
            "description": "Use implicit directory reference",
            "expected_context": "Should resolve to current directory"
        }
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"--- Test {i}: {test['description']} ---")
        print(f"Input: '{test['input']}'")
        print(f"Expected: {test['expected_context']}")
        
        # Show current session state before
        print(f"Before - Last File: {agent_core._last_file}, Current Dir: {agent_core._current_directory}")
        
        try:
            # Initialize conversation history for each test
            conversation_history = []
            response = chat_with_agent_enhanced(conversation_history, test["input"])
            print(f"Response: {response}")
            
            # If there's a followup (like selecting option 1), execute it
            if test.get("followup"):
                followup_response = chat_with_agent_enhanced(conversation_history, test["followup"])
                print(f"Followup Response: {followup_response}")
            
            # Show session state after
            print(f"After - Last File: {agent_core._last_file}, Current Dir: {agent_core._current_directory}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
        
        # Clear pending action between tests to avoid interference
        agent_core.pending_action = None
        print()
    
    print("🎯 Phase 4B Context Test Complete!")
    print(f"Final session state:")
    print(f"  Last Action: {agent_core._last_action}")
    print(f"  Last File: {agent_core._last_file}")
    print(f"  Current Directory: {agent_core._current_directory}")

if __name__ == "__main__":
    test_phase4b_context()
