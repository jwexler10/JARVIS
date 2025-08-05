#!/usr/bin/env python3
"""
Test script for the semantic file search functionality
"""

from tools import search_files
from agent_core import chat_with_agent

def test_search_files():
    """Test the search_files function directly"""
    print("🔍 Testing search_files function...")
    
    test_queries = [
        "econ 306 pdf",
        "Python files",
        "jarvis configuration",
        "audio files",
        "recent documents"
    ]
    
    for query in test_queries:
        print(f"\nQuery: '{query}'")
        try:
            results = search_files(query, top_k=3)
            if results:
                print(f"Found {len(results)} results:")
                for i, hit in enumerate(results, 1):
                    print(f"  {i}. {hit.get('name', 'Unknown')} - Score: {hit.get('score', 0):.3f}")
                    print(f"     Path: {hit.get('path', 'Unknown')}")
            else:
                print("No results found")
        except Exception as e:
            print(f"Error: {e}")

def test_agent_integration():
    """Test the agent integration with semantic file search"""
    print("\n\n🤖 Testing agent integration...")
    
    test_queries = [
        "Show me PDFs from my econ 306 class",
        "Find Python files related to jarvis",
        "What audio files do I have?",
        "Search for configuration files"
    ]
    
    for query in test_queries:
        print(f"\nAgent Query: '{query}'")
        try:
            history = [
                {"role": "system", "content": "You are JARVIS with access to file operations and semantic file search."}
            ]
            result = chat_with_agent(history, query)
            print(f"Agent Response: {result}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    test_search_files()
    print("\n" + "="*60)
    test_agent_integration()
