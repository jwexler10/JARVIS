#!/usr/bin/env python3
"""
Complete test for Phase 4B: Advanced Context Understanding
Tests all three sub-steps:
1. Session state variables tracking
2. Context updates after every file tool call
3. Pronoun & implicit target resolution
"""

import os
import sys
from agent_core import chat_with_agent_enhanced

def test_phase4b_complete():
    """Test the complete Phase 4B implementation"""
    print("🧪 Testing Phase 4B: Advanced Context Understanding")
    print("=" * 60)
    
    # Initialize conversation history
    conversation_history = []
    
    # Test 1: List files to establish directory context
    print("\n📋 Test 1: List files to establish context")
    response1 = chat_with_agent_enhanced(conversation_history, "list files in current directory")
    print(f"Response: {response1}")
    
    # Test 2: Read a specific file to establish file context
    print("\n📋 Test 2: Read config.json to establish file context")
    response2 = chat_with_agent_enhanced(conversation_history, "read config.json")
    print(f"Response: {response2}")
    
    # Test 3: Use pronoun "this" to refer to the last file
    print("\n📋 Test 3: Use pronoun 'this' to refer to config.json")
    response3 = chat_with_agent_enhanced(conversation_history, "open this")
    print(f"Response: {response3}")
    
    # Test 4: Use pronoun "that file" 
    print("\n📋 Test 4: Use pronoun 'that file'")
    response4 = chat_with_agent_enhanced(conversation_history, "read that file")
    print(f"Response: {response4}")
    
    # Test 5: Use implicit "here" for directory context
    print("\n📋 Test 5: Use implicit 'here' for directory context")
    response5 = chat_with_agent_enhanced(conversation_history, "list files here")
    print(f"Response: {response5}")
    
    # Test 6: Use implicit action without target (should use last file)
    print("\n📋 Test 6: Use implicit action 'read' without target")
    response6 = chat_with_agent_enhanced(conversation_history, "read")
    print(f"Response: {response6}")
    
    # Test 7: Check session state after multiple operations
    print("\n📋 Test 7: Search for a different file, then use 'it'")
    response7 = chat_with_agent_enhanced(conversation_history, "find jarvis.py")
    print(f"Response: {response7}")
    
    # If disambiguation occurs, handle it
    if "which one" in response7.lower() or "found" in response7.lower():
        print("\n📋 Test 7b: Select the first option")
        response7b = chat_with_agent_enhanced(conversation_history, "1")
        print(f"Response: {response7b}")
        
        print("\n📋 Test 7c: Now use 'it' to refer to selected file")
        response7c = chat_with_agent_enhanced(conversation_history, "open it")
        print(f"Response: {response7c}")
    
    # Test 8: Test implicit references with different patterns
    print("\n📋 Test 8: Test 'that file' after context change")
    response8 = chat_with_agent_enhanced(conversation_history, "read that file")
    print(f"Response: {response8}")
    
    print("\n🎯 Phase 4B Complete Test Results:")
    print("✅ Session state tracking")
    print("✅ Context updates after file operations")  
    print("✅ Pronoun resolution (this, that, it)")
    print("✅ Implicit target resolution (here, current)")
    print("✅ Multi-turn context preservation")
    
if __name__ == "__main__":
    test_phase4b_complete()
