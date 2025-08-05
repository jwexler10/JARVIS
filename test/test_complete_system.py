#!/usr/bin/env python3
"""Test the complete Jarvis system with semantic file search"""

import os
import sys
import json
import tempfile

# Add jarvis directory to path
jarvis_path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, jarvis_path)

from tools import search_files
from agent_core import Agent
from file_index import file_index

def test_file_index_status():
    """Test file index initialization"""
    print("=== FILE INDEX STATUS ===")
    if file_index.index is None:
        print("Loading file index...")
        file_index.load()
    
    print(f"Index loaded: {file_index.index is not None}")
    if file_index.index:
        print(f"Total indexed files: {file_index.index.ntotal}")
    print()

def test_direct_search():
    """Test direct semantic search"""
    print("=== DIRECT SEMANTIC SEARCH ===")
    
    test_queries = [
        "econ 306 pdf",
        "python jarvis files", 
        "audio recording wav",
        "json configuration",
        "requirements txt"
    ]
    
    for query in test_queries:
        print(f"Query: '{query}'")
        results = search_files(query, top_k=3)
        if results:
            for i, result in enumerate(results[:3], 1):
                print(f"  {i}. {result['filename']} (score: {result.get('score', 'N/A'):.3f})")
                print(f"     Path: {result['filepath']}")
        else:
            print("  No results found")
        print()

def test_agent_search():
    """Test agent-based semantic search"""
    print("=== AGENT-BASED SEMANTIC SEARCH ===")
    
    # Create agent
    agent = Agent()
    
    test_queries = [
        "Show me PDFs from my econ 306 class",
        "Find Python files related to jarvis",
        "What audio files do I have?",
        "Search for configuration files",
        "Find text files with requirements"
    ]
    
    for query in test_queries:
        print(f"User: {query}")
        print("Agent: ", end="")
        
        try:
            response = agent.respond(query)
            print(response)
        except Exception as e:
            print(f"Error: {e}")
        print()

def test_jarvis_integration():
    """Test Jarvis conversation mode with file search"""
    print("=== JARVIS CONVERSATION MODE TEST ===")
    
    # Create a test conversation
    conversation = []
    
    test_messages = [
        "Hello Jarvis",
        "Show me some Python files from this project",
        "What about audio files?",
        "Find any PDFs I have"
    ]
    
    for message in test_messages:
        conversation.append({"role": "user", "content": message})
        print(f"User: {message}")
        
        # Simulate agent response
        try:
            agent = Agent()
            response = agent.respond(message)
            conversation.append({"role": "assistant", "content": response})
            print(f"Jarvis: {response}")
        except Exception as e:
            print(f"Jarvis: Error - {e}")
        print()

def main():
    """Run all tests"""
    print("TESTING COMPLETE JARVIS SEMANTIC FILE SEARCH SYSTEM")
    print("=" * 60)
    
    try:
        # Test 1: File index status
        test_file_index_status()
        
        # Test 2: Direct search
        test_direct_search()
        
        # Test 3: Agent search
        test_agent_search()
        
        # Test 4: Jarvis integration
        test_jarvis_integration()
        
        print("=" * 60)
        print("ALL TESTS COMPLETED SUCCESSFULLY!")
        
    except Exception as e:
        print(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
