#!/usr/bin/env python3
"""
Test script to demonstrate speaker-aware memory functionality.
Simulates the exact scenario Jason described.
"""

import time
from memory import load_memory_cache, has_speaker_memories, schedule_index_rebuild
from jarvis import ask_jarvis

def test_speaker_memory():
    """Test the speaker-aware memory system"""
    
    print("=== Testing Speaker-Aware Memory ===")
    print("Simulating Jason's scenario...")
    print()
    
    # Load memory system
    print("🔧 Loading memory system...")
    load_memory_cache()
    print()
    
    # Step 1: Jason tells JARVIS his favorite fruit
    print("1️⃣ Jason tells JARVIS his favorite fruit is mangoes:")
    jason_response = ask_jarvis("My favorite fruit is mangoes", speaker="Jason")
    print(f"   Jason: My favorite fruit is mangoes")
    print(f"   JARVIS: {jason_response}")
    print()
    
    # Brief pause to let async memory save
    print("⏳ Waiting for memory to save...")
    time.sleep(2)
    print()
    
    # Step 2: Schmoo tells JARVIS her favorite fruit
    print("2️⃣ Schmoo tells JARVIS her favorite fruit:")
    schmoo_response = ask_jarvis("Hi JARVIS, my favorite fruit is strawberries", speaker="Schmoo")
    print(f"   Schmoo: Hi JARVIS, my favorite fruit is strawberries")
    print(f"   JARVIS: {schmoo_response}")
    print()
    
    # Brief pause to let async memory save
    print("⏳ Waiting for memory to save...")
    time.sleep(2)
    print()
    
    # Step 3: Check if JARVIS has memories of both speakers
    print("3️⃣ Checking JARVIS's memory banks:")
    has_jason_memories = has_speaker_memories("Jason")
    has_schmoo_memories = has_speaker_memories("Schmoo")
    print(f"   Has memories of Jason: {has_jason_memories}")
    print(f"   Has memories of Schmoo: {has_schmoo_memories}")
    print()
    
    # Step 4: NEW SESSION - Schmoo asks about her favorite fruit
    print("4️⃣ NEW SESSION - Schmoo asks about her favorite fruit:")
    schmoo_question = ask_jarvis("What's my favorite fruit?", speaker="Schmoo")
    print(f"   Schmoo: What's my favorite fruit?")
    print(f"   JARVIS: {schmoo_question}")
    print()
    
    # Step 5: NEW SESSION - Jason asks about his favorite fruit
    print("5️⃣ NEW SESSION - Jason asks about his favorite fruit:")
    jason_question = ask_jarvis("What's my favorite fruit?", speaker="Jason")
    print(f"   Jason: What's my favorite fruit?")
    print(f"   JARVIS: {jason_question}")
    print()
    
    # Step 6: Cross-check - Schmoo asks about Jason's favorite fruit
    print("6️⃣ Cross-check - Schmoo asks about Jason's favorite fruit:")
    cross_check = ask_jarvis("What's Jason's favorite fruit?", speaker="Schmoo")
    print(f"   Schmoo: What's Jason's favorite fruit?")
    print(f"   JARVIS: {cross_check}")
    print()
    
    print("=== Test Complete ===")
    print()
    print("Expected behavior:")
    print("- Step 4: JARVIS should remember Schmoo's favorite fruit is strawberries")
    print("- Step 5: JARVIS should remember Jason's favorite fruit is mangoes")
    print("- Step 6: JARVIS should know Jason's fruit even when Schmoo asks")
    
    # Schedule memory rebuild for next run
    schedule_index_rebuild()

if __name__ == "__main__":
    test_speaker_memory()
