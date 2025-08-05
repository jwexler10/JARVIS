# news_scraper.py - Simple BeautifulSoup-only version
import requests
from bs4 import BeautifulSoup
from typing import List, Tuple
import time
from urllib.parse import urlparse
import openai
from memory import load_api_key

# Rate limiting: don't hit the same domain more than once per second
_last_request_time = {}

def rate_limit_check(url: str) -> bool:
    """Simple rate limiting per domain"""
    domain = urlparse(url).netloc
    now = time.time()
    
    if domain in _last_request_time:
        if now - _last_request_time[domain] < 1.0:  # 1 second between requests
            return False
    
    _last_request_time[domain] = now
    return True

def fetch_article_text(url: str, timeout: int = 10) -> Tuple[str, str]:
    """
    Fetch and extract main article text from a URL using BeautifulSoup only.
    Returns (title, content) tuple.
    """
    if not rate_limit_check(url):
        print(f"[Scraper] Rate limiting: skipping {url}")
        return "", ""
    
    try:
        print(f"[Scraper] Fetching: {url[:60]}...")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract title
        title = ""
        title_selectors = ['h1', 'title', '.headline', '.article-title', '.entry-title']
        for selector in title_selectors:
            title_elem = soup.select_one(selector)
            if title_elem and title_elem.get_text().strip():
                title = title_elem.get_text().strip()
                break
        
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "header", "footer", "aside", "menu", "form"]):
            script.decompose()
        
        # Try to find article content
        content = ""
        
        # Look for common article selectors
        article_selectors = [
            'article', '.article-content', '.post-content', '.entry-content',
            '.story-body', '.article-body', '.content', 'main', '.post-body',
            '.article-text', '.story-content'
        ]
        
        for selector in article_selectors:
            elements = soup.select(selector)
            if elements:
                for elem in elements:
                    paragraphs = elem.find_all('p')
                    if len(paragraphs) >= 2:  # At least 2 paragraphs
                        content = '\n'.join([p.get_text().strip() for p in paragraphs if p.get_text().strip()])
                        break
                if content:
                    break
        
        # Fallback: just get all paragraphs
        if not content:
            paragraphs = soup.find_all('p')
            content = '\n'.join([p.get_text().strip() for p in paragraphs if p.get_text().strip()])
        
        # Clean up title
        if title:
            title = title.replace('\n', ' ').replace('\r', ' ')
            title = ' '.join(title.split())  # Remove extra whitespace
            # Remove common site suffixes
            for suffix in [' - CNN', ' | Reuters', ' - BBC', ' | AP News', ' - TechCrunch']:
                if title.endswith(suffix):
                    title = title[:-len(suffix)]
        
        if content and len(content.strip()) > 100:
            print(f"[Scraper] ✅ Extracted {len(content)} chars")
            return title[:100] if title else "Article", content.strip()[:2000]  # Limit to 2000 chars
        else:
            print(f"[Scraper] ❌ Insufficient content from {url}")
            return title[:100] if title else "", ""
            
    except Exception as e:
        print(f"[Scraper] ❌ Error fetching {url}: {e}")
        return "", ""

def summarize_text(text: str, context: str = "news article") -> str:
    """
    Use OpenAI to summarize article text into 2-3 sentences.
    """
    if not text or len(text.strip()) < 50:
        return "Summary not available."
    
    try:
        load_api_key()
        
        prompt = f"""Summarize this {context} in 2-3 clear, informative sentences. Focus on the key facts, events, or insights. Be concise but informative:

{text}

Summary:"""

        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a skilled news summarizer. Create concise, factual summaries."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=150,
            temperature=0.3
        )
        
        summary = response.choices[0].message.content.strip()
        print(f"[Scraper] ✅ Generated summary: {summary[:50]}...")
        return summary
        
    except Exception as e:
        print(f"[Scraper] ❌ Summarization failed: {e}")
        return "Summary not available."

def extract_urls_from_search_results(search_results: str) -> List[str]:
    """
    Extract URLs from search results string.
    Assumes search results are formatted as "1. Title — Description (URL)"
    """
    urls = []
    lines = search_results.strip().split('\n')
    
    for line in lines:
        if '(' in line and ')' in line:
            # Extract URL from parentheses
            start = line.rfind('(')
            end = line.rfind(')')
            if start != -1 and end != -1 and end > start:
                url = line[start+1:end].strip()
                if url.startswith('http'):
                    urls.append(url)
    
    return urls[:5]  # Limit to top 5

def get_news_summaries(query: str, top_k: int = 3) -> List[Tuple[str, str, str]]:
    """
    Get news summaries for a given query.
    Returns list of (title, summary, url) tuples.
    """
    from search import search_web
    
    print(f"[NewsScraper] 🔍 Searching for: {query}")
    
    # Get search results
    search_results = search_web(query)
    if not search_results:
        print(f"[NewsScraper] ❌ No search results for: {query}")
        return []
    
    print(f"[NewsScraper] 📄 Search results: {search_results[:200]}...")
    
    # Extract URLs from search results
    urls = extract_urls_from_search_results(search_results)
    if not urls:
        print(f"[NewsScraper] ❌ No URLs found in search results for: {query}")
        print(f"[NewsScraper] Debug - search results format: {search_results[:500]}")
        return []
    
    print(f"[NewsScraper] 📄 Found {len(urls)} URLs for {query}")
    
    summaries = []
    
    # Process each URL (limit to top_k)
    for i, url in enumerate(urls[:top_k]):
        print(f"[NewsScraper] Processing URL {i+1}/{min(len(urls), top_k)}: {url}")
        
        # Fetch article text
        title, article_text = fetch_article_text(url)
        if not article_text:
            print(f"[NewsScraper] ❌ No content from {url}")
            continue
        
        # Use title from scraping or generate one
        if not title:
            title = f"Article {i+1}"
        
        # Generate summary
        summary = summarize_text(article_text, f"{query} article")
        
        summaries.append((title, summary, url))
        print(f"[NewsScraper] ✅ Added summary for: {title[:50]}...")
        
        # Small delay to be respectful
        time.sleep(0.5)
    
    print(f"[NewsScraper] ✅ Generated {len(summaries)} summaries for {query}")
    return summaries

async def get_news_summaries_async(query: str, top_k: int = 3) -> List[Tuple[str, str, str]]:
    """
    Async version of get_news_summaries to avoid blocking the Discord bot.
    """
    import asyncio
    
    # Run the synchronous function in a thread pool
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, get_news_summaries, query, top_k)

def format_news_section(title: str, summaries: List[Tuple[str, str, str]]) -> str:
    """
    Format a news section for Discord message.
    """
    if not summaries:
        return f"**{title}:**\nNo recent news available.\n"
    
    section = f"**{title}:**\n"
    for i, (article_title, summary, url) in enumerate(summaries, 1):
        # Clean up title
        clean_title = article_title.replace('*', '').replace('_', '').strip()
        if len(clean_title) > 80:
            clean_title = clean_title[:77] + "..."
        
        section += f"{i}. **{clean_title}**\n"
        section += f"   {summary}\n"
        section += f"   [Read more]({url})\n\n"
    
    return section
