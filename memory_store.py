# memory_store.py

import os
import sqlite3
import datetime
import json
from cryptography.fernet import Fernet

# ——— Load your symmetric key ———
KEY_PATH = "memory_key.key"

def generate_key_if_needed(key_path: str = KEY_PATH):
    """Generate encryption key if it doesn't exist."""
    if not os.path.exists(key_path):
        key = Fernet.generate_key()
        with open(key_path, "wb") as f:
            f.write(key)
        print(f"🔐 Generated new encryption key: {key_path}")
        return key
    else:
        with open(key_path, "rb") as f:
            return f.read()

# Lazy loading of key and Fernet instance
_KEY = None
_FERNET = None

def get_fernet():
    """Get or create the Fernet encryption instance."""
    global _KEY, _FERNET
    if _FERNET is None:
        _KEY = generate_key_if_needed()
        _FERNET = Fernet(_KEY)
    return _FERNET

# ——— Database file ———
DB_PATH = "memories.db"

def init_db(db_path: str = DB_PATH):
    """
    Create the encrypted-memory table if it doesn't exist.
    Fields:
      id          INTEGER PRIMARY KEY
      content     BLOB   (encrypted)
      timestamp   TEXT   (ISO-8601 string)
      tags        TEXT   (JSON list of strings)
      sentiment   TEXT   (e.g. "positive")
      speaker     TEXT   (optional speaker ID)
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS memories (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        content     BLOB    NOT NULL,
        timestamp   TEXT    NOT NULL,
        tags        TEXT,
        sentiment   TEXT,
        speaker     TEXT
    );
    """)
    conn.commit()
    conn.close()
    
    # Also initialize the ratings table
    init_ratings_table(db_path)

def init_ratings_table(db_path: str = DB_PATH):
    """Create the ratings table if it doesn't exist."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ratings (
      id       INTEGER PRIMARY KEY AUTOINCREMENT,
      user     TEXT    NOT NULL,
      item     TEXT    NOT NULL,
      rating   REAL    NOT NULL,     -- e.g. 1.0 = like, 0.0 = dislike
      timestamp TEXT   NOT NULL
    );
    """)
    conn.commit()
    conn.close()

def encrypt(plaintext: str) -> bytes:
    """Encrypt a UTF-8 string to bytes."""
    fernet = get_fernet()
    return fernet.encrypt(plaintext.encode("utf-8"))

def decrypt(ciphertext: bytes) -> str:
    """Decrypt bytes to a UTF-8 string."""
    fernet = get_fernet()
    return fernet.decrypt(ciphertext).decode("utf-8")

# ——— Example write/read functions ———

def add_memory(content: str,
               tags: list[str] = None,
               sentiment: str = None,
               speaker: str = None,
               db_path: str = DB_PATH) -> int:
    """
    Insert a new memory record into the encrypted store and
    return its auto-generated ID.
    """
    enc = encrypt(content)
    ts = datetime.datetime.utcnow().isoformat()
    tags_json = json.dumps(tags or [])
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO memories (content, timestamp, tags, sentiment, speaker)
        VALUES (?, ?, ?, ?, ?);
    """, (enc, ts, tags_json, sentiment, speaker))
    mem_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return mem_id

def get_all_memories(db_path: str = DB_PATH) -> list[dict]:
    """
    Retrieve and decrypt all memories as list of dicts.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT id, content, timestamp, tags, sentiment, speaker FROM memories;")
    rows = cursor.fetchall()
    conn.close()

    results = []
    for _id, enc_content, ts, tags_json, sentiment, speaker in rows:
        content = decrypt(enc_content)
        tags = json.loads(tags_json)
        results.append({
            "id": _id,
            "content": content,
            "timestamp": ts,
            "tags": tags,
            "sentiment": sentiment,
            "speaker": speaker
        })
    return results

def delete_memory(mem_id: int, db_path: str = DB_PATH):
    """
    Remove a memory record by its ID.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM memories WHERE id = ?;", (mem_id,))
    conn.commit()
    conn.close()

# ——— Ratings functions for recommendation engine ———

def add_rating(user: str, item: str, rating: float, db_path: str = DB_PATH):
    """Log a user's like/dislike for an item."""
    ts = datetime.datetime.utcnow().isoformat()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
      INSERT INTO ratings (user, item, rating, timestamp)
      VALUES (?, ?, ?, ?);
    """, (user, item, rating, ts))
    conn.commit()
    conn.close()

def get_all_ratings(db_path: str = DB_PATH) -> list[dict]:
    """Retrieve all ratings as dicts."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT user, item, rating FROM ratings;")
    rows = cursor.fetchall()
    conn.close()
    return [{"user": u, "item": i, "rating": r} for u, i, r in rows]

def get_user_ratings(user: str, db_path: str = DB_PATH) -> list[dict]:
    """Get all ratings for a specific user."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT item, rating FROM ratings WHERE user = ?;", (user,))
    rows = cursor.fetchall()
    conn.close()
    return [{"item": i, "rating": r} for i, r in rows]
