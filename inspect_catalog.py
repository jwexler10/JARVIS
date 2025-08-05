#!/usr/bin/env python3
"""
Quick script to inspect file catalog database entries and their snippets.
"""

import sqlite3
from pathlib import Path

DB_PATH = "file_catalog.db"

def inspect_by_extension(ext: str, limit: int = 5):
    """Inspect files by extension and show their snippets."""
    print(f"\n🔍 Inspecting {ext} files:")
    print("=" * 60)
    
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    cur.execute("""
        SELECT name, path, snippet, size 
        FROM files 
        WHERE extension = ? AND snippet IS NOT NULL AND snippet != ''
        LIMIT ?
    """, (ext, limit))
    
    results = cur.fetchall()
    
    if not results:
        print(f"❌ No {ext} files found with snippets")
    else:
        for name, path, snippet, size in results:
            print(f"📄 {name} ({size} bytes)")
            print(f"📂 {path}")
            preview = snippet[:200] + "..." if len(snippet) > 200 else snippet
            print(f"💬 Snippet ({len(snippet)} chars):")
            print(f"   {preview}")
            print("-" * 40)
    
    conn.close()

def inspect_recent_files(limit: int = 10):
    """Show recent files with snippets."""
    print(f"\n📅 Recent files with content:")
    print("=" * 60)
    
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    cur.execute("""
        SELECT name, extension, snippet, modified 
        FROM files 
        WHERE snippet IS NOT NULL AND snippet != ''
        ORDER BY modified DESC
        LIMIT ?
    """, (limit,))
    
    results = cur.fetchall()
    
    for name, ext, snippet, modified in results:
        print(f"📄 {name} ({ext}) - {modified[:19]}")
        preview = snippet[:150] + "..." if len(snippet) > 150 else snippet
        print(f"   💬 {preview}")
        print()
    
    conn.close()

def show_snippet_stats():
    """Show statistics about snippets."""
    print(f"\n📊 Snippet Statistics:")
    print("=" * 40)
    
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # Total files vs files with snippets
    cur.execute("SELECT COUNT(*) FROM files")
    total_files = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM files WHERE snippet IS NOT NULL AND snippet != ''")
    files_with_snippets = cur.fetchone()[0]
    
    # Average snippet length
    cur.execute("SELECT AVG(LENGTH(snippet)) FROM files WHERE snippet IS NOT NULL AND snippet != ''")
    avg_length = cur.fetchone()[0] or 0
    
    # By extension
    cur.execute("""
        SELECT extension, COUNT(*) as count, AVG(LENGTH(snippet)) as avg_len
        FROM files 
        WHERE snippet IS NOT NULL AND snippet != ''
        GROUP BY extension 
        ORDER BY count DESC
        LIMIT 10
    """)
    ext_stats = cur.fetchall()
    
    print(f"Total Files: {total_files:,}")
    print(f"Files with Snippets: {files_with_snippets:,} ({files_with_snippets/total_files*100:.1f}%)")
    print(f"Average Snippet Length: {avg_length:.0f} characters")
    
    print(f"\n📋 Snippets by File Type:")
    for ext, count, avg_len in ext_stats:
        ext_display = ext if ext else "(no extension)"
        print(f"   {ext_display:<12} | {count:>4} files | {avg_len:>6.0f} avg chars")
    
    conn.close()

if __name__ == "__main__":
    if not Path(DB_PATH).exists():
        print(f"❌ Database file '{DB_PATH}' not found. Run file_catalog.py first.")
        exit(1)
    
    print("🗂️ File Catalog Inspector")
    
    # Show statistics first
    show_snippet_stats()
    
    # Inspect different file types
    inspect_by_extension(".txt", 3)
    inspect_by_extension(".py", 3)
    inspect_by_extension(".json", 3)
    inspect_by_extension(".pdf", 3)
    inspect_by_extension(".md", 3)
    
    # Show recent files
    inspect_recent_files(5)
    
    print("\n✅ Inspection complete!")
