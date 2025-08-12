#!/usr/bin/env python3
"""
Diagnostic script to inspect memory store and index for specific terms
"""

import os
import sys
import sqlite3
from datetime import datetime
from memory_store import init_db, decrypt
from memory_index import MemoryIndex, get_memory_index

def search_memory_store(term, limit=50):
    """Search the encrypted memory store for a specific term"""
    print(f"\n=== Searching Memory Store for '{term}' ===")
    
    try:
        # Initialize database
        init_db()
        
        # Connect to the database
        db_path = "memories.db"
        if not os.path.exists(db_path):
            print(f"❌ Memory database not found at {db_path}")
            return []
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all memories ordered by timestamp
        cursor.execute("""
            SELECT timestamp, content, speaker, sentiment 
            FROM memories 
            ORDER BY timestamp DESC 
            LIMIT ?
        """, (limit,))
        
        results = cursor.fetchall()
        conn.close()
        
        print(f"📊 Found {len(results)} total memories in database")
        
        matching_memories = []
        for i, (timestamp, encrypted_content, speaker_id, sentiment) in enumerate(results):
            try:
                # Decrypt the memory
                decrypted_memory = decrypt(encrypted_content)
                
                # Check if term appears in memory (case-insensitive)
                if term.lower() in decrypted_memory.lower():
                    matching_memories.append({
                        'timestamp': timestamp,
                        'memory': decrypted_memory,
                        'speaker_id': speaker_id,
                        'sentiment': sentiment
                    })
                    
                    # Print matching memory
                    dt = datetime.fromisoformat(timestamp)
                    print(f"\n🎯 Match #{len(matching_memories)} - {dt.strftime('%Y-%m-%d %H:%M:%S')}")
                    print(f"Speaker: {speaker_id}, Sentiment: {sentiment}")
                    print(f"Memory: {decrypted_memory}")
                    print("-" * 80)
            
            except Exception as e:
                print(f"⚠️ Error decrypting memory {i+1}: {e}")
        
        print(f"\n✅ Found {len(matching_memories)} memories containing '{term}'")
        return matching_memories
        
    except Exception as e:
        print(f"❌ Error searching memory store: {e}")
        return []

def search_memory_index(term, top_k=10):
    """Search the vector index for memories related to a term"""
    print(f"\n=== Searching Memory Index for '{term}' ===")
    
    try:
        # Get the memory index
        index = get_memory_index()
        
        if index is None:
            print("❌ Memory index not initialized")
            return []
        
        print(f"📊 Memory index loaded with {len(index.meta)} memories")
        
        # Instead of using embeddings (which is failing), let's search the metadata directly
        results = []
        for i, meta_entry in enumerate(index.meta):
            content = meta_entry.get("content", "").lower()
            if term.lower() in content:
                # Calculate a simple score based on term frequency
                score = content.count(term.lower()) / len(content.split())
                meta_entry["score"] = score
                results.append(meta_entry)
        
        # Sort by score (highest first)
        results.sort(key=lambda x: x.get("score", 0), reverse=True)
        results = results[:top_k]
        
        print(f"✅ Found {len(results)} relevant memories for '{term}':")
        
        for i, result_dict in enumerate(results, 1):
            score = result_dict.get("score", 0.0)
            content = result_dict.get("content", "No content")
            timestamp = result_dict.get("timestamp", "No timestamp")
            speaker = result_dict.get("speaker", "Unknown")
            
            print(f"\n🔍 Result #{i} (Score: {score:.3f})")
            print(f"Timestamp: {timestamp}")
            print(f"Speaker: {speaker}")
            print(f"Memory: {content}")
            print("-" * 80)
        
        return results
        
    except Exception as e:
        print(f"❌ Error searching memory index: {e}")
        return []

def check_memory_files():
    """Check if memory-related files exist and their sizes"""
    print("\n=== Checking Memory Files ===")
    
    files_to_check = [
        "memories.db",
        "memories.index", 
        "memories_meta.json",
        "memory_key.key",
        "file_catalog.db",
        "file_catalog.index",
        "file_catalog_meta.json"
    ]
    
    for filename in files_to_check:
        if os.path.exists(filename):
            size = os.path.getsize(filename)
            print(f"✅ {filename}: {size:,} bytes")
        else:
            print(f"❌ {filename}: Not found")

def main():
    print("🔍 Memory Diagnostic Tool")
    print("=" * 50)
    
    # Check file existence
    check_memory_files()
    
    # Search for girlfriend mentions
    search_term = "girlfriend"
    
    # Search both memory store and index
    store_results = search_memory_store(search_term)
    index_results = search_memory_index(search_term)
    
    # Summary
    print(f"\n📋 SUMMARY for '{search_term}':")
    print(f"Memory Store: {len(store_results)} matches")
    print(f"Memory Index: {len(index_results)} matches")
    
    if len(store_results) == 0 and len(index_results) == 0:
        print(f"\n🤔 No memories found for '{search_term}'")
        print("This could mean:")
        print("1. The term was never mentioned")
        print("2. Memories weren't properly saved")
        print("3. There's an issue with memory retrieval")
        
        # Let's also search for related terms
        related_terms = ["girl", "dating", "relationship", "partner", "love", "she", "her"]
        print(f"\n🔍 Checking related terms...")
        
        for term in related_terms:
            store_matches = search_memory_store(term, limit=10)
            if store_matches:
                print(f"Found {len(store_matches)} matches for '{term}'")

if __name__ == "__main__":
    main()
