# pattern_learning.py

import datetime
import json
import os
from collections import Counter
from sklearn.mixture import GaussianMixture
import numpy as np

from memory_store import get_all_memories

# Where to persist your learned patterns
PATTERN_PATH = "preferred_times.json"

def compute_hour_counts(tag: str) -> Counter:
    """
    Count the distribution of event-hours for memories tagged with `tag`.
    """
    records = get_all_memories()
    hours = []
    for r in records:
        # Handle both string and list tags
        tags = r.get("tags", [])
        if isinstance(tags, str):
            tags = [tags]
        elif not isinstance(tags, list):
            tags = []
            
        if tag in tags:
            # parse ISO timestamp
            ts = datetime.datetime.fromisoformat(r["timestamp"])
            hours.append(ts.hour)
    return Counter(hours)

def fit_gmm(hours: list[int], n_components: int = 2) -> GaussianMixture:
    """
    Fit a simple Gaussian Mixture over the hours (treated as 0–23).
    Returns the trained model.
    """
    if len(hours) < 2:
        # Not enough data for GMM, return None
        return None
    
    X = np.array(hours).reshape(-1,1)
    # Ensure we don't use more components than we have unique values
    unique_hours = len(set(hours))
    actual_components = min(n_components, unique_hours, len(hours))
    
    if actual_components < 1:
        return None
        
    gmm = GaussianMixture(n_components=actual_components, random_state=0)
    gmm.fit(X)
    return gmm

def extract_preferred_slots(tag: str, top_n: int = 3) -> list[int]:
    """
    Return your top_n preferred hours for the given tag,
    by mixing frequency counts with a GMM peak.
    """
    counts = compute_hour_counts(tag)
    if not counts:
        return []
    
    # If we have very few data points, just return the most common hours
    if len(counts) < 2:
        return [h for h, _ in counts.most_common(top_n)]
    
    # Most common raw hours
    common = [h for h,_ in counts.most_common(top_n*2)]
    
    # Try to fit GMM on all hours
    all_hours = list(counts.elements())
    gmm = fit_gmm(all_hours, n_components=min(3, len(set(all_hours))))
    
    if gmm is None:
        # Fallback to simple frequency-based ranking
        return [h for h, _ in counts.most_common(top_n)]
    
    # Score each candidate by its GMM density
    scores = {}
    for h in set(common):
        try:
            scores[h] = np.exp(gmm.score([[h]]))  # density proxy
        except:
            scores[h] = counts[h]  # fallback to frequency
    
    # Sort by density * frequency
    ranked = sorted(common, key=lambda h: scores[h]*counts[h], reverse=True)
    return ranked[:top_n]

def save_preferred_times(tag: str, slots: list[int], path: str = PATTERN_PATH):
    """
    Persist your preferred slots mapping as JSON.
    """
    data = {}
    if os.path.exists(path):
        with open(path,"r",encoding="utf-8") as f:
            data = json.load(f)
    data[tag] = slots
    with open(path,"w",encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def load_preferred_times(tag: str, path: str = PATTERN_PATH) -> list[int]:
    """Load persisted slots for a tag, or empty list."""
    if not os.path.exists(path):
        return []
    data = json.load(open(path,"r",encoding="utf-8"))
    return data.get(tag, [])

def get_preferred_times(tag: str, top_n: int = 3) -> list[int]:
    """
    Returns the persisted preferred hours for `tag`,
    falling back to a fresh compute if none saved.
    """
    slots = load_preferred_times(tag)
    if not slots:
        slots = extract_preferred_slots(tag, top_n)
        if slots:  # Only save if we found patterns
            save_preferred_times(tag, slots)
    return slots
