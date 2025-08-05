#!/usr/bin/env python3
"""
Test script for Google commands integration with Jarvis
"""

from google_commands import handle_google_command

def test_google_commands():
    """Test various Google command patterns"""
    
    test_commands = [
        "Check my calendar",
        "What's on my schedule today?",
        "Schedule a meeting with Bob for tomorrow at 2pm",
        "Create an event called 'Doctor appointment' for next Friday at 10am",
        "Check my email",
        "Read my recent emails",
        "Show me my Google Drive files",
        "List my files in Drive"
    ]
    
    print("🧪 Testing Google Commands Integration\n")
    
    for i, command in enumerate(test_commands, 1):
        print(f"Test {i}: '{command}'")
        print("-" * 50)
        
        try:
            result = handle_google_command(command)
            if result:
                print(f"✅ Result: {result}")
            else:
                print("❌ No Google command matched")
        except Exception as e:
            print(f"❌ Error: {str(e)}")
        
        print("\n")

if __name__ == "__main__":
    test_google_commands()
