import re
def extract_urls_from_search_results(results_str):
    """
    Extract URLs from formatted search results string.
    Returns a list of URLs in order of appearance.
    """
    urls = []
    for line in results_str.splitlines():
        match = re.search(r'https?://[^\s)]+', line)
        if match:
            url = match.group().rstrip('.,;)')
            if url not in urls:
                urls.append(url)
    return urls

def get_search_result_urls(query, primary_site=None, max_results=5):
    """
    Returns a list of URLs from a site-specific search (if primary_site),
    otherwise from a general search. Used for disambiguation.
    """
    if primary_site:
        results = search_web(query, max_results=max_results, site=primary_site)
    else:
        results = search_web(query, max_results=max_results)
    return extract_urls_from_search_results(results)
"""
Enhanced search functionality using ddgs (DuckDuckGo Search)
Supports general web search and fandom-specific search with site restrictions.
"""

import json
from ddgs import DDGS

def search_web(query, max_results=5, site=None, time_period=None):
    """
    Perform a web search using DuckDuckGo.
    
    Args:
        query (str): Search query
        max_results (int): Maximum number of results to return
        site (str): Restrict search to specific site (e.g., "fandom.com")
        time_period (str): Time period filter ("d", "w", "m", "y")
    
    Returns:
        str: Formatted search results
    """
    try:
        # Build the search query with site restriction if provided
        search_query = query
        if site:
            search_query = f"site:{site} {query}"
        
        print(f"🔍 Searching: {search_query}")
        
        with DDGS() as ddgs:
            # Perform text search
            results = list(ddgs.text(
                query=search_query,
                max_results=max_results,
                timelimit=time_period
            ))
        
        if not results:
            return f"No results found for '{query}'"
        
        # Format results
        formatted_results = []
        for i, result in enumerate(results, 1):
            title = result.get('title', 'No title')
            url = result.get('href', 'No URL')
            snippet = result.get('body', 'No description')
            
            formatted_results.append(f"{i}. **{title}**\n   {url}\n   {snippet}\n")
        
        return "\n".join(formatted_results)
        
    except Exception as e:
        print(f"❌ Search error: {e}")
        return f"Search failed: {e}"


def search_fandom_specific(query, max_results=5):
    """
    Search specifically on VGHW Fandom wiki.
    
    Args:
        query (str): Search query
        max_results (int): Maximum number of results to return
    
    Returns:
        str: Formatted search results from VGHW Fandom
    """
    return search_web(query, max_results=max_results, site="vghw.fandom.com")


def search_with_fallback(query, primary_site=None, max_results=5):
    """
    Search with fallback strategy - try site-specific first, then general search.
    
    Args:
        query (str): Search query
        primary_site (str): Primary site to search first
        max_results (int): Maximum number of results to return
    
    Returns:
        str: Formatted search results with fallback info
    """
    try:
        # Try site-specific search first
        if primary_site:
            print(f"🔍 Trying site-specific search on {primary_site}")
            site_results = search_web(query, max_results=max_results, site=primary_site)
            
            # Check if we got meaningful results
            if "No results found" not in site_results:
                return f"**Results from {primary_site}:**\n\n{site_results}"
        
        # Fall back to general search
        print(f"🔍 Falling back to general web search")
        general_results = search_web(query, max_results=max_results)
        
        fallback_msg = ""
        if primary_site:
            fallback_msg = f"**No specific results found on {primary_site}. General search results:**\n\n"
        
        return f"{fallback_msg}{general_results}"
        
    except Exception as e:
        return f"Search failed: {e}"


def search_news(query, max_results=5, time_period="w"):
    """
    Search for news articles using DuckDuckGo news search.
    
    Args:
        query (str): Search query
        max_results (int): Maximum number of results to return
        time_period (str): Time period ("d", "w", "m", "y")
    
    Returns:
        str: Formatted news search results
    """
    try:
        print(f"📰 Searching news: {query}")
        
        with DDGS() as ddgs:
            # Perform news search
            results = list(ddgs.news(
                query=query,
                max_results=max_results,
                timelimit=time_period
            ))
        
        if not results:
            return f"No news results found for '{query}'"
        
        # Format results
        formatted_results = []
        for i, result in enumerate(results, 1):
            title = result.get('title', 'No title')
            url = result.get('url', 'No URL')
            source = result.get('source', 'Unknown source')
            date = result.get('date', 'No date')
            
            formatted_results.append(f"{i}. **{title}**\n   Source: {source} | Date: {date}\n   {url}\n")
        
        return "\n".join(formatted_results)
        
    except Exception as e:
        print(f"❌ News search error: {e}")
        return f"News search failed: {e}"


# Convenience functions for common searches
def search_mario_wiki(query):
    """Search Super Mario Wiki specifically."""
    return search_web(query, site="mariowiki.com")

def search_zelda_wiki(query):
    """Search Zelda Wiki specifically.""" 
    return search_web(query, site="zeldawiki.wiki")

def search_wikipedia(query):
    """Search Wikipedia specifically."""
    return search_web(query, site="wikipedia.org")


if __name__ == "__main__":
    # Test the search functions
    print("Testing general search:")
    print(search_web("python programming", max_results=3))
    
    print("\n" + "="*50 + "\n")
    
    print("Testing fandom search:")
    print(search_fandom_specific("diddy kong"))
