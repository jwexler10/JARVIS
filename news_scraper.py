# news_scraper.py
import asyncio
import aiohttp
import requests
from bs4 import BeautifulSoup
from typing import List, Tuple, Optional
import json
import time
from urllib.parse import urlparse
import openai
from memory import load_api_key

# Try to import newspaper3k, but handle the dependency error gracefully
NEWSPAPER_AVAILABLE = False
try:
    from newspaper import Article
    NEWSPAPER_AVAILABLE = True
    print("[Scraper] newspaper3k loaded successfully")
except ImportError as e:
    print(f"[Scraper] newspaper3k not available: {e}")
    print("[Scraper] Will use BeautifulSoup only for article extraction")

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

def fetch_article_text(url: str, timeout: int = 10) -> str:
    """
    Fetch and extract main article text from a URL.
    Uses BeautifulSoup primarily, with newspaper3k as fallback if available.
    """
    if not rate_limit_check(url):
        print(f"[Scraper] Rate limiting: skipping {url}")
        return ""
    
    try:
        print(f"[Scraper] Fetching: {url[:60]}...")
        
        # Method 1: BeautifulSoup (more reliable with current setup)
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers, timeout=timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "header", "footer", "aside", "form", "iframe"]):
                script.decompose()
            
            # Try to find article content using multiple strategies
            content = ""
            
            # Strategy 1: Look for common article selectors
            article_selectors = [
                'article', '.article-content', '.post-content', '.entry-content',
                '.story-body', '.article-body', '.content', 'main', '.main-content',
                '.post-body', '.story-content', '[role="main"]', '.article-text'
            ]
            
            for selector in article_selectors:
                elements = soup.select(selector)
                if elements:
                    for elem in elements:
                        paragraphs = elem.find_all('p')
                        if len(paragraphs) >= 2:  # At least 2 paragraphs
                            content = '\n'.join([p.get_text().strip() for p in paragraphs if p.get_text().strip()])
                            break
                    if content and len(content.strip()) > 200:  # Ensure substantial content
                        break
            
            # Strategy 2: Look for div with lots of text
            if not content:
                all_divs = soup.find_all('div')
                for div in all_divs:
                    div_text = div.get_text().strip()
                    if len(div_text) > 500 and len(div.find_all('p')) >= 3:
                        content = div_text
                        break
            
            # Strategy 3: Fallback - just get all paragraphs
            if not content:
                paragraphs = soup.find_all('p')
                all_text = '\n'.join([p.get_text().strip() for p in paragraphs if p.get_text().strip()])
                if len(all_text) > 200:
                    content = all_text
            
            if content and len(content.strip()) > 100:
                print(f"[Scraper] ✅ Extracted {len(content)} chars with BeautifulSoup")
                return content.strip()[:2000]  # Limit to 2000 chars
                
        except Exception as e:
            print(f"[Scraper] BeautifulSoup failed: {e}")
        
        # Method 2: newspaper3k (if available)
        if NEWSPAPER_AVAILABLE:
            try:
                article = Article(url)
                article.download()
                article.parse()
                
                if article.text and len(article.text.strip()) > 100:
                    print(f"[Scraper] ✅ Extracted {len(article.text)} chars with newspaper3k")
                    return article.text.strip()[:2000]  # Limit to 2000 chars
            except Exception as e:
                print(f"[Scraper] newspaper3k failed: {e}")
        
        print(f"[Scraper] ❌ Failed to extract content from {url}")
        return ""
        
    except Exception as e:
        print(f"[Scraper] ❌ Error fetching {url}: {e}")
        return ""

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
    Try multiple formats to find URLs.
    """
    urls = []
    lines = search_results.strip().split('\n')
    
    print(f"[NewsScraper] Debug - parsing {len(lines)} result lines")
    
    for i, line in enumerate(lines):
        print(f"[NewsScraper] Line {i}: {line[:100]}...")
        
        # Method 1: Look for URLs in parentheses - "Title (URL)"
        if '(' in line and ')' in line:
            start = line.rfind('(')
            end = line.rfind(')')
            if start != -1 and end != -1 and end > start:
                url = line[start+1:end].strip()
                if url.startswith('http'):
                    urls.append(url)
                    print(f"[NewsScraper] Found URL in parentheses: {url}")
                    continue
        
        # Method 2: Look for URLs anywhere in the line
        import re
        url_pattern = r'https?://[^\s\)]+(?=\s|$|\))'
        found_urls = re.findall(url_pattern, line)
        for url in found_urls:
            # Clean up URL (remove trailing punctuation)
            url = url.rstrip('.,!?;:')
            if url not in urls:
                urls.append(url)
                print(f"[NewsScraper] Found URL with regex: {url}")
        
        # Method 3: Look for — followed by URL pattern
        if '—' in line:
            parts = line.split('—')
            if len(parts) > 1:
                url_part = parts[-1].strip()
                url_match = re.search(r'https?://[^\s\)]+', url_part)
                if url_match:
                    url = url_match.group().rstrip('.,!?;:')
                    if url not in urls:
                        urls.append(url)
                        print(f"[NewsScraper] Found URL after dash: {url}")
    
    print(f"[NewsScraper] Total URLs extracted: {len(urls)}")
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
    
    print(f"[NewsScraper] 📄 Raw search results:")
    print(f"[NewsScraper] {search_results}")
    print(f"[NewsScraper] End raw results")
    
    # Extract URLs from search results
    urls = extract_urls_from_search_results(search_results)
    if not urls:
        print(f"[NewsScraper] ❌ No URLs found in search results for: {query}")
        print(f"[NewsScraper] Search results sample: {search_results[:500]}")
        return []
    
    print(f"[NewsScraper] 📄 Found {len(urls)} URLs for {query}: {urls}")
    
    summaries = []
    
    # Process each URL (limit to top_k)
    for i, url in enumerate(urls[:top_k]):
        print(f"[NewsScraper] Processing URL {i+1}/{min(len(urls), top_k)}: {url}")
        
        # Fetch article text
        article_text = fetch_article_text(url)
        if not article_text:
            print(f"[NewsScraper] ❌ No content extracted from {url}")
            continue
        
        print(f"[NewsScraper] ✅ Got {len(article_text)} chars of content")
        
        # Generate summary
        summary = summarize_text(article_text, f"{query} article")
        
        # Extract title from URL or use first line of article
        title = f"Article {i+1}"
        try:
            # Try to get title from the same request we used for content
            if NEWSPAPER_AVAILABLE:
                article = Article(url)
                article.download()
                article.parse()
                if article.title:
                    title = article.title[:100]  # Limit title length
            else:
                # Extract title using BeautifulSoup
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
                response = requests.get(url, headers=headers, timeout=5)
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Try multiple title selectors
                title_elem = soup.find('title')
                if not title_elem:
                    title_elem = soup.find('h1')
                if not title_elem:
                    title_elem = soup.select_one('.article-title, .post-title, .entry-title')
                
                if title_elem:
                    title = title_elem.get_text().strip()[:100]
        except Exception as title_error:
            print(f"[NewsScraper] ❌ Title extraction failed: {title_error}")
            # If title extraction fails, try to use first sentence of summary
            if summary and len(summary) > 20:
                first_sentence = summary.split('.')[0]
                if len(first_sentence) > 10:
                    title = first_sentence[:80] + "..."
        
        print(f"[NewsScraper] ✅ Title: {title}")
        print(f"[NewsScraper] ✅ Summary: {summary[:100]}...")
        
        summaries.append((title, summary, url))
        
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
