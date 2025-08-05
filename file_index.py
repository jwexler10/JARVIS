# file_index.py

import os
import json
import sqlite3
import numpy as np
import faiss
from openai import OpenAI
from typing import List, Dict

# Paths & params
DB_PATH    = "file_catalog.db"
INDEX_PATH = "file_catalog.index"
META_PATH  = "file_catalog_meta.json"
EMBED_MODEL = "text-embedding-ada-002"
EMBED_DIM   = 1536  # dimension for ada-002

class FileIndex:
    def __init__(self,
                 db_path: str = DB_PATH,
                 index_path: str = INDEX_PATH,
                 meta_path: str = META_PATH):
        self.db_path    = db_path
        self.index_path = index_path
        self.meta_path  = meta_path
        self.index      = None
        self.meta       = []  # list of dicts with file metadata
        
        # Initialize OpenAI client with error handling
        try:
            with open("config.json") as f:
                content = f.read().strip()
                if not content:
                    raise ValueError("Config file is empty")
                config = json.loads(content)
        except (FileNotFoundError, json.JSONDecodeError, ValueError) as e:
            print(f"⚠️ Warning: Could not load config.json ({e}). File index will be disabled.")
            self.client = None
            return
            
        api_key = config.get("openai_api_key")
        org_id = config.get("openai_organization")
        
        if not api_key:
            print("⚠️ Warning: No OpenAI API key found in config. File index will be disabled.")
            self.client = None
            return
        
        if org_id:
            self.client = OpenAI(api_key=api_key, organization=org_id)
        else:
            self.client = OpenAI(api_key=api_key)

    def build(self):
        # Check if client is available
        if not self.client:
            print("⚠️ File index build skipped: OpenAI client not available")
            return
            
        # 1) Load all file records from SQLite
        conn = sqlite3.connect(self.db_path)
        cur  = conn.cursor()
        cur.execute("SELECT id, path, name, extension, modified, snippet FROM files;")
        rows = cur.fetchall()
        conn.close()

        texts = []
        self.meta = []
        for fid, path, name, ext, modified, snippet in rows:
            # Combine filename + snippet for embedding
            text = f"{name} {snippet or ''}"
            texts.append(text)
            self.meta.append({
                "id": fid,
                "path": path,
                "name": name,
                "extension": ext,
                "modified": modified
            })

        if not texts:
            print("⚠️ No files found to index")
            return

        # 2) Batch-embed all texts
        try:
            embeddings = []
            BATCH = 50
            for i in range(0, len(texts), BATCH):
                batch = texts[i : i + BATCH]
                resp = self.client.embeddings.create(input=batch, model=EMBED_MODEL)
                embeddings.extend([e.embedding for e in resp.data])
        except Exception as e:
            print(f"⚠️ Error creating embeddings: {e}")
            return

        embs = np.array(embeddings, dtype="float32")
        faiss.normalize_L2(embs)

        # 3) Build flat (inner-product) index
        self.index = faiss.IndexFlatIP(EMBED_DIM)
        self.index.add(embs)

        # 4) Persist index + meta
        faiss.write_index(self.index, self.index_path)
        with open(self.meta_path, "w", encoding="utf-8") as f:
            json.dump(self.meta, f, indent=2)

    def load(self):
        # Check if client is available
        if not self.client:
            print("⚠️ File index load skipped: OpenAI client not available")
            return
            
        # load from disk (build if missing)
        if not os.path.exists(self.index_path) or not os.path.exists(self.meta_path):
            self.build()
        else:
            try:
                self.index = faiss.read_index(self.index_path)
                with open(self.meta_path, "r", encoding="utf-8") as f:
                    self.meta = json.load(f)
            except Exception as e:
                print(f"⚠️ Error loading file index: {e}")
                self.build()  # Try to rebuild if loading fails

    def query(self, query_text: str, top_k: int = 5) -> List[Dict]:
        """
        Returns up to top_k file records with highest semantic similarity.
        Each record includes: path, name, extension, modified, score.
        """
        # Check if client and index are available
        if not self.client:
            print("⚠️ File index query skipped: OpenAI client not available")
            return []
            
        if not self.index or not self.meta:
            print("⚠️ File index not loaded")
            return []
            
        try:
            # 1) Embed the query
            resp = self.client.embeddings.create(input=[query_text], model=EMBED_MODEL)
            q_emb = np.array(resp.data[0].embedding, dtype="float32")[None, :]
            faiss.normalize_L2(q_emb)

            # 2) Search
            D, I = self.index.search(q_emb, top_k)
            results = []
            for idx, score in zip(I[0], D[0]):
                if idx < 0 or idx >= len(self.meta): 
                    continue
                m = self.meta[idx].copy()
                m["score"] = float(score)
                results.append(m)
            return results
        except Exception as e:
            print(f"⚠️ Error querying file index: {e}")
            return []

# Singleton for your app
file_index = FileIndex()
