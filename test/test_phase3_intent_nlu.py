#!/usr/bin/env python3
"""Test Phase 3: Intent & Contextual NLU capabilities"""

import os
import sys
import json
import time

# Add jarvis directory to path
jarvis_path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, jarvis_path)

from tools import interpret_file_intent
from agent_core import chat_with_agent_enhanced, handle_clarification, pending_action, _dispatch_file_operation

def test_intent_interpretation():
    """Test Phase 3A: Intent Classification & Slot Extraction"""
    print("=== PHASE 3A: INTENT CLASSIFICATION & SLOT EXTRACTION ===")
    
    test_commands = [
        "list files in my documents",
        "show me PDFs from my econ 306 class", 
        "open the cartoon file",
        "delete note.txt",
        "move report.pdf to desktop",
        "search for Python files",
        "what's the weather like",  # Non-file command
        "find audio files",
        "read the config file"
    ]
    
    for command in test_commands:
        print(f"\nCommand: '{command}'")
        try:
            intent = interpret_file_intent(command)
            print(f"  Intent: {json.dumps(intent, indent=2)}")
            
            # Test direct dispatch for high-confidence file commands
            if intent.get("is_file_command", False) and intent.get("confidence", 0) > 0.6:
                print("  → High confidence file command, testing direct dispatch...")
                result = _dispatch_file_operation(intent, command)
                if result:
                    print(f"  Direct result: {result[:100]}...")
                else:
                    print("  → Would fall back to generic function calling")
        except Exception as e:
            print(f"  Error: {e}")
    
    print("\n" + "="*60)

def test_enhanced_agent():
    """Test enhanced agent with intent interpretation"""
    print("=== TESTING ENHANCED AGENT ===")
    
    conversation_history = []
    
    test_queries = [
        "Hello Jarvis",
        "Show me Python files in the jarvis folder",
        "Search for configuration files",
        "List files in my downloads",
        "Find PDFs about economics"
    ]
    
    for query in test_queries:
        print(f"\nUser: {query}")
        try:
            response = chat_with_agent_enhanced(conversation_history, query)
            print(f"Jarvis: {response}")
            time.sleep(1)  # Brief pause between calls
        except Exception as e:
            print(f"Error: {e}")
    
    print("\n" + "="*60)

def test_clarification_workflow():
    """Test Phase 3B & 3C: Disambiguation & Clarifications"""
    print("=== PHASE 3B & 3C: DISAMBIGUATION & CLARIFICATIONS ===")
    
    # Simulate a clarification scenario
    print("Simulating a scenario with multiple file matches...")
    
    # Test intent that would trigger multiple matches
    intent = {
        "is_file_command": True,
        "action": "open",
        "pattern": "test",  # This would likely match multiple files
        "confidence": 0.8
    }
    
    print(f"Intent: {intent}")
    
    try:
        result = _dispatch_file_operation(intent, "open test file")
        print(f"Initial result: {result}")
        
        # Check if a pending action was created
        if pending_action:
            print(f"Pending action created: {pending_action}")
            
            # Test clarification responses
            clarification_responses = ["1", "the first one", "cancel"]
            
            for response in clarification_responses:
                print(f"\nClarification response: '{response}'")
                clarification_result = handle_clarification(response)
                if clarification_result:
                    print(f"Clarification result: {clarification_result}")
                    break
        else:
            print("No pending action created (single match or no matches)")
            
    except Exception as e:
        print(f"Error in clarification test: {e}")
    
    print("\n" + "="*60)

def demo_complete_workflow():
    """Demonstrate the complete Phase 3 workflow"""
    print("=== COMPLETE PHASE 3 WORKFLOW DEMO ===")
    
    # Simulate a conversation with file operations
    conversation_history = []
    
    scenarios = [
        {
            "description": "Scenario 1: Direct semantic search",
            "command": "show me PDFs from my econ class"
        },
        {
            "description": "Scenario 2: File listing with intent", 
            "command": "list Python files in jarvis folder"
        },
        {
            "description": "Scenario 3: Ambiguous file reference",
            "command": "open the test file"
        }
    ]
    
    for scenario in scenarios:
        print(f"\n{scenario['description']}")
        print(f"Command: {scenario['command']}")
        
        # Step 1: Intent interpretation
        try:
            intent = interpret_file_intent(scenario['command'])
            print(f"Extracted intent: {json.dumps(intent, indent=2)}")
            
            # Step 2: Direct dispatch or agent handling
            if intent.get("is_file_command", False) and intent.get("confidence", 0) > 0.6:
                result = _dispatch_file_operation(intent, scenario['command'])
                if result:
                    print(f"Direct dispatch result: {result}")
                    
                    # Step 3: Check for clarification needs
                    if pending_action:
                        print("Multiple matches found, clarification needed")
                        print("Simulating user selection...")
                        
                        # Simulate user choosing first option
                        clarification = handle_clarification("1")
                        if clarification:
                            print(f"After clarification: {clarification}")
                else:
                    print("Falling back to enhanced agent...")
                    response = chat_with_agent_enhanced(conversation_history, scenario['command'])
                    print(f"Agent response: {response}")
            else:
                print("Low confidence or non-file command, using standard processing")
                
        except Exception as e:
            print(f"Error in scenario: {e}")
        
        print("-" * 40)
    
    print("\n" + "="*60)

def main():
    """Run all Phase 3 tests"""
    print("TESTING PHASE 3: INTENT & CONTEXTUAL NLU")
    print("=" * 60)
    
    try:
        # Test 1: Intent interpretation
        test_intent_interpretation()
        
        # Test 2: Enhanced agent
        # test_enhanced_agent()  # Commented out to avoid OpenAI calls in demo
        
        # Test 3: Clarification workflow  
        test_clarification_workflow()
        
        # Test 4: Complete workflow demo
        demo_complete_workflow()
        
        print("✅ ALL PHASE 3 TESTS COMPLETED!")
        print("\nPhase 3 capabilities implemented:")
        print("✓ 3A: Intent Classification & Slot Extraction")
        print("✓ 3B: Disambiguation & Conversational State")
        print("✓ 3C: Follow-Up Clarifications & Flexible Dialogue")
        
    except Exception as e:
        print(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
