# file_catalog.py

import os
import sqlite3
import datetime
from pathlib import Path

# New imports for snippet extraction
try:
    from PyPDF2 import PdfReader
except ImportError:
    PdfReader = None
    print("⚠️ PyPDF2 not installed - PDF extraction disabled")

try:
    import docx
except ImportError:
    docx = None
    print("⚠️ python-docx not installed - DOCX extraction disabled")

# ——— Config ———
DB_PATH = "file_catalog.db"
TARGET_FOLDERS = [
    Path.home() / "Desktop" / "jarvis",
    Path.home() / "Documents",
    Path.home() / "Downloads",
]

# Exclude these directories and file patterns to avoid system files
EXCLUDE_DIRS = {
    "__pycache__", ".git", ".vscode", "node_modules", ".pytest_cache",
    "venv", ".venv", "env", ".env", "site-packages", ".tox"
}

EXCLUDE_EXTENSIONS = {
    ".pyc", ".pyo", ".pyd", ".so", ".dll", ".exe", ".msi", ".deb", ".rpm",
    ".tmp", ".temp", ".log", ".cache", ".lock"
}

MAX_SNIPPET_CHARS = 500  # adjust as desired
MAX_FILE_SIZE_FOR_SNIPPET = 10 * 1024 * 1024  # 10MB limit for snippet extraction

def init_db(db_path: str = DB_PATH):
    """
    Create the `files` table (with a new `snippet` column) if it doesn't exist.
    Also handle migration for existing databases.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create table with new schema
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS files (
      id         INTEGER PRIMARY KEY AUTOINCREMENT,
      path       TEXT    UNIQUE NOT NULL,
      name       TEXT    NOT NULL,
      extension  TEXT,
      size       INTEGER,
      modified   TEXT,
      snippet    TEXT    -- first few hundred chars from file content
    );
    """)
    
    # Check if snippet column exists and add it if not (migration)
    cursor.execute("PRAGMA table_info(files)")
    columns = [column[1] for column in cursor.fetchall()]
    
    if 'snippet' not in columns:
        print("🔧 Migrating database: Adding snippet column...")
        cursor.execute("ALTER TABLE files ADD COLUMN snippet TEXT")
        print("✅ Database migration complete")
    
    conn.commit()
    conn.close()

def extract_snippet(path: Path, max_chars: int = MAX_SNIPPET_CHARS) -> str:
    """
    Return a small text snippet from the beginning of the file.
    Supports .pdf, .docx, and plain-text formats.
    """
    ext = path.suffix.lower()
    try:
        if ext == ".pdf" and PdfReader:
            reader = PdfReader(str(path))
            if len(reader.pages) > 0:
                text = reader.pages[0].extract_text() or ""
            else:
                text = ""
        elif ext == ".docx" and docx:
            doc = docx.Document(str(path))
            text = "\n".join(p.text for p in doc.paragraphs)
        elif ext in (".txt", ".md", ".csv", ".json", ".py", ".js", ".html", ".css", ".xml"):
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read(max_chars)
        else:
            return ""  # unsupported type
        # truncate to max_chars and clean up
        return text.strip().replace("\r\n", "\n")[:max_chars]
    except Exception:
        return ""  # any extraction error → empty

def scan_folder(folder: Path, db_path: str = DB_PATH):
    """
    Walk `folder` recursively and upsert each file’s metadata into the DB.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    file_count = 0

    for root, dirs, files in os.walk(folder):
        # Filter out excluded directories in-place to avoid walking them
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        
        for filename in files:
            full_path = Path(root) / filename
            try:
                stat = full_path.stat()
            except OSError:
                continue  # skip unreadable files

            # Skip files with excluded extensions
            ext = full_path.suffix.lower()
            if ext in EXCLUDE_EXTENSIONS:
                continue
                
            # Skip very large files for snippet extraction
            size = stat.st_size
            if size > MAX_FILE_SIZE_FOR_SNIPPET:
                continue

            # Gather metadata
            path_str  = str(full_path)
            name      = filename
            modified  = datetime.datetime.fromtimestamp(stat.st_mtime).isoformat()

            # Extract a snippet if the file type is supported
            snippet = extract_snippet(full_path)
            
            file_count += 1
            if file_count % 100 == 0:
                print(f"  Processed {file_count} files...")
            
            print(f"  📄 {name} ({len(snippet)} chars)" if snippet else f"  📄 {name}")

            # Upsert with snippet
            cursor.execute("""
            INSERT INTO files (path,name,extension,size,modified,snippet)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(path) DO UPDATE SET
              name=excluded.name,
              extension=excluded.extension,
              size=excluded.size,
              modified=excluded.modified,
              snippet=excluded.snippet;
            """, (path_str, name, ext, size, modified, snippet))

    conn.commit()
    conn.close()

def scan_all(targets: list[Path] = TARGET_FOLDERS, db_path: str = DB_PATH):
    """
    Initialize the DB and scan each folder in turn.
    """
    init_db(db_path)
    for folder in targets:
        if folder.exists() and folder.is_dir():
            print(f"📂 Scanning {folder} …")
            scan_folder(folder, db_path)
        else:
            print(f"⚠️ Skipping missing folder: {folder}")

def query_files(search_term: str = None, db_path: str = DB_PATH, limit: int = 20):
    """
    Query files from the database. If search_term is provided, search by name, path, or snippet content.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    if search_term:
        cursor.execute("""
        SELECT name, path, extension, size, modified, snippet 
        FROM files 
        WHERE name LIKE ? OR path LIKE ? OR snippet LIKE ?
        ORDER BY modified DESC
        LIMIT ?
        """, (f"%{search_term}%", f"%{search_term}%", f"%{search_term}%", limit))
    else:
        cursor.execute("""
        SELECT name, path, extension, size, modified, snippet 
        FROM files 
        ORDER BY modified DESC
        LIMIT ?
        """, (limit,))
    
    results = cursor.fetchall()
    conn.close()
    
    print(f"\n📁 Found {len(results)} files:")
    print("-" * 80)
    for name, path, ext, size, modified, snippet in results:
        size_mb = size / (1024 * 1024) if size else 0
        print(f"📄 {name:<30} | {ext:<8} | {size_mb:>6.1f}MB | {modified[:19]}")
        print(f"   📂 {path}")
        if snippet and search_term and search_term.lower() in snippet.lower():
            # Show snippet preview if search term matches content
            preview = snippet[:200] + "..." if len(snippet) > 200 else snippet
            print(f"   💬 {preview}")
        print()
    
    return results

def show_stats(db_path: str = DB_PATH):
    """
    Show database statistics.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Total files
    cursor.execute("SELECT COUNT(*) FROM files")
    total_files = cursor.fetchone()[0]
    
    # Total size
    cursor.execute("SELECT SUM(size) FROM files")
    total_size = cursor.fetchone()[0] or 0
    total_size_gb = total_size / (1024 * 1024 * 1024)
    
    # By extension
    cursor.execute("""
    SELECT extension, COUNT(*) as count, SUM(size) as total_size 
    FROM files 
    GROUP BY extension 
    ORDER BY count DESC 
    LIMIT 10
    """)
    ext_stats = cursor.fetchall()
    
    conn.close()
    
    print(f"\n📊 File Catalog Statistics:")
    print(f"   Total Files: {total_files:,}")
    print(f"   Total Size:  {total_size_gb:.2f} GB")
    print(f"\n🗂️  Top File Types:")
    for ext, count, size in ext_stats:
        size_mb = (size or 0) / (1024 * 1024)
        ext_display = ext if ext else "(no extension)"
        print(f"   {ext_display:<12} | {count:>6} files | {size_mb:>8.1f} MB")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) == 1:
        # No arguments - scan
        print("🗂️  Scanning folders for file metadata + snippets…")
        scan_all()
        print("✅ Scan complete.")
        show_stats()
    
    elif sys.argv[1] == "query":
        # Query mode
        search_term = sys.argv[2] if len(sys.argv) > 2 else None
        limit = int(sys.argv[3]) if len(sys.argv) > 3 else 20
        query_files(search_term, limit=limit)
    
    elif sys.argv[1] == "stats":
        # Show statistics
        show_stats()
    
    else:
        print("Usage:")
        print("  python file_catalog.py              # Scan all folders")
        print("  python file_catalog.py query [term] # Search files")
        print("  python file_catalog.py stats        # Show statistics")
