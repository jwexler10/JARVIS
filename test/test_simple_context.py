#!/usr/bin/env python3
"""
Simple Phase 4B Test: Context and Pronoun Resolution
Test a complete workflow with session state tracking and pronoun resolution.
"""

import sys
import os
import agent_core
from agent_core import chat_with_agent_enhanced

def test_simple_context_workflow():
    """Test a simple workflow with context tracking"""
    
    print("🧪 Simple Phase 4B Test: Context and Pronoun Resolution\n")
    
    # Reset session state
    agent_core._current_directory = os.getcwd()
    agent_core._last_file = None
    agent_core._last_action = None
    agent_core.pending_action = None
    
    # Step 1: Read a specific file that exists
    print("=== Step 1: Read agent_core.py ===")
    conversation_history = []
    response1 = chat_with_agent_enhanced(conversation_history, "read agent_core.py")
    print(f"Response: {response1[:200]}...")
    print(f"Session State: Last File: {agent_core._last_file}")
    print()
    
    # Clear any pending actions
    agent_core.pending_action = None
    
    # Step 2: Use pronoun "it" to refer to the same file
    print("=== Step 2: Open it (should resolve to agent_core.py) ===")
    conversation_history = []  # Fresh conversation
    response2 = chat_with_agent_enhanced(conversation_history, "open it")
    print(f"Response: {response2}")
    print(f"Session State: Last File: {agent_core._last_file}")
    print()
    
    # Clear any pending actions
    agent_core.pending_action = None
    
    # Step 3: List files "here"
    print("=== Step 3: List files here ===")
    conversation_history = []  # Fresh conversation
    response3 = chat_with_agent_enhanced(conversation_history, "list files here")
    print(f"Response: {response3[:300]}...")
    print(f"Session State: Current Dir: {agent_core._current_directory}")
    print()
    
    # Clear any pending actions
    agent_core.pending_action = None
    
    # Step 4: Test "this file" reference
    print("=== Step 4: what's in this file? (should use last file) ===")
    conversation_history = []  # Fresh conversation
    response4 = chat_with_agent_enhanced(conversation_history, "what's in this file?")
    print(f"Response: {response4[:200]}...")
    print(f"Session State: Last File: {agent_core._last_file}")
    
    print("\n🎯 Simple Phase 4B Test Complete!")
    print(f"Final State:")
    print(f"  Last Action: {agent_core._last_action}")
    print(f"  Last File: {agent_core._last_file}")
    print(f"  Current Directory: {agent_core._current_directory}")

if __name__ == "__main__":
    test_simple_context_workflow()
