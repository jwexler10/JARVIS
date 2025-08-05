#!/usr/bin/env python3
"""
Script to inspect and clean the JARVIS memory database.
"""

from memory_store import get_all_memories
import json

def inspect_memories():
    """Inspect what's currently in the memory database."""
    memories = get_all_memories()
    print(f'Found {len(memories)} memories in database:')
    
    for i, mem in enumerate(memories):
        print(f'{i+1}. Memory: {mem}')
        print(f'   Type: {type(mem)}')
        
        if isinstance(mem, dict):
            print(f'   Keys: {list(mem.keys())}')
            content = mem.get("content", "N/A")
            if isinstance(content, str) and len(content) > 100:
                content = content[:100] + "..."
            print(f'   Content: {content}')
            print(f'   Speaker: {mem.get("speaker", "N/A")}')
            print(f'   Timestamp: {mem.get("timestamp", "N/A")}')
        elif isinstance(mem, (list, tuple)) and len(mem) >= 4:
            # Old format: (id, content, timestamp, speaker, ...)
            print(f'   ID: {mem[0]}')
            content = mem[1] if len(mem[1]) <= 100 else mem[1][:100] + "..."
            print(f'   Content: {content}')
            print(f'   Timestamp: {mem[2]}')
            print(f'   Speaker: {mem[3]}')
        
        print()

def clear_test_memories():
    """Clear memories that look like test data."""
    from memory_store import init_db
    import sqlite3
    
    # Connect to database
    init_db()
    conn = sqlite3.connect('memory.db')
    cursor = conn.cursor()
    
    # Get all memories to inspect
    cursor.execute('SELECT id, content, speaker FROM memories')
    memories = cursor.fetchall()
    
    test_patterns = [
        'test',
        'cape may vacation',
        'dentist',
        'whole foods',
        'organic vegetables',
        'cleaning'
    ]
    
    deleted_count = 0
    for memory_id, content, speaker in memories:
        content_lower = content.lower()
        
        # Check if this looks like test data
        is_test = any(pattern in content_lower for pattern in test_patterns)
        
        if is_test:
            print(f"Deleting test memory {memory_id}: {content[:50]}...")
            cursor.execute('DELETE FROM memories WHERE id = ?', (memory_id,))
            deleted_count += 1
    
    conn.commit()
    conn.close()
    
    print(f"Deleted {deleted_count} test memories.")

if __name__ == "__main__":
    print("=== MEMORY DATABASE INSPECTION ===")
    inspect_memories()
    
    print("\n=== CLEANING TEST MEMORIES ===")
    response = input("Do you want to delete test memories? (y/N): ")
    if response.lower() == 'y':
        clear_test_memories()
        print("\n=== AFTER CLEANUP ===")
        inspect_memories()
    else:
        print("Skipping cleanup.")
