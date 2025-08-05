# test_file_search.py
# Quick manual test for semantic file search

from file_index import file_index

def test_file_search():
    """Test the semantic file search functionality"""
    print("🔍 Testing Semantic File Search")
    print("=" * 40)
    
    # Load the index
    print("Loading file index...")
    file_index.load()
    print("✅ File index loaded successfully!\n")
    
    # Test queries
    test_queries = [
        "python files",
        "jarvis main file", 
        "configuration files",
        "memory database",
        "requirements dependencies",
        "google calendar",
        "file catalog"
    ]
    
    for query in test_queries:
        print(f"🔎 Query: '{query}'")
        hits = file_index.query(query, top_k=3)
        
        if hits:
            for i, hit in enumerate(hits, 1):
                print(f"  {i}. {hit['name']} (score: {hit['score']:.3f})")
                print(f"     Path: {hit['path']}")
        else:
            print("  No results found")
        print()

if __name__ == "__main__":
    test_file_search()
