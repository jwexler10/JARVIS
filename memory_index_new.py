# memory_index_new.py - Fresh implementation

import os, json
import faiss
import numpy as np
from typing import List, Tuple
from memory_store import get_all_memories
from openai import OpenAI

# Path to your SQLite DB (same as memory_store)
DB_PATH = "memories.db"

# FAISS index parameters
EMBED_DIM = 1536  # e.g. OpenAI's embedding size
INDEX_PATH = "memories.index"
META_PATH  = "memories_meta.json"

class MemoryIndex:
    def __init__(self, db_path=DB_PATH, index_path=INDEX_PATH, meta_path=META_PATH):
        print("🎉 NEW FILE: MemoryIndex.__init__ called!")
        
        # Basic attributes
        self.db_path = db_path
        self.index_path = index_path
        self.meta_path = meta_path
        self.index = None
        self.meta = []
        
        # Initialize OpenAI client directly
        print("🎉 NEW FILE: Creating OpenAI client...")
        
        with open("config.json") as f:
            config = json.load(f)
        api_key = config.get("openai_api_key")
        org_id = config.get("openai_organization")
        
        if org_id:
            self.client = OpenAI(api_key=api_key, organization=org_id)
        else:
            self.client = OpenAI(api_key=api_key)
            
        print(f"🎉 NEW FILE: Client created successfully: {type(self.client)}")

    def load(self):
        # load from disk
        if not os.path.exists(self.index_path):
            # Just create empty for now
            self.index = faiss.IndexFlatIP(EMBED_DIM)
            self.meta = []
        else:
            self.index = faiss.read_index(self.index_path)
            with open(self.meta_path, "r", encoding="utf-8") as f:
                self.meta = json.load(f)

    def query(self, query_text: str, top_k: int = 5) -> List[dict]:
        # Handle empty index
        if not self.meta or self.index.ntotal == 0:
            return []
        
        # embed the query
        resp = self.client.embeddings.create(input=[query_text], model="text-embedding-ada-002")
        q_emb = np.array(resp.data[0].embedding, dtype="float32")[None, :]
        faiss.normalize_L2(q_emb)

        # search
        D, I = self.index.search(q_emb, top_k)
        results = []
        for idx, score in zip(I[0], D[0]):
            if idx >= 0 and idx < len(self.meta):  # Validate index bounds
                meta = self.meta[idx].copy()
                meta["score"] = float(score)
                results.append(meta)
        return results

# Global memory index instance
_global_memory_index = None

def get_memory_index():
    """Get or create the global memory index instance."""
    global _global_memory_index
    if _global_memory_index is None:
        _global_memory_index = MemoryIndex()
        _global_memory_index.load()
    return _global_memory_index

def retrieve_relevant(query: str, top_k: int = 5) -> List[Tuple[str, str]]:
    """
    Returns a list of (content, timestamp) for the top_k most relevant memories.
    """
    try:
        idx = get_memory_index()
        hits = idx.query(query, top_k)
        return [(h["content"], h["timestamp"]) for h in hits]
    except Exception as e:
        print(f"⚠️ Memory retrieval failed: {e}")
        return []
