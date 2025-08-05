#!/usr/bin/env python3
"""
Fix memory retrieval to prioritize recent corrections over old memories.
This script will:
1. Rebuild the memory index from the database
2. Update speaker info for recent memories 
3. Test retrieval to ensure corrections are prioritized
"""

import sqlite3
from memory_store import decrypt, get_all_memories
from memory_advanced import _mem_idx, retrieve_relevant
import datetime

def fix_memory_retrieval():
    print("🔧 Fixing memory retrieval...")
    
    # 1. Get all memories from database
    memories = get_all_memories()
    print(f"Found {len(memories)} memories in database")
    
    # 2. Update speaker for recent memories that are missing it
    conn = sqlite3.connect('memories.db')
    cursor = conn.cursor()
    
    updated_count = 0
    for memory in memories:
        if memory.get('speaker') is None or memory.get('speaker') == 'None':
            # Update speaker to Jason for memories from recent sessions
            cursor.execute(
                "UPDATE memories SET speaker = ? WHERE id = ?",
                ('Jason', memory['id'])
            )
            updated_count += 1
    
    conn.commit()
    conn.close()
    print(f"✅ Updated speaker info for {updated_count} memories")
    
    # 3. Rebuild the memory index from scratch
    print("🔄 Rebuilding memory index from database...")
    _mem_idx.build()
    print("✅ Memory index rebuilt successfully")
    
    # 4. Test retrieval for Cape May
    print("\n🧪 Testing Cape May retrieval after fix:")
    hits = retrieve_relevant('Cape May', top_k=5, speaker='Jason')
    
    for i, hit in enumerate(hits, 1):
        dt = datetime.datetime.fromisoformat(hit["timestamp"]).strftime("%b %d, %Y %H:%M")
        print(f'{i}. Score: {hit["score"]:.3f} | {dt} | {hit["content"][:80]}...')
    
    # Check if the correction is now prioritized
    if hits and ('august 1st' in hits[0]['content'].lower() or 'august 2nd' in hits[0]['content'].lower()):
        print("\n✅ SUCCESS: Recent correction is now prioritized!")
    else:
        print("\n⚠️  Still showing old memory first. May need additional fixes.")
    
    return hits

if __name__ == "__main__":
    fix_memory_retrieval()
