# discover_headlines.py

from newsapi import NewsApiClient
from newspaper import Article
import openai
import textwrap

# === Configuration ===

# Load API keys from environment variables for security
import os
NEWS_API_KEY = os.environ.get("NEWS_API_KEY", "")   # Your NewsAPI key
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")   # Your OpenAI key

# Authenticate with OpenAI
openai.api_key = OPENAI_API_KEY
news = NewsApiClient(api_key=NEWS_API_KEY)

# === Helper Functions ===

def extract_text(url):
    """
    Download and parse article text from a URL using newspaper3k.
    """
    article = Article(url)
    article.download()
    article.parse()
    return article.text


def summarize_openai(text):
    """
    Summarize text using OpenAI's new Python library interface (v1+).
    """
    try:
        # Use more text for better context, but still reasonable limits
        if len(text) > 4000:
            text = text[:4000]
        
        resp = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Provide a very brief summary in exactly 10-20 words that captures the main point. Be concise and direct."},
                {"role": "user", "content": text}
            ],
            max_tokens=50,  # Reduced to ensure short summaries
            timeout=15  # Increased timeout for better processing
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error in OpenAI summarization: {e}")
        return "Summary unavailable due to processing error."


def process_section(title, articles, limit):
    """
    Print a section header, then for each article up to 'limit',
    display title, URL, and an OpenAI-generated summary.
    """
    print(f"\n=== {title} ===")
    for idx, art in enumerate(articles[:limit], start=1):
        art_title = art.get("title", "No title")
        url = art.get("url", "")
        print(f"\n{idx}. {art_title}\n{url}")
        try:
            full_text = extract_text(url)
            summary = summarize_openai(full_text)
            print(f"Summary: {summary}")
        except Exception as e:
            print(f"Error summarizing article: {e}")


def get_section_data(title, articles, limit):
    """
    Process articles and return structured data for Discord bot use.
    Returns list of tuples: (title, summary, url)
    """
    results = []
    for art in articles[:limit]:
        art_title = art.get("title", "No title")
        url = art.get("url", "")
        try:
            full_text = extract_text(url)
            summary = summarize_openai(full_text)
            results.append((art_title, summary, url))
        except Exception as e:
            print(f"Error processing article {art_title}: {e}")
            # Skip articles that fail instead of including error messages
            continue
    return results


def generate_motivational_quote():
    """
    Generate a motivational quote using a curated database of real quotes.
    Tracks used quotes to avoid repetition.
    """
    import json
    import random
    import os
    
    # Database of real motivational quotes
    quote_database = [
        "The way to get started is to quit talking and begin doing. - Walt Disney",
        "The pessimist sees difficulty in every opportunity. The optimist sees opportunity in every difficulty. - Winston Churchill",
        "Don't let yesterday take up too much of today. - Will Rogers",
        "It's not whether you get knocked down, it's whether you get up. - Vince Lombardi",
        "If you are working on something that you really care about, you don't have to be pushed. The vision pulls you. - Steve Jobs",
        "People who are crazy enough to think they can change the world, are the ones who do. - Rob Siltanen",
        "Failure will never overtake me if my determination to succeed is strong enough. - Og Mandino",
        "We don't have to be smarter than the rest. We have to be more disciplined than the rest. - Warren Buffett",
        "Whether you think you can or you think you can't, you're right. - Henry Ford",
        "The future belongs to those who believe in the beauty of their dreams. - Eleanor Roosevelt",
        "It is during our darkest moments that we must focus to see the light. - Aristotle",
        "Do not go where the path may lead, go instead where there is no path and leave a trail. - Ralph Waldo Emerson",
        "The only impossible journey is the one you never begin. - Tony Robbins",
        "In the midst of winter, I found there was, within me, an invincible summer. - Albert Camus",
        "Success is not final, failure is not fatal: it is the courage to continue that counts. - Winston Churchill",
        "Believe you can and you're halfway there. - Theodore Roosevelt",
        "The only way to do great work is to love what you do. - Steve Jobs",
        "Life is what happens to you while you're busy making other plans. - John Lennon",
        "The mind is everything. What you think you become. - Buddha",
        "Be yourself; everyone else is already taken. - Oscar Wilde",
        "Two roads diverged in a wood, and I— I took the one less traveled by, And that has made all the difference. - Robert Frost",
        "Yesterday is history, tomorrow is a mystery, today is a gift of God, which is why we call it the present. - Bill Keane",
        "A person who never made a mistake never tried anything new. - Albert Einstein",
        "The best time to plant a tree was 20 years ago. The second best time is now. - Chinese Proverb",
        "Your limitation—it's only your imagination. - Unknown",
        "Great things never come from comfort zones. - Unknown",
        "Dream it. Wish it. Do it. - Unknown",
        "Success doesn't just find you. You have to go out and get it. - Unknown",
        "The harder you work for something, the greater you'll feel when you achieve it. - Unknown",
        "Dream bigger. Do bigger. - Unknown",
        "Don't stop when you're tired. Stop when you're done. - Unknown",
        "Wake up with determination. Go to bed with satisfaction. - Unknown",
        "Do something today that your future self will thank you for. - Sean Higgins",
        "Little things make big days. - Unknown",
        "It's going to be hard, but hard does not mean impossible. - Unknown",
        "Don't wait for opportunity. Create it. - Unknown",
        "Sometimes we're tested not to show our weaknesses, but to discover our strengths. - Unknown",
        "The key to success is to focus on goals, not obstacles. - Unknown",
        "Dream it. Believe it. Build it. - Unknown",
        "What lies behind us and what lies before us are tiny matters compared to what lies within us. - Ralph Waldo Emerson",
        "I have not failed. I've just found 10,000 ways that won't work. - Thomas Edison",
        "A winner is a dreamer who never gives up. - Nelson Mandela",
        "You are never too old to set another goal or to dream a new dream. - C.S. Lewis",
        "The only person you are destined to become is the person you decide to be. - Ralph Waldo Emerson",
        "Go confidently in the direction of your dreams. Live the life you have imagined. - Henry David Thoreau",
        "When you have a dream, you've got to grab it and never let go. - Carol Burnett",
        "Nothing is impossible. The word itself says 'I'm possible!' - Audrey Hepburn",
        "There is only one way to avoid criticism: do nothing, say nothing, and be nothing. - Aristotle",
        "Ask and it will be given to you; search, and you will find; knock and the door will be opened for you. - Jesus Christ",
        "The only thing we have to fear is fear itself. - Franklin D. Roosevelt",
        "Darkness cannot drive out darkness: only light can do that. Hate cannot drive out hate: only love can do that. - Martin Luther King Jr.",
        "Do one thing every day that scares you. - Eleanor Roosevelt",
        "Well done is better than well said. - Benjamin Franklin",
        "The best revenge is massive success. - Frank Sinatra",
        "If you do what you always did, you will get what you always got. - Tony Robbins",
        "A goal is not always meant to be reached, it often serves simply as something to aim at. - Bruce Lee",
        "Success is walking from failure to failure with no loss of enthusiasm. - Winston Churchill",
        "Keep your face always toward the sunshine—and shadows will fall behind you. - Walt Whitman",
        "You have been assigned this mountain to show others it can be moved. - Mel Robbins",
        "Difficult roads often lead to beautiful destinations. The best is yet to come. - Zig Ziglar",
        "Believe in yourself and all that you are. Know that there is something inside you that is greater than any obstacle. - Christian D. Larson",
        "Champions train, losers complain. - Unknown"
    ]
    
    quotes_file = "motivational_quotes_used.json"
    
    try:
        # Load previously used quotes
        if os.path.exists(quotes_file):
            with open(quotes_file, 'r', encoding='utf-8') as f:
                used_quotes = json.load(f)
        else:
            used_quotes = []
        
        # Find unused quotes
        unused_quotes = [q for q in quote_database if q not in used_quotes]
        
        # If all quotes have been used, reset the list
        if not unused_quotes:
            unused_quotes = quote_database.copy()
            used_quotes = []
            print("[Quote] All quotes used, resetting database...")
        
        # Select a random unused quote
        selected_quote = random.choice(unused_quotes)
        
        # Add to used quotes and save
        used_quotes.append(selected_quote)
        with open(quotes_file, 'w', encoding='utf-8') as f:
            json.dump(used_quotes, f, indent=2, ensure_ascii=False)
        
        print(f"[Quote] Selected: {selected_quote[:50]}...")
        return selected_quote
        
    except Exception as e:
        print(f"Error selecting motivational quote: {e}")
        return "The way to get started is to quit talking and begin doing. - Walt Disney"

# === API Functions for Discord Bot ===

def get_tech_headlines_data(limit=3):
    """Get technology headlines data for Discord bot."""
    try:
        tech = news.get_top_headlines(category="technology", language="en", page_size=limit)
        return get_section_data("Technology Headlines", tech.get("articles", []), limit)
    except Exception as e:
        print(f"Error fetching tech headlines: {e}")
        return []


def get_ai_headlines_data(limit=2):
    """Get AI headlines data for Discord bot."""
    try:
        ai = news.get_everything(
            q="artificial intelligence OR AI OR machine learning",
            language="en",
            sort_by="publishedAt",
            page_size=limit
        )
        return get_section_data("AI Headlines", ai.get("articles", []), limit)
    except Exception as e:
        print(f"Error fetching AI headlines: {e}")
        return []


def get_jets_news_data(limit=1):
    """Get New York Jets news data for Discord bot."""
    try:
        jets = news.get_everything(
            q="New York Jets NFL",
            language="en",
            sort_by="publishedAt",
            page_size=limit
        )
        return get_section_data("New York Jets", jets.get("articles", []), limit)
    except Exception as e:
        print(f"Error fetching Jets news: {e}")
        return []


def get_phillies_news_data(limit=1):
    """Get Philadelphia Phillies news data for Discord bot."""
    try:
        phillies = news.get_everything(
            q="Philadelphia Phillies MLB baseball",
            language="en",
            sort_by="publishedAt",
            page_size=limit
        )
        return get_section_data("Philadelphia Phillies", phillies.get("articles", []), limit)
    except Exception as e:
        print(f"Error fetching Phillies news: {e}")
        return []


def get_sixers_news_data(limit=1):
    """Get Philadelphia 76ers news data for Discord bot."""
    try:
        sixers = news.get_everything(
            q="Philadelphia 76ers OR Sixers NBA basketball",
            language="en",
            sort_by="publishedAt",
            page_size=limit
        )
        return get_section_data("Philadelphia 76ers", sixers.get("articles", []), limit)
    except Exception as e:
        print(f"Error fetching Sixers news: {e}")
        return []


def get_general_sports_data(sport, limit=2):
    """Get general sports news data for Discord bot."""
    try:
        if sport.lower() == "nfl":
            query = "NFL football news -Jets"
        elif sport.lower() == "mlb":
            query = "MLB baseball news -Phillies"
        elif sport.lower() == "nba":
            query = "NBA basketball news -76ers -Sixers"
        elif sport.lower() == "golf":
            query = "PGA golf tournament news"
        elif sport.lower() == "liverpool":
            query = "Liverpool FC Premier League football soccer"
        else:
            return []
            
        results = news.get_everything(
            q=query,
            language="en",
            sort_by="publishedAt",
            page_size=limit
        )
        return get_section_data(f"{sport.upper()}", results.get("articles", []), limit)
    except Exception as e:
        print(f"Error fetching {sport} news: {e}")
        return []


def get_league_bullet_news(sport, limit=3):
    """Get very brief bullet-point news for general league updates."""
    try:
        if sport.lower() == "nfl":
            # Use the same query as the main() function's "Around the NFL"
            query = "NFL football NOT Jets"
        elif sport.lower() == "mlb":
            # Use the same query as the main() function's "Around MLB"
            query = "MLB baseball NOT Phillies"
        elif sport.lower() == "nba":
            # Use the same query as the main() function's "Around the NBA"
            query = "NBA basketball NOT 76ers NOT Sixers"
        elif sport.lower() == "golf":
            query = "PGA Tour golf tournament winner"
            limit = 1  # Only one golf story
        else:
            return []
            
        results = news.get_everything(
            q=query,
            language="en",
            sort_by="publishedAt",
            page_size=limit
        )
        
        # Process with very short summaries for bullet points
        bullet_results = []
        for art in results.get("articles", [])[:limit]:
            art_title = art.get("title", "No title")
            url = art.get("url", "")
            try:
                full_text = extract_text(url)
                # Use a special short summarization for bullets
                resp = openai.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "Provide an extremely brief 5-10 word summary capturing the main point."},
                        {"role": "user", "content": full_text[:2000]}
                    ],
                    max_tokens=25,
                    timeout=10
                )
                summary = resp.choices[0].message.content.strip()
                bullet_results.append((art_title, summary, url))
            except Exception as e:
                print(f"Error processing bullet article {art_title}: {e}")
                continue
        return bullet_results
    except Exception as e:
        print(f"Error fetching {sport} bullet news: {e}")
        return []


# === Fetch & Summarize Sections ===

def main():
    # 1. Technology headlines
    tech = news.get_top_headlines(category="technology", language="en", page_size=5)
    process_section("Technology Headlines", tech.get("articles", []), limit=5)

    # 2. AI-specific headlines
    ai = news.get_everything(
        q="artificial intelligence OR AI OR machine learning",
        language="en",
        sort_by="publishedAt",
        page_size=5
    )
    process_section("AI Headlines", ai.get("articles", []), limit=5)

    # 3. New York Jets
    jets = news.get_everything(
        q="New York Jets NFL",
        language="en",
        sort_by="publishedAt",
        page_size=3
    )
    process_section("New York Jets", jets.get("articles", []), limit=3)

    # 4. Philadelphia Phillies
    phillies = news.get_everything(
        q="Philadelphia Phillies MLB baseball",
        language="en",
        sort_by="publishedAt",
        page_size=3
    )
    process_section("Philadelphia Phillies", phillies.get("articles", []), limit=3)

    # 5. Philadelphia 76ers
    sixers = news.get_everything(
        q="Philadelphia 76ers OR Sixers NBA basketball",
        language="en",
        sort_by="publishedAt",
        page_size=3
    )
    process_section("Philadelphia 76ers", sixers.get("articles", []), limit=3)

    # 6. Around the NFL (excluding Jets)
    nfl = news.get_everything(
        q="NFL football NOT Jets",
        language="en",
        sort_by="publishedAt",
        page_size=4
    )
    process_section("Around the NFL", nfl.get("articles", []), limit=4)

    # 7. Around MLB (excluding Phillies)
    mlb = news.get_everything(
        q="MLB baseball NOT Phillies",
        language="en",
        sort_by="publishedAt",
        page_size=4
    )
    process_section("Around MLB", mlb.get("articles", []), limit=4)

    # 8. Around the NBA (excluding 76ers)
    nba = news.get_everything(
        q="NBA basketball NOT 76ers NOT Sixers",
        language="en",
        sort_by="publishedAt",
        page_size=4
    )
    process_section("Around the NBA", nba.get("articles", []), limit=4)

    print("\n=== End of Briefing ===")

if __name__ == "__main__":
    main()
