#!/usr/bin/env python3
"""
Test script for Phase 4A: Invisible Content Scanning & Summaries
Tests the enhanced disambiguation with file content summaries.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import agent_core
from agent_core import chat_with_agent_enhanced
from tools import summarize_text, get_file_preview

def test_summarization_functions():
    """Test the core summarization functions"""
    print("🧪 Testing Phase 4A: Content Scanning & Summaries")
    print("=" * 60)
    
    # Test 1: Basic text summarization
    print("\n📋 Test 1: Basic text summarization")
    sample_text = """
    This is a Python script that implements a file management system for JARVIS.
    It contains functions for listing files, reading file contents, and moving files around.
    The script uses OpenAI's GPT-4 model to provide intelligent file operations.
    It also includes error handling and logging functionality.
    """
    
    summary = summarize_text(sample_text, max_sentences=1)
    print(f"Original text: {sample_text.strip()}")
    print(f"Summary: {summary}")
    
    # Test 2: File preview functionality
    print("\n📋 Test 2: File preview functionality")
    
    # Test with agent_core.py
    if os.path.exists("agent_core.py"):
        preview = get_file_preview("agent_core.py", max_chars=300)
        print(f"Preview of agent_core.py: {preview[:100]}...")
        
        summary = summarize_text(preview, max_sentences=1)
        print(f"Summary: {summary}")
    
    # Test 3: Different file types
    print("\n📋 Test 3: File type handling")
    test_files = ["jarvis.py", "tools.py", "config.json"]
    
    for filename in test_files:
        if os.path.exists(filename):
            print(f"\n📄 {filename}:")
            preview = get_file_preview(filename, max_chars=200)
            summary = summarize_text(preview, max_sentences=1)
            print(f"   Summary: {summary}")

def test_enhanced_disambiguation():
    """Test the enhanced disambiguation with summaries"""
    print("\n" + "=" * 60)
    print("🧪 Testing Enhanced Disambiguation with Summaries")
    print("=" * 60)
    
    # Reset pending action
    agent_core.pending_action = None
    
    # Test 1: Ambiguous Python file command
    print("\n📋 Test 1: Enhanced Python file disambiguation")
    print("Command: 'Read a Python file'")
    
    conversation_history = [
        {"role": "system", "content": "You are JARVIS with enhanced file operation capabilities and content summaries."}
    ]
    
    response = chat_with_agent_enhanced(conversation_history, "Read a Python file")
    print(f"Response:\n{response}")
    print(f"\nPending action set: {agent_core.pending_action is not None}")
    
    # Test 2: If we have pending action, test clarification
    if agent_core.pending_action:
        print("\n📋 Test 2: Clarification with enhanced context")
        print("Follow-up: '1'")
        
        clarification_response = agent_core.handle_clarification("1")
        print(f"Response: {clarification_response}")
        print(f"Pending action cleared: {agent_core.pending_action is None}")

def test_edge_cases():
    """Test edge cases for summarization"""
    print("\n" + "=" * 60)
    print("🧪 Testing Edge Cases")
    print("=" * 60)
    
    # Test empty text
    print("\n📋 Test 1: Empty text")
    empty_summary = summarize_text("", max_sentences=1)
    print(f"Empty text summary: {empty_summary}")
    
    # Test very long text
    print("\n📋 Test 2: Very long text")
    long_text = "This is a test. " * 200  # Create very long text
    long_summary = summarize_text(long_text, max_sentences=1)
    print(f"Long text summary: {long_summary}")
    
    # Test non-existent file
    print("\n📋 Test 3: Non-existent file")
    nonexistent_preview = get_file_preview("nonexistent_file.txt")
    print(f"Non-existent file preview: {nonexistent_preview}")

if __name__ == "__main__":
    try:
        test_summarization_functions()
        test_enhanced_disambiguation()
        test_edge_cases()
        print("\n🎉 All Phase 4A tests completed!")
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
