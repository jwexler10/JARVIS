#!/usr/bin/env python3
"""
Demonstration of Phase 3: Intent & Contextual NLU in action
This shows how Jarvis now has "intuition" to understand vague file commands
"""

import os
import sys
import json

# Add jarvis directory to path
jarvis_path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, jarvis_path)

from tools import interpret_file_intent
from agent_core import chat_with_agent_enhanced, handle_clarification, pending_action, _dispatch_file_operation

def demonstrate_phase3_intuition():
    """Show how Phase 3 gives Jarvis file operation intuition"""
    
    print("=" * 70)
    print("🧠 JARVIS PHASE 3: INTENT & CONTEXTUAL NLU DEMONSTRATION")
    print("   Now Jarvis has 'intuition' for vague file commands!")
    print("=" * 70)
    
    # Demonstrate vague commands that Phase 3 can now understand
    vague_commands = [
        {
            "command": "show me those Python files",
            "explanation": "Vague reference - but Jarvis knows you want Python files"
        },
        {
            "command": "find my config stuff", 
            "explanation": "Informal language - Jarvis understands 'config stuff'"
        },
        {
            "command": "open that requirements thing",
            "explanation": "Imprecise description - Jarvis maps to requirements.txt"
        },
        {
            "command": "list recent downloads",
            "explanation": "Natural language - Jarvis knows to check Downloads folder"
        },
        {
            "command": "search for my economics homework",
            "explanation": "Content-based search - uses semantic file indexing"
        }
    ]
    
    print("\n🎯 BEFORE Phase 3: These commands would confuse Jarvis")
    print("🎯 AFTER Phase 3: Jarvis understands intent and responds intelligently\n")
    
    for i, example in enumerate(vague_commands, 1):
        print(f"{i}. Command: '{example['command']}'")
        print(f"   Context: {example['explanation']}")
        
        # Show intent analysis
        try:
            intent = interpret_file_intent(example['command'])
            confidence = intent.get('confidence', 0)
            action = intent.get('action', 'unknown')
            
            if intent.get('is_file_command', False):
                print(f"   🧠 Jarvis thinks: 'This is a {action} operation' (confidence: {confidence:.2f})")
                print(f"   ✅ Jarvis now knows how to handle this!")
            else:
                print(f"   🤔 Jarvis thinks: 'This isn't about files'")
                print(f"   ➡️ Would route to general conversation")
            
        except Exception as e:
            print(f"   ❌ Intent analysis failed: {e}")
        
        print()
    
    print("=" * 70)
    print("🎉 PHASE 3 COMPLETE: JARVIS NOW HAS FILE OPERATION INTUITION!")
    print("=" * 70)
    
    # Show what this means for users
    print("\n📈 USER EXPERIENCE IMPROVEMENTS:")
    print("✓ More natural file commands")
    print("✓ Better disambiguation when multiple files match")  
    print("✓ Smarter follow-up clarifications")
    print("✓ Reduced need for precise syntax")
    print("✓ Context-aware file operations")
    
    print("\n🔧 TECHNICAL ACHIEVEMENTS:")
    print("✓ 3A: Intent Classification & Slot Extraction")
    print("✓ 3B: Disambiguation & Conversational State") 
    print("✓ 3C: Follow-Up Clarifications & Flexible Dialogue")
    
    print("\n🚀 NEXT STEPS:")
    print("• Phase 4: Advanced context understanding")
    print("• Phase 5: Predictive file suggestions")
    print("• Phase 6: Multi-step file workflows")

def show_real_world_scenarios():
    """Show real-world scenarios where Phase 3 helps"""
    
    print("\n" + "=" * 70)
    print("🌍 REAL-WORLD SCENARIOS WHERE PHASE 3 HELPS")
    print("=" * 70)
    
    scenarios = [
        {
            "scenario": "Student looking for homework",
            "before": "User: 'find my economics assignment'\nJarvis: 'I need more specific file names'",
            "after": "User: 'find my economics assignment'\nJarvis: 'I found 3 files related to economics. Which one: homework.pdf, notes.docx, or readings.pdf?'"
        },
        {
            "scenario": "Developer managing code",
            "before": "User: 'open the config file'\nJarvis: 'Which config file? There are many'",
            "after": "User: 'open the config file'\nJarvis: 'Opening config.json... [file opens automatically]'"
        },
        {
            "scenario": "User organizing downloads",
            "before": "User: 'show me recent stuff'\nJarvis: 'Please specify a directory and file type'",
            "after": "User: 'show me recent stuff'\nJarvis: 'Here are your recent downloads: report.pdf (2 hours ago), photo.jpg (yesterday)...'"
        }
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n{i}. {scenario['scenario'].upper()}")
        print(f"   Before Phase 3:")
        print(f"   {scenario['before']}")
        print(f"   After Phase 3:")
        print(f"   {scenario['after']}")
        print(f"   ✨ Much more intuitive!")

if __name__ == "__main__":
    demonstrate_phase3_intuition()
    show_real_world_scenarios()
    
    print(f"\n🎊 Phase 3 implementation complete! Jarvis now has file operation intuition.")
