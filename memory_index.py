# memory_index.py

import os, json
import faiss
import numpy as np
from typing import List, Tuple
from memory_store import get_all_memories
from openai import OpenAI

# Path to your SQLite DB (same as memory_store)
DB_PATH = "memories.db"

# FAISS index parameters
EMBED_DIM = 1536  # e.g. OpenAI’s embedding size
INDEX_PATH = "memories.index"
META_PATH  = "memories_meta.json"

class MemoryIndex:
    def __init__(self, db_path=DB_PATH, index_path=INDEX_PATH, meta_path=META_PATH):
        self.db_path = db_path
        self.index_path = index_path
        self.meta_path  = meta_path
        self.index = None
        self.meta  = []  # list of dicts: {"id":..., "timestamp":..., "tags":..., "sentiment":..., "speaker":...}
        
        # Initialize OpenAI client
        with open("config.json") as f:
            config = json.load(f)
        api_key = config.get("openai_api_key")
        org_id = config.get("openai_organization")
        
        if org_id:
            self.client = OpenAI(api_key=api_key, organization=org_id)
        else:
            self.client = OpenAI(api_key=api_key)

    def build(self):
        # 1) load all memories
        records = get_all_memories(self.db_path)
        
        # Handle empty records case
        if not records:
            # Create empty index and metadata
            self.index = faiss.IndexFlatIP(EMBED_DIM)
            self.meta = []
            # Persist empty index & metadata
            faiss.write_index(self.index, self.index_path)
            with open(self.meta_path, "w", encoding="utf-8") as f:
                json.dump(self.meta, f, indent=2)
            return
        
        texts = [rec["content"] for rec in records]
        # 2) embed in batches
        embeddings = []
        for i in range(0, len(texts), 50):
            batch = texts[i:i+50]
            resp = self.client.embeddings.create(input=batch, model="text-embedding-ada-002")
            embeddings.extend([e.embedding for e in resp.data])
        embs = np.array(embeddings, dtype="float32")

        # 3) create FAISS index
        self.index = faiss.IndexFlatIP(EMBED_DIM)
        faiss.normalize_L2(embs)
        self.index.add(embs)

        # 4) store metadata in same order
        self.meta = [
            {"id":rec["id"], "timestamp":rec["timestamp"],
             "tags":rec["tags"], "sentiment":rec["sentiment"],
             "speaker":rec["speaker"], "content":rec["content"]}
            for rec in records
        ]
        # 5) persist index & metadata
        faiss.write_index(self.index, self.index_path)
        with open(self.meta_path, "w", encoding="utf-8") as f:
            json.dump(self.meta, f, indent=2)

    def load(self):
        # load from disk
        if not os.path.exists(self.index_path):
            self.build()
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

    def save(self):
        """Write current index and metadata back to disk."""
        faiss.write_index(self.index, self.index_path)
        with open(self.meta_path, "w", encoding="utf-8") as f:
            json.dump(self.meta, f, indent=2)

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
