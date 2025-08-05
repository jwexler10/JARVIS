#!/usr/bin/env python3
"""
Debug script to test the agent with token counting
"""

import json
from agent_core import chat_with_agent
import tiktoken

def count_tokens(text, model="gpt-4"):
    """Count tokens in text using tiktoken"""
    try:
        encoding = tiktoken.encoding_for_model(model)
        return len(encoding.encode(str(text)))
    except Exception as e:
        print(f"Error counting tokens: {e}")
        return len(str(text)) // 4  # rough estimate

def debug_agent_call():
    """Test the agent with debug output"""
    agent_history = [
        {'role': 'system', 'content': 
            'You are JARVIS with access to file operations. When users ask for files, use the list_files function. '
            'CURRENT WORKING DIRECTORY: C:\\Users\\jwexl\\Desktop\\jarvis '
            'DIRECTORY RESOLUTION: Your file tools can accept human-friendly folder names like '
            'jarvis folder on my desktop, documents folder, downloads, etc. and will resolve them automatically. '
            'When users mention jarvis folder or jarvis directory, they mean the current working directory. '
            'Use list_files(directory, pattern, recursive) and get_latest_file(directory, pattern) '
            'whenever the user refers to folders by name. You can use natural language for directories.'
        }
    ]
    
    print("Initial conversation history:")
    for i, msg in enumerate(agent_history):
        tokens = count_tokens(msg.get('content', ''))
        print(f"  Message {i}: {msg['role']} - {tokens} tokens")
    
    total_tokens = sum(count_tokens(msg.get('content', '')) for msg in agent_history)
    print(f"Total initial tokens: {total_tokens}")
    
    print("\nCalling agent...")
    try:
        response = chat_with_agent(agent_history, 'list all python files in the jarvis folder on my desktop')
        print(f"Agent response: {response}")
        
        print(f"\nFinal conversation history size: {len(agent_history)} messages")
        for i, msg in enumerate(agent_history):
            tokens = count_tokens(msg.get('content', ''))
            role = msg.get('role', 'unknown')
            content_preview = str(msg.get('content', ''))[:100] + "..." if len(str(msg.get('content', ''))) > 100 else str(msg.get('content', ''))
            print(f"  Message {i}: {role} - {tokens} tokens - {content_preview}")
            
    except Exception as e:
        print(f"Agent error: {e}")
        print(f"\nConversation history after error:")
        for i, msg in enumerate(agent_history):
            tokens = count_tokens(msg.get('content', ''))
            role = msg.get('role', 'unknown')
            content_preview = str(msg.get('content', ''))[:100] + "..." if len(str(msg.get('content', ''))) > 100 else str(msg.get('content', ''))
            print(f"  Message {i}: {role} - {tokens} tokens - {content_preview}")

if __name__ == "__main__":
    debug_agent_call()
