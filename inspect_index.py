import numpy as np

data = np.load("profile_index.npz", allow_pickle=True)
chunks = data["chunks"]
for i, c in enumerate(chunks, 1):
    print(f"Chunk {i}:\n{c}\n{'-'*40}")
