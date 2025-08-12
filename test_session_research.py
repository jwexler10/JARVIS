#!/usr/bin/env python3
"""
Test the new session-aware research and file saving capabilities.
Tests the conversation memory for seamless research → save workflows.
"""

import sys
sys.path.append('.')

from agent_core import chat_with_agent, session

def test_session_research():
    """Test the session-aware research system"""
    print("🧪 Testing Session-Aware Research System")
    print("=" * 50)
    
    conversation_history = []
    
    # Test 1: Combined research + save command
    print("\n🧪 Test 1: Combined 'research X and save to Y.txt' command")
    query1 = "research best React hooks patterns and save to react_hooks.txt"
    print(f"👤 User: {query1}")
    
    response1 = chat_with_agent(conversation_history, query1)
    print(f"🤖 Jarvis: {response1[:200]}...")
    
    print(f"\n📊 Session state after Test 1:")
    print(f"  - Last query: '{session.last_query}'")
    print(f"  - Has summary: {len(session.last_summary) > 0}")
    print(f"  - URLs available: {len(session.last_urls)}")
    print(f"  - Awaiting disambiguation: {session.awaiting_disambiguation}")
    
    # Test 2: Save last research (if no combined save happened)
    if not session.awaiting_disambiguation and session.last_summary:
        print(f"\n🧪 Test 2: Save last research to different file")
        query2 = "save that to hooks_reference.txt"
        print(f"👤 User: {query2}")
        
        response2 = chat_with_agent(conversation_history, query2)
        print(f"🤖 Jarvis: {response2}")
    
    # Test 3: Handle disambiguation if it occurred
    elif session.awaiting_disambiguation:
        print(f"\n🧪 Test 3: Handle disambiguation")
        query3 = "1"  # Pick first option
        print(f"👤 User: {query3}")
        
        response3 = chat_with_agent(conversation_history, query3)
        print(f"🤖 Jarvis: {response3[:200]}...")
        
        # Now test saving the result
        if session.last_summary:
            print(f"\n🧪 Test 4: Save disambiguated research")
            query4 = "save that summary to react_hooks_final.txt"
            print(f"👤 User: {query4}")
            
            response4 = chat_with_agent(conversation_history, query4)
            print(f"🤖 Jarvis: {response4}")
    
    # Test 5: Research without save, then save later
    print(f"\n🧪 Test 5: Separate research and save")
    query5 = "research latest JavaScript ES2024 features"
    print(f"👤 User: {query5}")
    
    response5 = chat_with_agent(conversation_history, query5)
    print(f"🤖 Jarvis: {response5[:200]}...")
    
    if not session.awaiting_disambiguation and session.last_summary:
        print(f"\n🧪 Test 6: Save the separate research")
        query6 = "write that to es2024_features.txt"
        print(f"👤 User: {query6}")
        
        response6 = chat_with_agent(conversation_history, query6)
        print(f"🤖 Jarvis: {response6}")
    
    print(f"\n📊 Final session state:")
    print(f"  - Last query: '{session.last_query}'")
    print(f"  - Summary length: {len(session.last_summary)} chars")
    print(f"  - URLs available: {len(session.last_urls)}")
    print(f"  - Awaiting disambiguation: {session.awaiting_disambiguation}")
    
    print(f"\n✅ Session-aware research test completed!")

def test_session_helpers():
    """Test the helper functions"""
    print(f"\n🧪 Testing Session Helper Functions")
    print("=" * 40)
    
    from agent_core import (
        is_save_last_research_command,
        detect_combined_research_and_save,
        is_disambiguation_response,
        extract_selection_number
    )
    
    # Test save detection
    save_tests = [
        ("save that to summary.txt", "summary.txt"),
        ("write that summary to notes.txt", "notes.txt"),
        ("save it", "research_summary.txt"),
        ("create a file with that called results.txt", "results.txt"),
        ("tell me about cats", None)
    ]
    
    print("Save command detection:")
    for test_input, expected in save_tests:
        result = is_save_last_research_command(test_input)
        status = "✅" if result == expected else "❌"
        print(f"  {status} '{test_input}' → {result}")
    
    # Test combined research + save detection
    combined_tests = [
        ("research React hooks and save to hooks.txt", ("React hooks", "hooks.txt")),
        ("find Python tutorials and save it to python.txt", ("Python tutorials", "python.txt")),
        ("look up AI trends", (None, None))
    ]
    
    print(f"\nCombined research + save detection:")
    for test_input, expected in combined_tests:
        result = detect_combined_research_and_save(test_input)
        status = "✅" if result == expected else "❌"
        print(f"  {status} '{test_input}' → {result}")
    
    # Test disambiguation detection
    disambig_tests = [
        ("1", True),
        ("first", True),
        ("the second one", True),
        ("option 3", True),
        ("random text", False)
    ]
    
    print(f"\nDisambiguation response detection:")
    for test_input, expected in disambig_tests:
        result = is_disambiguation_response(test_input)
        status = "✅" if result == expected else "❌"
        print(f"  {status} '{test_input}' → {result}")
    
    # Test number extraction
    number_tests = [
        ("1", 1),
        ("first", 1),
        ("the second one", 2),
        ("option 3", 3),
        ("pick number 5", 5)
    ]
    
    print(f"\nNumber extraction:")
    for test_input, expected in number_tests:
        result = extract_selection_number(test_input)
        status = "✅" if result == expected else "❌"
        print(f"  {status} '{test_input}' → {result}")

if __name__ == "__main__":
    test_session_helpers()
    test_session_research()
