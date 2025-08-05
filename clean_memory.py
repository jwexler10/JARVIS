#!/usr/bin/env python3
"""
Script to clean up corrupted memory database.
"""

import sqlite3
from datetime import datetime

def clean_memory_database():
    """Clean up the corrupted memory database."""
    
    # Connect to database
    conn = sqlite3.connect('memories.db')
    cursor = conn.cursor()
    
    print("🧹 Cleaning corrupted memory database...")
    
    # First, let's see the current schema
    cursor.execute("PRAGMA table_info(memories)")
    columns = cursor.fetchall()
    print(f"Current schema: {[col[1] for col in columns]}")
    
    # Get all memories
    cursor.execute('SELECT * FROM memories')
    all_memories = cursor.fetchall()
    
    print(f"Found {len(all_memories)} total memories")
    
    # Delete test memories and corrupted entries
    test_patterns = [
        'test memory',
        'cape may vacation',  # The fake one from AI hallucination
        'dentist for a cleaning today',  # Test data
        'whole foods',  # Test data  
        'organic vegetables',  # Test data
        'great meeting with the team'  # Test data
    ]
    
    deleted_count = 0
    kept_memories = []
    
    for memory in all_memories:
        memory_id = memory[0]
        content = memory[1]
        timestamp = memory[2]
        
        # Handle both string and bytes content
        if isinstance(content, bytes):
            content = content.decode('utf-8', errors='ignore')
        content_lower = content.lower()
        
        # Check if this is test data or corrupted
        is_test_or_corrupted = any(pattern in content_lower for pattern in test_patterns)
        
        # Also check for corrupted entries where response text is in tags field
        tags_field = memory[4] if len(memory) > 4 else ""
        if isinstance(tags_field, str) and len(tags_field) > 50:  # Tags shouldn't be this long
            is_test_or_corrupted = True
        
        # Check for None speaker (sign of corruption)
        speaker_field = memory[5] if len(memory) > 5 else ""
        if speaker_field is None or speaker_field == "None":
            is_test_or_corrupted = True
        
        if is_test_or_corrupted:
            print(f"🗑️  Deleting corrupted/test memory {memory_id}: {content_lower[:50]}...")
            cursor.execute('DELETE FROM memories WHERE id = ?', (memory_id,))
            deleted_count += 1
        else:
            kept_memories.append(memory)
    
    # For the real Cape May memory, let's fix it if it exists
    for memory in kept_memories:
        memory_id = memory[0]
        content = memory[1]
        
        # Handle both string and bytes content
        if isinstance(content, bytes):
            content = content.decode('utf-8', errors='ignore')
        
        # Look for the real Cape May entry
        if 'i actually went the weekend of august 1st' in content.lower():
            print(f"✅ Fixing Cape May memory {memory_id}")
            # Update with correct data
            cursor.execute('''
                UPDATE memories 
                SET content = ?, 
                    timestamp = ?, 
                    tags = ?, 
                    sentiment = ?, 
                    speaker = ?
                WHERE id = ?
            ''', (
                'I went to Cape May from August 1st to August 2nd, 2025. Had an amazing time at the beach!',
                '2025-08-01T12:00:00.000000',  # Set to Aug 1st when trip actually happened
                '["cape may", "beach", "vacation", "weekend", "august"]',
                'positive',
                'Jason',
                memory_id
            ))
            print(f"✅ Fixed Cape May memory with correct date")
            break
    
    conn.commit()
    conn.close()
    
    print(f"🧹 Cleanup complete! Deleted {deleted_count} corrupted/test memories")
    
    # Show what's left
    print("\n📋 Remaining memories:")
    conn = sqlite3.connect('memories.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, content, timestamp, speaker FROM memories ORDER BY timestamp')
    remaining = cursor.fetchall()
    
    for memory in remaining:
        print(f"  {memory[0]}: {memory[1][:60]}... ({memory[3]}, {memory[2][:10]})")
    
    conn.close()

def rebuild_memory_index():
    """Rebuild the FAISS index after cleaning."""
    try:
        from memory_index import get_memory_index
        print("\n🔄 Rebuilding memory index...")
        mem_idx = get_memory_index()
        mem_idx.build()
        mem_idx.save()
        print("✅ Memory index rebuilt successfully")
    except Exception as e:
        print(f"⚠️  Failed to rebuild index: {e}")

if __name__ == "__main__":
    clean_memory_database()
    rebuild_memory_index()
    print("\n🎉 Memory cleanup complete! Your Cape May memory should now be accurate.")
