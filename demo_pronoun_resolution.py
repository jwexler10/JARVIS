#!/usr/bin/env python3
"""
Manual Phase 4B Demo: Test pronoun resolution with manually set context
"""

import sys
import os
import agent_core
from agent_core import chat_with_agent_enhanced, _resolve_context_and_pronouns

def demo_pronoun_resolution():
    """Demo pronoun resolution with manually established context"""
    
    print("🧪 Manual Phase 4B Demo: Pronoun Resolution\n")
    
    # Manually set up session state as if we just read a file
    agent_core._current_directory = r"C:\Users\jwexl\Desktop\jarvis"
    agent_core._last_file = r"C:\Users\jwexl\Desktop\jarvis\agent_core.py"
    agent_core._last_action = "read"
    agent_core.pending_action = None
    
    print(f"📋 Simulated state after reading a file:")
    print(f"   Last File: {agent_core._last_file}")
    print(f"   Current Dir: {agent_core._current_directory}")
    print(f"   Last Action: {agent_core._last_action}")
    print()
    
    # Test cases for pronoun resolution
    test_intents = [
        {
            "command": "open it",
            "intent": {"is_file_command": True, "action": "open", "target": None, "pattern": "it", "confidence": 0.9}
        },
        {
            "command": "what's in this file?",
            "intent": {"is_file_command": True, "action": "read", "target": "this file", "pattern": None, "confidence": 0.95}
        },
        {
            "command": "delete that file",
            "intent": {"is_file_command": True, "action": "delete", "target": None, "pattern": "that file", "confidence": 0.9}
        },
        {
            "command": "list files here",
            "intent": {"is_file_command": True, "action": "list", "target": "here", "pattern": None, "confidence": 0.95}
        }
    ]
    
    for i, test in enumerate(test_intents, 1):
        print(f"=== Test {i}: {test['command']} ===")
        print(f"Original intent: {test['intent']}")
        
        # Test pronoun resolution
        enhanced_intent = _resolve_context_and_pronouns(test['intent'])
        print(f"Enhanced intent: {enhanced_intent}")
        print()
    
    print("🎯 Manual Demo Complete!")

if __name__ == "__main__":
    demo_pronoun_resolution()
