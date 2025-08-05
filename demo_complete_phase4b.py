#!/usr/bin/env python3
"""
Complete Phase 4B Demo: End-to-End Context and Pronoun Resolution
This demonstrates the full Phase 4B functionality working correctly.
"""

import sys
import os
import agent_core
from agent_core import chat_with_agent_enhanced

def demo_complete_phase4b():
    """Demo complete Phase 4B workflow with direct file paths and pronoun resolution"""
    
    print("🧪 Complete Phase 4B Demo: Context-Aware File Operations\n")
    
    # Reset session state
    agent_core._current_directory = os.getcwd()
    agent_core._last_file = None
    agent_core._last_action = None
    agent_core.pending_action = None
    
    # Use full path to avoid disambiguation issues
    jarvis_path = r"C:\Users\jwexl\Desktop\jarvis\jarvis.py"
    
    print("=== Step 1: Read a specific file (establishes context) ===")
    conversation_history = []
    
    # Simulate reading a specific file that exists
    if os.path.exists(jarvis_path):
        response1 = chat_with_agent_enhanced(conversation_history, f"read {jarvis_path}")
        print(f"Response: {response1[:200]}...")
    else:
        # Fallback to reading config.json which should exist
        config_path = r"C:\Users\jwexl\Desktop\jarvis\config.json"
        response1 = chat_with_agent_enhanced(conversation_history, f"read {config_path}")
        print(f"Response: {response1[:200]}...")
    
    print(f"Context after Step 1: Last File = {agent_core._last_file}")
    print(f"                        Last Action = {agent_core._last_action}")
    print()
    
    # Clear pending actions to start fresh
    agent_core.pending_action = None
    
    print("=== Step 2: Use 'it' to refer to the same file ===")
    conversation_history = []  # Fresh conversation
    response2 = chat_with_agent_enhanced(conversation_history, "open it")
    print(f"Response: {response2}")
    print(f"Context after Step 2: Last File = {agent_core._last_file}")
    print()
    
    # Clear pending actions
    agent_core.pending_action = None
    
    print("=== Step 3: List files in current location ===")
    conversation_history = []
    response3 = chat_with_agent_enhanced(conversation_history, "list files here")
    print(f"Response: {response3[:300]}...")
    print(f"Context after Step 3: Current Dir = {agent_core._current_directory}")
    print()
    
    # Clear pending actions
    agent_core.pending_action = None
    
    print("=== Step 4: Read 'this file' (should use context) ===")
    conversation_history = []
    response4 = chat_with_agent_enhanced(conversation_history, "what's in this file?")
    print(f"Response: {response4[:200]}...")
    print(f"Context after Step 4: Last File = {agent_core._last_file}")
    print()
    
    print("=== Step 5: Test fallback when no context exists ===")
    # Clear session state to test fallback
    agent_core._last_file = None
    agent_core._last_action = None
    agent_core.pending_action = None
    
    conversation_history = []
    response5 = chat_with_agent_enhanced(conversation_history, "open it")
    print(f"Response (no context): {response5[:200]}...")
    print()
    
    print("🎯 Complete Phase 4B Demo Finished!")
    print(f"Final State:")
    print(f"  Last Action: {agent_core._last_action}")
    print(f"  Last File: {agent_core._last_file}")
    print(f"  Current Directory: {agent_core._current_directory}")

if __name__ == "__main__":
    demo_complete_phase4b()
