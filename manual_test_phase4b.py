#!/usr/bin/env python3
"""
Manual test for Phase 4B: Advanced Context Understanding
Tests core pronoun resolution functionality step by step
"""

import os
import sys
from agent_core import chat_with_agent_enhanced, _last_file, _current_directory, _last_action

def manual_test_phase4b():
    """Manual test Phase 4B to verify context tracking"""
    print("🧪 Manual Testing Phase 4B: Advanced Context Understanding")
    print("=" * 60)
    
    # Single conversation to maintain context
    conversation = []
    
    print("\n📋 Step 1: Read config.json to establish file context")
    response1 = chat_with_agent_enhanced(conversation, "read config.json")
    print(f"Session state after step 1: last_file={_last_file}, current_dir={_current_directory}")
    print(f"Response: {response1[:100]}...")
    
    print("\n📋 Step 2: Use pronoun 'this' to refer to config.json")
    response2 = chat_with_agent_enhanced(conversation, "open this")
    print(f"Session state after step 2: last_file={_last_file}, current_dir={_current_directory}")
    print(f"Response: {response2[:100]}...")
    
    print("\n📋 Step 3: Use pronoun 'it'")
    response3 = chat_with_agent_enhanced(conversation, "read it")
    print(f"Session state after step 3: last_file={_last_file}, current_dir={_current_directory}")
    print(f"Response: {response3[:100]}...")
    
    print("\n📋 Step 4: Use implicit action 'read' without target")
    response4 = chat_with_agent_enhanced(conversation, "read")
    print(f"Session state after step 4: last_file={_last_file}, current_dir={_current_directory}")
    print(f"Response: {response4[:100]}...")
    
    print("\n🎯 Manual Test Results Complete")
    
if __name__ == "__main__":
    manual_test_phase4b()
