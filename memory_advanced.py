# memory.py

import threading
import datetime
import json
import numpy as np
import openai
import faiss
import re
import time

from memory_store import add_memory, get_all_memories, delete_memory
from memory_index import MemoryIndex
from pattern_learning import extract_preferred_slots, save_preferred_times

# Model to use for embeddings
EMBED_MODEL = "text-embedding-ada-002"

# 1) Sentiment detection via GPT
def detect_sentiment(text: str) -> str:
    """
    Classify the user's text sentiment as 'positive', 'negative', or 'neutral'.
    """
    from openai import OpenAI
    # Load API key and create client
    with open("config.json") as f:
        config = json.load(f)
    api_key = config.get("openai_api_key")
    org_id = config.get("openai_organization")
    
    if org_id:
        client = OpenAI(api_key=api_key, organization=org_id)
    else:
        client = OpenAI(api_key=api_key)
    
    resp = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role":"system","content":"Classify the sentiment of the following text as positive, negative, or neutral."},
            {"role":"user",  "content": text}
        ],
        temperature=0
    )
    sentiment = resp.choices[0].message.content.strip().lower()
    # normalize to one of the three
    for s in ("positive","negative","neutral"):
        if s in sentiment:
            return s
    return "neutral"

# 2) Tag extraction via GPT
def extract_tags(text: str) -> list[str]:
    """
    Extract a short list of 3–6 tags or keywords describing this memory.
    """
    from openai import OpenAI
    # Load API key and create client
    with open("config.json") as f:
        config = json.load(f)
    api_key = config.get("openai_api_key")
    org_id = config.get("openai_organization")
    
    if org_id:
        client = OpenAI(api_key=api_key, organization=org_id)
    else:
        client = OpenAI(api_key=api_key)
    
    resp = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role":"system","content":"Extract 3–6 short, single-word tags best describing this text. Return them as a comma-separated list."},
            {"role":"user",  "content": text}
        ],
        temperature=0
    )
    tag_str = resp.choices[0].message.content
    # split on commas and clean up
    tags = [t.strip().lower() for t in tag_str.split(",") if t.strip()]
    # dedupe and return
    return list(dict.fromkeys(tags))[:6]

# Shared index instance
_mem_idx = MemoryIndex()
_mem_idx.load()

def load_memory_cache():
    """Reload or build the vector index at startup."""
    _mem_idx.load()

def auto_remember_async(content: str,
                        tags: list[str] = None,
                        sentiment: str = None,
                        speaker: str = None):
    """
    Spawn a background thread to persist, embed, and index a new memory.
    """
    threading.Thread(
        target=_auto_remember,
        args=(content, tags, sentiment, speaker),
        daemon=True
    ).start()

def _auto_remember(content, tags, sentiment, speaker):
    # 0) Auto-detect sentiment & tags if not provided
    if sentiment is None:
        sentiment = detect_sentiment(content)
    if tags is None:
        tags = extract_tags(content)

    # 1) Persist to the encrypted store
    mem_id = add_memory(content, tags, sentiment, speaker)

    # 2) Embed the new content
    from openai import OpenAI
    import json
    # Load API key and create client
    with open("config.json") as f:
        config = json.load(f)
    api_key = config.get("openai_api_key")
    org_id = config.get("openai_organization")
    
    if org_id:
        client = OpenAI(api_key=api_key, organization=org_id)
    else:
        client = OpenAI(api_key=api_key)
    
    resp = client.embeddings.create(input=[content], model=EMBED_MODEL)
    emb = np.array(resp.data[0].embedding, dtype="float32")[None, :]
    faiss.normalize_L2(emb)

    # 3) Add to in-memory FAISS index
    _mem_idx.index.add(emb)

    # 4) Append to metadata list
    ts = datetime.datetime.utcnow().isoformat()
    _mem_idx.meta.append({
        "id": mem_id,
        "content": content,
        "timestamp": ts,
        "tags": tags or [],
        "sentiment": sentiment,
        "speaker": speaker
    })

    # 5) Persist the updated index & metadata
    _mem_idx.save()

    # 6) Pattern learning: if this memory contains "meeting" tag, update preferred meeting times
    if tags and "meeting" in tags:
        try:
            slots = extract_preferred_slots("meeting", top_n=3)
            if slots:  # Only save if we found patterns
                save_preferred_times("meeting", slots)
        except Exception as e:
            # Silent fail to not interrupt memory storage
            pass

def retrieve_relevant(query: str,
                      top_k: int = 5,
                      speaker: str = None,
                      since: datetime.datetime = None,
                      tags: list[str] = None,
                      sentiment: str = None) -> list[dict]:
    """
    Returns the top_k most relevant memories to `query`, each as a dict:
      {
        "content": str,
        "timestamp": "2025-08-15T14:23:00",
        "tags": [...],
        "sentiment": "...",
        "speaker": "...",
        "score": 0.95
      }
    Optionally filters by:
      - speaker: only memories from this speaker
      - since: only memories with timestamp >= since
      - tags: only memories containing ANY of these tags
      - sentiment: only memories matching this sentiment
    
    PRIORITIZES RECENT MEMORIES: More recent memories get score boosts to handle corrections.
    """
    try:
        # 1) semantic search
        hits = _mem_idx.query(query, top_k=top_k * 3)  # Get more to allow for filtering and recency boost
        results = []
        
        # 2) Calculate recency boost - more recent memories get higher scores
        if hits:
            # Get the timestamp range
            timestamps = []
            for h in hits:
                try:
                    ts = datetime.datetime.fromisoformat(h["timestamp"])
                    timestamps.append(ts)
                except:
                    timestamps.append(datetime.datetime.min)
            
            if timestamps:
                max_time = max(timestamps)
                min_time = min(timestamps)
                time_range = (max_time - min_time).total_seconds()
                
                # Apply recency boost to each hit
                for i, h in enumerate(hits):
                    try:
                        ts = datetime.datetime.fromisoformat(h["timestamp"])
                        # More recent = higher boost (0.0 to 0.2 boost)
                        if time_range > 0:
                            recency_factor = (ts - min_time).total_seconds() / time_range
                            recency_boost = recency_factor * 0.2  # Up to 20% boost for newest
                        else:
                            recency_boost = 0.1  # Small boost if all same time
                        
                        # Apply boost to score
                        original_score = h.get("score", 0.0)
                        h["score"] = min(1.0, original_score + recency_boost)
                    except:
                        pass  # Keep original score if timestamp parsing fails
                
                # Re-sort by boosted scores
                hits = sorted(hits, key=lambda x: x.get("score", 0.0), reverse=True)
        
        # 3) Apply filters and collect results
        for h in hits:
            # Optional filters
            if speaker and speaker != "Unknown" and h.get("speaker") != speaker:
                continue
            
            if since:
                try:
                    ts = datetime.datetime.fromisoformat(h["timestamp"])
                    if ts < since:
                        continue
                except:
                    continue
            
            if tags and not any(t in h.get("tags", []) for t in tags):
                continue
            
            if sentiment and h.get("sentiment") != sentiment:
                continue
            
            results.append(h)
            
            # Stop when we have enough results
            if len(results) >= top_k:
                break
        
        return results
    except Exception as e:
        print(f"⚠️ Memory retrieval failed: {e}")
        return []

def retrieve_relevant_simple(query: str, top_k: int = 5, speaker: str = None):
    """
    Compatibility function that returns (content, timestamp) tuples.
    Used by quiet_retrieve_relevant in jarvis.py.
    """
    results = retrieve_relevant(query, top_k=top_k, speaker=speaker)
    return [(r["content"], r["timestamp"]) for r in results]

def has_speaker_memories(speaker: str) -> bool:
    """Check if we have any memories for a specific speaker."""
    return any(meta.get("speaker") == speaker for meta in _mem_idx.meta)

def schedule_index_rebuild(interval_hours: int = 24):
    """
    Optional: rebuild the entire index periodically (e.g. at shutdown or daily).
    """
    # Could use threading.Timer to call _mem_idx.build() on a schedule.
    pass

def summarize_old_memories(cutoff_days: int = 180):
    """
    1) Find all memories older than cutoff_days,
    2) Summarize them into bullets with GPT,
    3) Store the summary as a new memory (tagged 'summary'),
    4) Delete the raw old memories,
    5) Rebuild the FAISS index.
    """
    cutoff = datetime.datetime.utcnow() - datetime.timedelta(days=cutoff_days)
    
    # 1) Gather old records
    all_mems = get_all_memories()
    old = [m for m in all_mems
           if datetime.datetime.fromisoformat(m["timestamp"]) < cutoff]
    
    if not old:
        print(f"📦 No memories older than {cutoff_days} days found to summarize")
        return  # nothing to do

    print(f"📦 Found {len(old)} memories older than {cutoff_days} days to summarize")
    
    # 2) Build the summarization prompt
    contents = [f"- {m['content']}" for m in old]
    prompt = (
        "You are a personal AI that condenses long lists of life memories into "
        "a concise set of bullet points capturing the key events and insights. "
        "Here are older memories:\n\n" +
        "\n".join(contents) +
        "\n\nPlease provide a summary in 5–10 bullet points."
    )

    # 3) Call GPT to summarize
    try:
        from openai import OpenAI
        # Load API key and create client
        with open("config.json") as f:
            config = json.load(f)
        api_key = config.get("openai_api_key")
        org_id = config.get("openai_organization")
        
        if org_id:
            client = OpenAI(api_key=api_key, organization=org_id)
        else:
            client = OpenAI(api_key=api_key)
        
        resp = client.chat.completions.create(
            model="gpt-4-0613",
            messages=[
                {"role":"system","content":"Condense these memories into bullets."},
                {"role":"user","content": prompt}
            ],
            temperature=0.5,
            max_tokens=500
        )
        summary = resp.choices[0].message.content.strip()
        
        # 4) Store the summary as a new memory
        print(f"📦 Creating summary memory from {len(old)} old memories")
        auto_remember_async(
            content=f"Memory Summary ({cutoff_days}+ days ago): {summary}",
            tags=["summary", "archived"],
            sentiment="neutral",
            speaker="system"
        )

        # 5) Delete the raw old memories
        for m in old:
            delete_memory(m["id"])
        
        print(f"📦 Deleted {len(old)} old memories and created summary")

        # 6) Rebuild the entire index to remove deleted vectors & add summary
        print("📦 Rebuilding memory index...")
        _mem_idx.build()
        print("📦 Memory compression complete!")
        
    except Exception as e:
        print(f"❌ Error during memory summarization: {e}")

def schedule_summarization(interval_hours: int = 24):
    """
    Kick off a background thread that runs summarize_old_memories()
    every interval_hours.
    """
    def loop():
        while True:
            try:
                summarize_old_memories()
            except Exception as e:
                print(f"❌ Error in memory summarization loop: {e}")
            time.sleep(interval_hours * 3600)
    
    print(f"📦 Starting memory compression scheduler (every {interval_hours} hours)")
    threading.Thread(target=loop, daemon=True).start()
