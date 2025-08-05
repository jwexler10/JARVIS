# memory.py
import json
import numpy as np
import openai
import os
import threading
import time
from typing import Optional, List, Tuple

# Which embedding model to use
EMBED_MODEL = "text-embedding-3-small"

# Global in-memory storage for fast operations
_memory_cache: List[str] = []  # Raw text chunks for duplicate checking
_memory_embeddings = None      # Numpy array of embeddings
_memory_chunks = None          # Numpy array of chunks (for retrieval)
_memory_lock = threading.Lock()
_last_profile_mtime = 0

def load_api_key(path: str = "config.json"):
    """Load OpenAI key from config.json into openai.api_key."""
    cfg = json.load(open(path, encoding="utf-8"))
    openai.api_key = cfg["openai_api_key"]

def split_into_chunks(text: str) -> List[str]:
    """
    Split text into paragraphs and meaningful chunks.
    Each paragraph becomes a separate chunk for memory.
    """
    # Split on double newlines (paragraphs)
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
    
    # Also split very long paragraphs
    chunks = []
    for para in paragraphs:
        if len(para) <= 800:
            chunks.append(para)
        else:
            # Split long paragraphs by sentences
            sentences = para.split('. ')
            current_chunk = ""
            for sentence in sentences:
                if len(current_chunk) + len(sentence) + 2 <= 800:
                    current_chunk += sentence + ". " if not sentence.endswith('.') else sentence + " "
                else:
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                    current_chunk = sentence + ". " if not sentence.endswith('.') else sentence + " "
            if current_chunk:
                chunks.append(current_chunk.strip())
    
    return chunks

def load_memory_cache():
    """
    Load user_profile.txt into memory cache and check if index needs rebuilding.
    Always runs on startup.
    """
    global _memory_cache, _memory_embeddings, _memory_chunks, _last_profile_mtime
    
    profile_path = "user_profile.txt"
    index_path = "profile_index.npz"
    
    # Always read the profile file
    if os.path.exists(profile_path):
        with open(profile_path, 'r', encoding='utf-8') as f:
            profile_text = f.read().strip()
        
        # Get file modification time
        current_mtime = os.path.getmtime(profile_path)
        
        # Split into chunks for cache
        chunks = split_into_chunks(profile_text) if profile_text else []
        
        with _memory_lock:
            _memory_cache = chunks
            _last_profile_mtime = current_mtime
        
        print(f"[memory] Loaded {len(chunks)} chunks into cache")
        
        # Check if index needs rebuilding
        needs_rebuild = True
        if os.path.exists(index_path):
            index_mtime = os.path.getmtime(index_path)
            if index_mtime >= current_mtime:
                # Index is newer than profile, try to load it
                try:
                    data = np.load(index_path, allow_pickle=True)
                    with _memory_lock:
                        _memory_embeddings = data["embeddings"]
                        _memory_chunks = data["chunks"]
                    print(f"[memory] Loaded existing index with {len(_memory_chunks)} chunks")
                    needs_rebuild = False
                except Exception as e:
                    print(f"[memory] Failed to load index: {e}")
        
        if needs_rebuild:
            print("[memory] Index out of date or missing, rebuilding...")
            schedule_full_rebuild()
    else:
        # No profile file exists yet
        with _memory_lock:
            _memory_cache = []
            _memory_embeddings = np.array([], dtype=np.float32).reshape(0, 1536)
            _memory_chunks = np.array([], dtype=object)
        print("[memory] No profile file found, starting with empty cache")

def is_duplicate_in_cache(new_info: str, threshold: float = 0.8) -> bool:
    """
    Fast text-based duplicate check against in-memory cache.
    Checks for semantic similarity without needing embeddings.
    """
    with _memory_lock:
        cache_copy = _memory_cache.copy()
    
    if not cache_copy:
        return False
    
    # Simple keyword overlap check for speed
    new_words = set(new_info.lower().split())
    
    for existing_chunk in cache_copy:
        existing_words = set(existing_chunk.lower().split())
        
        # Calculate Jaccard similarity (intersection / union)
        if len(existing_words) > 0:
            intersection = len(new_words & existing_words)
            union = len(new_words | existing_words)
            similarity = intersection / union if union > 0 else 0
            
            if similarity > threshold:
                return True
    
    return False

def add_to_memory_async(new_info: str):
    """
    Add new information to memory in background thread.
    Updates both cache and file, then incrementally updates embeddings.
    """
    def background_add():
        try:
            load_api_key()
            
            # 1. Add to file immediately
            with open("user_profile.txt", "a", encoding="utf-8") as f:
                f.write(f"\n\n{new_info}")
            
            # 2. Add to in-memory cache
            with _memory_lock:
                _memory_cache.append(new_info)
            
            # 3. Get embedding for new info
            resp = openai.embeddings.create(model=EMBED_MODEL, input=new_info)
            new_emb = np.array(resp.data[0].embedding, dtype=np.float32)
            
            # 4. Add to embeddings matrix incrementally
            global _memory_embeddings, _memory_chunks
            with _memory_lock:
                if _memory_embeddings is None or len(_memory_embeddings) == 0:
                    _memory_embeddings = new_emb.reshape(1, -1)
                    _memory_chunks = np.array([new_info], dtype=object)
                else:
                    _memory_embeddings = np.vstack([_memory_embeddings, new_emb])
                    _memory_chunks = np.append(_memory_chunks, new_info)
            
            print(f"[memory] Added: {new_info[:50]}{'...' if len(new_info) > 50 else ''}")
            
        except Exception as e:
            print(f"[memory] Background add failed: {e}")
    
    # Run in background thread
    thread = threading.Thread(target=background_add)
    thread.daemon = True
    thread.start()

def auto_remember_async(user_message: str, ai_response: str = "", speaker: str = "Unknown") -> Optional[str]:
    """
    Lightweight, non-blocking memory check and storage.
    Returns acknowledgment message if something was remembered, None otherwise.
    """
    # Quick check if we should remember anything
    should_save, info = should_remember_fast(user_message, ai_response)
    
    if should_save and info:
        # Add speaker information to the memory
        if speaker != "Unknown":
            info = f"[Speaker: {speaker}] {info}"
        
        # Fast duplicate check
        if is_duplicate_in_cache(info):
            return None  # Already known, no acknowledgment needed
        
        # Spawn background thread to add to memory
        add_to_memory_async(info)
        
        return None  # No verbal acknowledgment to keep conversation flowing
    
    return None

def auto_remember_sync(user_message: str, ai_response: str = "", speaker: str = "Unknown") -> Optional[str]:
    """
    Synchronous version of auto_remember for Discord bot to ensure immediate memory storage.
    """
    # Quick check if we should remember anything
    should_save, info = should_remember_fast(user_message, ai_response)
    
    if should_save and info:
        # Add speaker information to the memory
        if speaker != "Unknown":
            info = f"[Speaker: {speaker}] {info}"
        
        # Fast duplicate check
        if is_duplicate_in_cache(info):
            return None  # Already known, no acknowledgment needed
        
        # Synchronously add to memory for immediate availability
        try:
            load_api_key()
            
            # 1. Add to file immediately
            with open("user_profile.txt", "a", encoding="utf-8") as f:
                f.write(f"\n\n{info}")
            
            # 2. Add to in-memory cache
            with _memory_lock:
                _memory_cache.append(info)
            
            # 3. Get embedding for new info
            import openai
            resp = openai.embeddings.create(model=EMBED_MODEL, input=info)
            new_emb = np.array(resp.data[0].embedding, dtype=np.float32)
            
            # 4. Add to embeddings matrix incrementally
            global _memory_embeddings, _memory_chunks
            with _memory_lock:
                if _memory_embeddings is None or len(_memory_embeddings) == 0:
                    _memory_embeddings = new_emb.reshape(1, -1)
                    _memory_chunks = np.array([info], dtype=object)
                else:
                    _memory_embeddings = np.vstack([_memory_embeddings, new_emb])
                    _memory_chunks = np.append(_memory_chunks, info)
            
            print(f"[memory] Sync added: {info[:50]}{'...' if len(info) > 50 else ''}")
            
        except Exception as e:
            print(f"[memory] Sync add failed: {e}")
        
        return None  # No verbal acknowledgment to keep conversation flowing
    
    return None

def should_remember_fast(user_message: str, ai_response: str = "") -> Tuple[bool, str]:
    """
    Simplified memory classifier for speed.
    Uses keyword matching and patterns to quickly identify memorable content.
    """
    combined_text = f"{user_message} {ai_response}".lower()
    
    # Quick pattern matching for common memorable information
    memory_patterns = [
        ("birthday", "march 4", "born"),
        ("name is", "my name", "call me"),
        ("favorite", "like", "love", "prefer"),
        ("family", "mother", "father", "brother", "sister"),
        ("work", "job", "study", "school", "college"),
        ("live", "address", "from"),
        ("age", "years old", "birthday"),
        ("friend", "friends"),
    ]
    
    # Look for correction patterns
    correction_patterns = ["actually", "correction", "wrong", "not", "should be"]
    
    # Check if this contains memorable information
    for pattern_group in memory_patterns:
        if any(pattern in combined_text for pattern in pattern_group):
            # Extract the relevant sentence/phrase
            sentences = user_message.split('.')
            for sentence in sentences:
                if any(pattern in sentence.lower() for pattern in pattern_group):
                    return True, sentence.strip()
    
    # Check for corrections
    if any(pattern in combined_text for pattern in correction_patterns):
        return True, user_message.strip()
    
    return False, ""

def chunk_text(text: str, max_chars: int = 1000) -> list[str]:
    """
    Split text on blank lines, then group paragraphs so
    each chunk is <= max_chars.
    """
    paras = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks = []
    buffer = ""
    for p in paras:
        if len(buffer) + len(p) + 2 <= max_chars:
            buffer = f"{buffer}\n\n{p}".strip()
        else:
            if buffer:
                chunks.append(buffer)
            buffer = p
    if buffer:
        chunks.append(buffer)
    return chunks

def build_index(profile_path: str = "user_profile.txt",
                index_path:   str = "profile_index.npz"):
    """
    Read user_profile.txt, chunk it, embed with OpenAI (v1.x),
    and save embeddings+chunks in profile_index.npz.
    """
    load_api_key()
    text = open(profile_path, encoding="utf-8").read()
    chunks = chunk_text(text)
    embeddings = []
    for chunk in chunks:
        resp = openai.embeddings.create(
            model=EMBED_MODEL,
            input=chunk
        )
        embeddings.append(resp.data[0].embedding)
    # Save to a compressed .npz
    np.savez_compressed(
        index_path,
        embeddings=np.array(embeddings, dtype=np.float32),
        chunks=np.array(chunks, dtype=object)
    )
    print(f"[memory] Indexed {len(chunks)} profile chunks.")

def retrieve_relevant(query: str, top_k: int = 3, speaker: str = "Unknown") -> List[Tuple[str, float]]:
    """
    Fast retrieval using in-memory embeddings cache.
    Now speaker-aware: prioritizes memories from the current speaker.
    """
    global _memory_embeddings, _memory_chunks
    
    with _memory_lock:
        if _memory_embeddings is None or len(_memory_embeddings) == 0:
            print(f"[memory] No embeddings available for query: {query[:50]}")
            return []
        
        emb_matrix = _memory_embeddings.copy()
        chunks = _memory_chunks.copy()
        print(f"[memory] Searching {len(chunks)} memory chunks for: {query[:50]} (Speaker: {speaker})")
    
    try:
        load_api_key()
        # Embed the query
        qresp = openai.embeddings.create(model=EMBED_MODEL, input=query)
        q_emb = np.array(qresp.data[0].embedding, dtype=np.float32)
        
        # Compute cosine similarities
        sims = emb_matrix.dot(q_emb) / (
            np.linalg.norm(emb_matrix, axis=1) * np.linalg.norm(q_emb) + 1e-8
        )
        
        # Separate memories by speaker tags
        current_speaker_results = []
        other_speaker_results = []
        general_results = []
        
        for i, sim in enumerate(sims):
            if sim > 0.1:  # Filter low relevance
                chunk = chunks[i]
                if f"[Speaker: {speaker}]" in chunk:
                    # This is a memory from the current speaker
                    current_speaker_results.append((chunk, float(sim)))
                elif "[Speaker:" in chunk:
                    # This is a memory from a different specific speaker
                    other_speaker_results.append((chunk, float(sim)))
                else:
                    # This is a general memory (no speaker tag)
                    general_results.append((chunk, float(sim)))
        
        # Sort all lists by similarity
        current_speaker_results.sort(key=lambda x: x[1], reverse=True)
        other_speaker_results.sort(key=lambda x: x[1], reverse=True)
        general_results.sort(key=lambda x: x[1], reverse=True)
        
        # Smart prioritization based on query content
        query_lower = query.lower()
        mentions_other_person = any(name in query_lower for name in ['schmoo', 'abbey', 'mom', 'mother', 'jason', 'dad', 'father'])
        
        if mentions_other_person:
            # If query mentions another person, prioritize all memories (including other speakers)
            all_results = current_speaker_results + other_speaker_results + general_results
            all_results.sort(key=lambda x: x[1], reverse=True)
            result = all_results[:top_k]
            print(f"[memory] Query mentions other person - searching all memories")
        elif speaker != "Unknown" and current_speaker_results:
            # For personal queries, prioritize current speaker's memories
            speaker_count = min(top_k - 1, len(current_speaker_results))
            other_count = min(1, len(other_speaker_results + general_results), top_k - speaker_count)
            other_combined = other_speaker_results + general_results
            other_combined.sort(key=lambda x: x[1], reverse=True)
            result = current_speaker_results[:speaker_count] + other_combined[:other_count]
            print(f"[memory] Personal query - prioritizing current speaker memories")
        else:
            # For unknown speakers or general queries, use all memories equally
            all_results = current_speaker_results + other_speaker_results + general_results
            all_results.sort(key=lambda x: x[1], reverse=True)
            result = all_results[:top_k]
            print(f"[memory] General query - searching all memories equally")
        
        print(f"[memory] Found {len(current_speaker_results)} current speaker, {len(other_speaker_results)} other speaker, {len(general_results)} general memories")
        return result
        
    except Exception as e:
        print(f"[memory] Retrieval failed: {e}")
        return []

def has_speaker_memories(speaker: str) -> bool:
    """
    Check if JARVIS has any stored memories about a specific speaker.
    Returns True if the speaker has been encountered before.
    """
    global _memory_chunks
    
    if speaker == "Unknown":
        return False
        
    with _memory_lock:
        if _memory_chunks is None:
            return False
        
        # Check if any memory chunks contain this speaker
        speaker_tag = f"[Speaker: {speaker}]"
        for chunk in _memory_chunks:
            if speaker_tag in chunk:
                return True
    
    return False

def schedule_index_rebuild():
    """
    Schedule a full rebuild of the profile_index.npz file in background.
    Called during idle times or startup.
    """
    def rebuild():
        try:
            profile_path = "user_profile.txt"
            index_path = "profile_index.npz"
            
            if not os.path.exists(profile_path):
                return
            
            load_api_key()
            
            # Read and chunk the profile
            with open(profile_path, 'r', encoding='utf-8') as f:
                text = f.read().strip()
            
            if not text:
                return
            
            chunks = split_into_chunks(text)
            
            # Generate embeddings
            embeddings = []
            for chunk in chunks:
                resp = openai.embeddings.create(model=EMBED_MODEL, input=chunk)
                embeddings.append(resp.data[0].embedding)
            
            # Save to compressed file
            np.savez_compressed(
                index_path,
                embeddings=np.array(embeddings, dtype=np.float32),
                chunks=np.array(chunks, dtype=object)
            )
            
            # Update global cache
            global _memory_embeddings, _memory_chunks
            with _memory_lock:
                _memory_embeddings = np.array(embeddings, dtype=np.float32)
                _memory_chunks = np.array(chunks, dtype=object)
            
            print(f"[memory] Index rebuilt with {len(chunks)} chunks")
            
        except Exception as e:
            print(f"[memory] Index rebuild failed: {e}")
    
    thread = threading.Thread(target=rebuild)
    thread.daemon = True
    thread.start()

# Legacy functions for compatibility (simplified)
def chunk_text(text: str, max_chars: int = 1000) -> List[str]:
    """Legacy function - use split_into_chunks instead."""
    return split_into_chunks(text)

def build_index(profile_path: str = "user_profile.txt", index_path: str = "profile_index.npz"):
    """Legacy function - use schedule_index_rebuild instead."""
    schedule_index_rebuild()

def schedule_full_rebuild():
    """Legacy function - use schedule_index_rebuild instead."""
    schedule_index_rebuild()


