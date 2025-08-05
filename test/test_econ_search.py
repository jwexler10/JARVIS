#!/usr/bin/env python3
"""
Quick test script to demonstrate semantic file search for "econ 306 pdf"
"""

from file_index import file_index

def main():
    print("🔍 Loading file index...")
    file_index.load()
    
    print('🔍 Search results for "econ 306 pdf":')
    hits = file_index.query("econ 306 pdf", top_k=3)
    
    if hits:
        for i, h in enumerate(hits, 1):
            print(f"{i}. {h['name']} ({h['path']}) — score {h['score']:.3f}")
    else:
        print("No results found.")

if __name__ == "__main__":
    main()
