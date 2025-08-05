# recommender.py

import json
import pickle
import numpy as np
from collections import defaultdict
from sklearn.neighbors import NearestNeighbors
from memory_store import get_all_ratings

# Paths
MODEL_PATH = "knn_model.pkl"
ITEMS_PATH = "knn_items.json"

class Recommender:
    def __init__(self):
        # items_list: index → item name
        # matrix: len(items)×len(users)
        self.items_list = []
        self.user_index = {}
        self.matrix = None
        self.model = None

    def build_model(self):
        # 1) Load ratings
        data = get_all_ratings()
        
        # Check if we have any data to train on
        if not data:
            print("No ratings data available. Recommender will be initialized but not trained.")
            # Create empty model state for future use
            self.user_index = {}
            self.items_list = []
            self.matrix = np.array([])
            self.model = None
            return
        
        # 2) Map users & items to indices
        users = sorted({d["user"] for d in data})
        items = sorted({d["item"] for d in data})
        self.user_index = {u:i for i,u in enumerate(users)}
        self.items_list = items
        # 3) Build matrix
        mat = np.zeros((len(items), len(users)), dtype=float)
        for d in data:
            u = self.user_index[d["user"]]
            idx = items.index(d["item"])
            mat[idx, u] = d["rating"]
        self.matrix = mat
        # 4) Train kNN on item vectors
        self.model = NearestNeighbors(metric="cosine", algorithm="brute")
        self.model.fit(mat)
        # 5) Persist
        with open(MODEL_PATH, "wb") as f:
            pickle.dump(self.model, f)
        with open(ITEMS_PATH, "w", encoding="utf-8") as f:
            json.dump(self.items_list, f)

    def load_model(self):
        with open(MODEL_PATH, "rb") as f:
            self.model = pickle.load(f)
        with open(ITEMS_PATH, "r", encoding="utf-8") as f:
            self.items_list = json.load(f)

    def recommend(self, user_id: str = None, item: str = None, num_recommendations: int = 5) -> list:
        """
        Get recommendations for a user or based on an item.
        Returns list of (item_id, score) tuples.
        """
        # Check if model is trained
        if not self.model or not self.items_list:
            return []
        
        if item is not None:
            # Item-based recommendation (original behavior)
            if item not in self.items_list:
                return []
            idx = self.items_list.index(item)
            vec = self.matrix[idx].reshape(1, -1)
            dists, nbrs = self.model.kneighbors(vec, n_neighbors=num_recommendations+1)
            recs = []
            for dist, nbr in zip(dists[0], nbrs[0]):
                if nbr == idx:
                    continue  # skip the item itself
                score = 1.0 - dist  # Convert distance to similarity score
                recs.append((self.items_list[nbr], score))
                if len(recs) >= num_recommendations:
                    break
            return recs
        
        elif user_id is not None:
            # User-based recommendation - recommend items similar to ones they've rated highly
            from memory_store import get_user_ratings
            user_ratings = get_user_ratings(user_id)
            
            if not user_ratings:
                return []
            
            # Find items the user liked (rating >= 4)
            liked_items = [r["item"] for r in user_ratings if r["rating"] >= 4]
            
            if not liked_items:
                return []
            
            # Get recommendations based on liked items
            all_recs = {}
            for liked_item in liked_items:
                item_recs = self.recommend(item=liked_item, num_recommendations=num_recommendations*2)
                for rec_item, score in item_recs:
                    # Skip items the user has already rated
                    if rec_item not in [r["item"] for r in user_ratings]:
                        if rec_item in all_recs:
                            all_recs[rec_item] = max(all_recs[rec_item], score)
                        else:
                            all_recs[rec_item] = score
            
            # Sort by score and return top recommendations
            sorted_recs = sorted(all_recs.items(), key=lambda x: x[1], reverse=True)
            return sorted_recs[:num_recommendations]
        
        else:
            return []

# Singleton instance
_recommender = Recommender()
