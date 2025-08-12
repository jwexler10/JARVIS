#!/usr/bin/env python3
"""
Comprehensive test of the session-aware research system.
Tests all conversation memory features and research continuity.
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from agent_core import chat_with_agent, session

def test_comprehensive_session_flows():
    """Test comprehensive session-aware conversation flows"""
    
    print("🧪 Testing Comprehensive Session-Aware Research Flows")
    print("=" * 60)
    
    # Reset session state
    session.clear()
    conversation_history = []
    
    print("\n🔄 Test Flow 1: Research → Disambiguate → Save")
    print("-" * 50)
    
    # Step 1: Research with disambiguation
    print("👤 User: research latest Python frameworks")
    response1 = chat_with_agent(conversation_history, "research latest Python frameworks")
    print(f"🤖 Jarvis: {response1[:100]}...")
    
    # Check session state
    print(f"📊 Session after research: awaiting_disambiguation={session.awaiting_disambiguation}")
    print(f"📊 Available URLs: {len(session.last_urls)}")
    
    # Step 2: Pick option
    if session.awaiting_disambiguation and session.last_urls:
        print("\n👤 User: 1")
        response2 = chat_with_agent(conversation_history, "1")
        print(f"🤖 Jarvis: {response2[:100]}...")
        
        # Check session state after selection
        print(f"📊 Session after selection: has_summary={bool(session.last_summary)}")
        print(f"📊 Summary length: {len(session.last_summary)} chars")
        
        # Step 3: Save the research
        if session.last_summary:
            print("\n👤 User: save that to python_frameworks.txt")
            response3 = chat_with_agent(conversation_history, "save that to python_frameworks.txt")
            print(f"🤖 Jarvis: {response3}")
    
    print("\n🔄 Test Flow 2: One-Command Research + Save")
    print("-" * 50)
    
    # Reset session
    session.clear()
    conversation_history = []
    
    print("👤 User: research Vue.js best practices and save to vue_practices.txt")
    response4 = chat_with_agent(conversation_history, "research Vue.js best practices and save to vue_practices.txt")
    print(f"🤖 Jarvis: {response4[:150]}...")
    
    # Handle any disambiguation if needed
    if session.awaiting_disambiguation and session.last_urls:
        print("\n👤 User: first")
        response5 = chat_with_agent(conversation_history, "first")
        print(f"🤖 Jarvis: {response5[:100]}...")
    
    print("\n🔄 Test Flow 3: Multiple Research Sessions")
    print("-" * 50)
    
    # Reset session
    session.clear()
    conversation_history = []
    
    # First research
    print("👤 User: look up machine learning trends")
    response6 = chat_with_agent(conversation_history, "look up machine learning trends")
    print(f"🤖 Jarvis: {response6[:100]}...")
    
    if session.awaiting_disambiguation and session.last_urls:
        print("\n👤 User: 2")
        response7 = chat_with_agent(conversation_history, "2")
        print(f"🤖 Jarvis: {response7[:100]}...")
    
    # Save first research
    if session.last_summary:
        print("\n👤 User: write that to ml_trends.txt")
        response8 = chat_with_agent(conversation_history, "write that to ml_trends.txt")
        print(f"🤖 Jarvis: {response8}")
    
    # Second research (should reset session)
    print("\n👤 User: research blockchain innovations")
    response9 = chat_with_agent(conversation_history, "research blockchain innovations")
    print(f"🤖 Jarvis: {response9[:100]}...")
    
    # Check that session was updated for new research
    print(f"📊 Session query changed to: '{session.last_query}'")
    
    print("\n🔄 Test Flow 4: Error Handling")
    print("-" * 50)
    
    # Test saving when no research exists
    session.clear()
    conversation_history = []
    
    print("👤 User: save that summary")
    response10 = chat_with_agent(conversation_history, "save that summary")
    print(f"🤖 Jarvis: {response10}")
    
    # Test invalid disambiguation choice
    session.last_urls = ["https://example1.com", "https://example2.com"]
    session.awaiting_disambiguation = True
    
    print("\n👤 User: 5")
    response11 = chat_with_agent(conversation_history, "5")
    print(f"🤖 Jarvis: {response11}")
    
    print("\n✅ Comprehensive session flow testing complete!")

def test_session_persistence():
    """Test that session state persists correctly across interactions"""
    
    print("\n🧪 Testing Session State Persistence")
    print("=" * 40)
    
    # Setup initial state
    session.clear()
    session.last_summary = "This is a test summary about AI trends."
    session.last_query = "AI trends"
    session.last_urls = ["https://example1.com", "https://example2.com"]
    session.awaiting_disambiguation = False
    
    conversation_history = []
    
    # Test that save commands work with existing state
    print("👤 User: save that to ai_summary.txt")
    response = chat_with_agent(conversation_history, "save that to ai_summary.txt")
    print(f"🤖 Jarvis: {response}")
    
    # Test session preservation after save
    print(f"📊 Session preserved: summary={bool(session.last_summary)}")
    print(f"📊 Query preserved: '{session.last_query}'")
    
    print("\n✅ Session persistence test complete!")

if __name__ == "__main__":
    try:
        test_comprehensive_session_flows()
        test_session_persistence()
        
        print(f"\n🎯 Final Session State Summary:")
        print(f"   Last Query: '{session.last_query}'")
        print(f"   Has Summary: {bool(session.last_summary)}")
        print(f"   Summary Length: {len(session.last_summary)} characters")
        print(f"   Available URLs: {len(session.last_urls)}")
        print(f"   Awaiting Disambiguation: {session.awaiting_disambiguation}")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
