#!/usr/bin/env python3
"""
Interactive demonstration of Phase 3: Intent & Contextual NLU
Shows how Jarvis now understands vague file commands and handles disambiguation
"""

import os
import sys

# Add jarvis directory to path
jarvis_path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, jarvis_path)

from agent_core import chat_with_agent_enhanced, handle_clarification, pending_action
from file_index import file_index

def demo_phase3():
    """Interactive demo of Phase 3 capabilities"""
    print("🚀 PHASE 3 DEMO: Intent & Contextual NLU")
    print("=" * 50)
    print("This demo shows how Jarvis now has 'intuition' about file operations!")
    print("Try commands like:")
    print("  • 'show me some Python files'")
    print("  • 'find configuration files'") 
    print("  • 'open the cartoon file'")
    print("  • 'delete temp files'")
    print("  • 'search for audio files'")
    print("Type 'quit' to exit")
    print()
    
    # Ensure file index is loaded
    if file_index.index is None:
        print("🔍 Loading file index...")
        file_index.load()
        print("✅ File index ready")
        print()
    
    conversation_history = [
        {"role": "system", "content": "You are JARVIS with enhanced file operation intuition."}
    ]
    
    while True:
        try:
            # Check for pending clarification
            if pending_action:
                print(f"🤔 Waiting for clarification about {pending_action['action']} operation...")
                print(f"   Choose from {len(pending_action['candidates'])} candidates")
                user_input = input("Your clarification: ").strip()
                
                if user_input.lower() == 'quit':
                    break
                
                result = handle_clarification(user_input)
                if result:
                    print(f"🎯 {result}")
                    print()
                else:
                    print("❌ Clarification not understood. Try again.")
                    print()
                continue
            
            # Normal command input
            user_input = input("You: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'stop']:
                break
            
            if not user_input:
                continue
            
            print("🎯 Processing with Phase 3 intent interpretation...")
            
            # Use enhanced agent
            response = chat_with_agent_enhanced(conversation_history.copy(), user_input)
            print(f"JARVIS: {response}")
            print()
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            print()
    
    print("👋 Demo ended. Phase 3 capabilities demonstrated!")

if __name__ == "__main__":
    demo_phase3()
