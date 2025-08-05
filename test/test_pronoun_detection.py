#!/usr/bin/env python3
"""
Test script for enhanced pronoun-based file operation detection
"""

from jarvis import process_command

def test_enhanced_pronoun_detection():
    """Test that various natural language file operations are detected"""
    
    # Create conversation history with file context
    conversation_history = [
        {
            "role": "system", 
            "content": "You are JARVIS..."
        },
        {
            "role": "user", 
            "content": "is there a file called test.txt on my desktop?"
        },
        {
            "role": "assistant", 
            "content": "Yes, there is a file named 'test.txt' on your desktop."
        }
    ]
    
    print("🔧 Testing enhanced natural language file operation detection...")
    print("📋 Conversation context:")
    for i, msg in enumerate(conversation_history):
        if msg["role"] != "system":
            print(f"  {i}. {msg['role']}: {msg['content']}")
    
    # Test various natural language commands
    test_commands = [
        "delete it please",
        "erase it",
        "get rid of it", 
        "trash it",
        "can you throw it away",
        "open it",
        "show it to me",
        "display it",
        "move it somewhere else",
        "copy it",
        "rename it"
    ]
    
    print(f"\n🎯 Testing {len(test_commands)} different commands...")
    
    success_count = 0
    for i, cmd in enumerate(test_commands, 1):
        print(f"\n{i}. Testing: '{cmd}'")
        
        try:
            response, should_exit = process_command(
                cmd, 
                conversation_history.copy(), 
                text_mode=True, 
                speaker="Jason", 
                emotion=None
            )
            
            # Check if the response indicates it was routed to the agent
            if any(keyword in response.lower() for keyword in ["file", "test.txt", "desktop"]):
                print(f"   ✅ SUCCESS: Routed to file agent")
                success_count += 1
            else:
                print(f"   ❌ FAILURE: Not routed to file agent")
                print(f"   📝 Response: {response[:100]}...")
                
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
    
    print(f"\n📊 Results: {success_count}/{len(test_commands)} commands successfully detected")
    
    if success_count == len(test_commands):
        print("🎉 ALL TESTS PASSED! Enhanced natural language detection is working perfectly!")
    elif success_count >= len(test_commands) * 0.8:
        print("✅ Most tests passed! Natural language detection is working well.")
    else:
        print("⚠️ Some tests failed. Natural language detection needs improvement.")

if __name__ == "__main__":
    test_enhanced_pronoun_detection()
