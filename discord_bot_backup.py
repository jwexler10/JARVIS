# discord_bot.py
import os
import discord
import json
import random
import datetime
import asyncio
from discord.ext import tasks
from jarvis import ask_jarvis
from memory import load_memory_cache, auto_remember_sync, schedule_index_rebuild
from search import search_web
from weather import get_weather
from news_scraper import get_news_summaries_async, format_news_section
f        # Send the DM
        await user.send(message)
        print(f"[Briefing] ✅ Morning briefing sent to {user.display_name}")
        
    except Exception as e:
        print(f"[Briefing] ❌ Error sending morning briefing: {e}")
        import traceback
        traceback.print_exc()
        
        # Fallback to legacy briefing if enhanced version fails
        try:
            print("[Briefing] 🔄 Attempting fallback to legacy briefing...")
            await send_legacy_briefing(user_id)
        except Exception as fallback_error:
            print(f"[Briefing] ❌ Fallback briefing also failed: {fallback_error}")adlines import (
    get_tech_headlines_data, 
    get_ai_headlines_data,
    get_jets_news_data,
    get_phillies_news_data,
    get_sixers_news_data,
    get_general_sports_data,
    generate_motivational_quote
)

# Load environment variables with proper encoding handling
try:
    # Manual loading with multiple encoding attempts
    encodings_to_try = ['utf-16', 'utf-16-le', 'utf-8-sig', 'utf-8']
    
    for encoding in encodings_to_try:
        try:
            with open('.env', 'r', encoding=encoding) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key.strip()] = value.strip()
                print(f"✅ Successfully loaded .env with {encoding} encoding")
                break
        except (UnicodeDecodeError, FileNotFoundError):
            continue
    else:
        print("❌ Could not read .env file with any encoding")
        
except Exception as e:
    print(f"❌ Error loading .env: {e}")

# Read your bot token from an environment variable
TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    raise RuntimeError("Please set DISCORD_TOKEN in your environment")

# Load the memory cache on startup
load_memory_cache()

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True  # Enable reading message text

client = discord.Client(intents=intents)

# Your user ID for DMs (replace with your actual Discord user ID)
USER_ID = None  # Will be set when the bot identifies you through DMs
BRIEFING_SENT = False  # Track if briefing has been sent this session

# Morning briefing quotes management
QUOTES_FILE = "morning_quotes.json"

def initialize_quotes():
    """Initialize the quotes file if it doesn't exist."""
    default_quotes = [
        "The way to get started is to quit talking and begin doing. - Walt Disney",
        "The pessimist sees difficulty in every opportunity. The optimist sees opportunity in every difficulty. - Winston Churchill",
        "Don't let yesterday take up too much of today. - Will Rogers",
        "You learn more from failure than from success. Don't let it stop you. Failure builds character. - Unknown",
        "It's not whether you get knocked down, it's whether you get up. - Vince Lombardi",
        "If you are working on something that you really care about, you don't have to be pushed. The vision pulls you. - Steve Jobs",
        "People who are crazy enough to think they can change the world, are the ones who do. - Rob Siltanen",
        "Failure will never overtake me if my determination to succeed is strong enough. - Og Mandino",
        "Entrepreneurs are great at dealing with uncertainty and also very good at minimizing risk. That's the classic entrepreneur. - Mohnish Pabrai",
        "We don't have to be smarter than the rest. We have to be more disciplined than the rest. - Warren Buffett",
        "How wonderful it is that nobody need wait a single moment before starting to improve the world. - Anne Frank",
        "Whether you think you can or you think you can't, you're right. - Henry Ford",
        "The future belongs to those who believe in the beauty of their dreams. - Eleanor Roosevelt",
        "It is during our darkest moments that we must focus to see the light. - Aristotle",
        "Whoever is happy will make others happy too. - Anne Frank",
        "Do not go where the path may lead, go instead where there is no path and leave a trail. - Ralph Waldo Emerson",
        "You have been assigned this mountain to show others it can be moved. - Mel Robbins",
        "The only impossible journey is the one you never begin. - Tony Robbins",
        "In the midst of winter, I found there was, within me, an invincible summer. - Albert Camus",
        "Success is not final, failure is not fatal: it is the courage to continue that counts. - Winston Churchill"
    ]
    
    if not os.path.exists(QUOTES_FILE):
        quote_data = {
            "quotes": default_quotes,
            "used_quotes": [],
            "current_index": 0
        }
        with open(QUOTES_FILE, 'w', encoding='utf-8') as f:
            json.dump(quote_data, f, indent=2)
        print(f"[Briefing] Initialized {len(default_quotes)} quotes")

def get_daily_quote():
    """Get the next quote in rotation, cycling through all quotes before repeating."""
    print("[Briefing] 💡 Getting daily quote...")
    initialize_quotes()
    
    try:
        with open(QUOTES_FILE, 'r', encoding='utf-8') as f:
            quote_data = json.load(f)
        
        quotes = quote_data["quotes"]
        used_quotes = quote_data.get("used_quotes", [])
        
        print(f"[Briefing] Quote pool: {len(quotes)} total, {len(used_quotes)} used")
        
        # If we've used all quotes, reset the cycle
        if len(used_quotes) >= len(quotes):
            used_quotes = []
            print("[Briefing] Quote cycle complete, resetting...")
        
        # Find unused quotes
        unused_quotes = [q for q in quotes if q not in used_quotes]
        
        if not unused_quotes:
            # Fallback to random selection
            selected_quote = random.choice(quotes)
        else:
            selected_quote = random.choice(unused_quotes)
        
        print(f"[Briefing] Selected quote: {selected_quote[:50]}...")
        
        # Mark as used and save
        used_quotes.append(selected_quote)
        quote_data["used_quotes"] = used_quotes
        
        with open(QUOTES_FILE, 'w', encoding='utf-8') as f:
            json.dump(quote_data, f, indent=2)
        
        return selected_quote
        
    except Exception as e:
        print(f"[Briefing] Error getting quote: {e}")
        return "Every day is a new beginning. Take a deep breath and start again."

async def get_tech_headlines_enhanced():
    """Get latest tech and AI headlines with summaries."""
    print("[Briefing] 📰 Getting enhanced tech headlines...")
    
    try:
        # Get tech news summaries
        tech_summaries = await get_news_summaries_async("latest technology news", 3)
        ai_summaries = await get_news_summaries_async("latest AI artificial intelligence news", 2)
        
        # Combine and format
        all_summaries = tech_summaries + ai_summaries
        
        if not all_summaries:
            return "No recent tech or AI news available."
        
        return format_news_section("📰 Tech & AI Headlines", all_summaries)
        
    except Exception as e:
        print(f"[Briefing] Error getting enhanced tech headlines: {e}")
        return "📰 **Tech & AI Headlines:**\nUnable to fetch headlines at this time.\n"

async def get_sports_updates_enhanced():
    """Get updates for user's favorite teams with summaries."""
    print("[Briefing] 🏈 Getting enhanced sports updates...")
    
    teams_queries = [
        ("New York Jets news latest", "🏈 Jets"),
        ("Philadelphia Phillies news latest", "⚾ Phillies"), 
        ("Philadelphia 76ers Sixers news latest", "🏀 Sixers")
    ]
    
    all_updates = ""
    
    try:
        for query, team_name in teams_queries:
            print(f"[Briefing] Getting news for {team_name}...")
            summaries = await get_news_summaries_async(query, 1)  # Just 1 top story per team
            
            if summaries:
                title, summary, url = summaries[0]
                clean_title = title.replace('*', '').replace('_', '').strip()
                if len(clean_title) > 60:
                    clean_title = clean_title[:57] + "..."
                
                all_updates += f"**{team_name}:**\n"
                all_updates += f"• **{clean_title}**\n"
                all_updates += f"  {summary}\n"
                all_updates += f"  [Read more]({url})\n\n"
            else:
                all_updates += f"**{team_name}:** No recent news available.\n\n"
        
        return all_updates.strip()
        
    except Exception as e:
        print(f"[Briefing] Error getting enhanced sports updates: {e}")
        return "🏈 **Sports Updates:**\nUnable to fetch sports news at this time."

# Legacy functions for backward compatibility (simplified versions)
def get_tech_headlines():
    """Legacy function - returns simplified tech headlines."""
    print("[Briefing] 📰 Using legacy tech headlines...")
    try:
        tech_results = search_web("latest technology news today")
        ai_results = search_web("latest AI news today")
        
        headlines = []
        for result_set in [tech_results, ai_results]:
            if result_set:
                for line in result_set.split('\n')[:2]:  # Just 2 from each
                    if line.strip() and '—' in line:
                        headlines.append(line.strip())
        
        return headlines[:5]
    except Exception as e:
        print(f"[Briefing] Error in legacy tech headlines: {e}")
        return ["Unable to fetch tech headlines."]

def get_sports_updates():
    """Legacy function - returns simplified sports updates."""
    print("[Briefing] 🏈 Using legacy sports updates...")
    teams = {
        "🏈 Jets": "New York Jets latest news",
        "⚾ Phillies": "Philadelphia Phillies latest news", 
        "🏀 Sixers": "Philadelphia 76ers latest news"
    }
    
    updates = {}
    for team_emoji, search_query in teams.items():
        try:
            results = search_web(search_query)
            if results:
                lines = [line.strip() for line in results.split('\n') if line.strip()]
                if lines:
                    updates[team_emoji] = lines[0].split('—')[0].strip() if '—' in lines[0] else lines[0]
                else:
                    updates[team_emoji] = "No recent updates"
            else:
                updates[team_emoji] = "No recent updates"
        except:
            updates[team_emoji] = "Unable to fetch update"
    
    return updates

def format_weather_info():
    """Get and format weather information."""
    print("[Briefing] 🌤️ Getting weather information...")
    try:
        weather_report = get_weather("Philadelphia")
        print(f"[Briefing] Weather report received: {weather_report[:100] if weather_report else 'None'}...")
        # Simple formatting - extract key temperature info if available
        if weather_report:
            return f"🌤️ Philadelphia: {weather_report}"
        else:
            return "🌤️ Philadelphia: Weather information unavailable"
    except Exception as e:
        print(f"[Briefing] Error getting weather: {e}")
        return "🌤️ Philadelphia: Weather information unavailable"

async def send_morning_briefing(user_id):
    """Send the complete morning briefing to the user."""
    try:
        print(f"[Briefing] 🚀 Starting morning briefing for user ID: {user_id}")
        
        user = await client.fetch_user(user_id)
        if not user:
            print("[Briefing] ❌ Could not find user for morning briefing")
            return
        
        print(f"[Briefing] ✅ Found user: {user.display_name}")
        print("[Briefing] 📊 Generating morning briefing using NewsAPI...")
        
        # Get weather first
        print("[Briefing] Step 1/6: Getting weather...")
        weather_info = format_weather_info()
        
        # Get tech headlines using discover_headlines.py
        print("[Briefing] Step 2/6: Getting tech headlines...")
        tech_data = get_tech_headlines_data(3)
        
        # Get AI headlines using discover_headlines.py
        print("[Briefing] Step 3/6: Getting AI headlines...")
        ai_data = get_ai_headlines_data(2)
        
        # Get sports updates using discover_headlines.py
        print("[Briefing] Step 4/6: Getting sports updates...")
        jets_data = get_jets_news_data(1)
        phillies_data = get_phillies_news_data(1)
        sixers_data = get_sixers_news_data(1)
        
        # Get general sports updates
        print("[Briefing] Step 5/6: Getting general sports...")
        nfl_data = get_general_sports_data("nfl", 1)
        mlb_data = get_general_sports_data("mlb", 1)
        nba_data = get_general_sports_data("nba", 1)
        
        # Generate motivational quote
        print("[Briefing] Step 6/6: Generating motivational quote...")
        motivational_quote = generate_motivational_quote()
        
        print("[Briefing] 📝 Formatting message...")
        
        # Start building the message
        message = "☀️ **Good morning, Jason!**\n\n"
        
        # Weather first
        message += f"{weather_info}\n\n"
        
        # Tech & AI Headlines
        message += "📰 **Tech & AI Headlines:**\n"
        all_tech_ai = tech_data + ai_data
        if all_tech_ai:
            for title, summary, url in all_tech_ai:
                clean_title = title.replace('*', '').replace('_', '').strip()
                if len(clean_title) > 60:
                    clean_title = clean_title[:57] + "..."
                message += f"• **{clean_title}**\n"
                message += f"  {summary}\n"
                message += f"  [Read more]({url})\n\n"
        else:
            message += "No recent tech or AI news available.\n\n"
        
        # Sports Updates - Favorite Teams
        message += "🏈 **Your Teams:**\n"
        
        # Jets
        if jets_data:
            title, summary, url = jets_data[0]
            clean_title = title.replace('*', '').replace('_', '').strip()
            if len(clean_title) > 60:
                clean_title = clean_title[:57] + "..."
            message += f"**🏈 Jets:** {clean_title}\n"
            message += f"  {summary}\n"
            message += f"  [Read more]({url})\n\n"
        else:
            message += "**🏈 Jets:** No recent news available.\n\n"
        
        # Phillies
        if phillies_data:
            title, summary, url = phillies_data[0]
            clean_title = title.replace('*', '').replace('_', '').strip()
            if len(clean_title) > 60:
                clean_title = clean_title[:57] + "..."
            message += f"**⚾ Phillies:** {clean_title}\n"
            message += f"  {summary}\n"
            message += f"  [Read more]({url})\n\n"
        else:
            message += "**⚾ Phillies:** No recent news available.\n\n"
        
        # Sixers
        if sixers_data:
            title, summary, url = sixers_data[0]
            clean_title = title.replace('*', '').replace('_', '').strip()
            if len(clean_title) > 60:
                clean_title = clean_title[:57] + "..."
            message += f"**🏀 Sixers:** {clean_title}\n"
            message += f"  {summary}\n"
            message += f"  [Read more]({url})\n\n"
        else:
            message += "**🏀 Sixers:** No recent news available.\n\n"
        
        # General Sports
        message += "🏆 **Around the Leagues:**\n"
        
        # Add one story from each general league if available
        for league_data, emoji, name in [(nfl_data, "🏈", "NFL"), (mlb_data, "⚾", "MLB"), (nba_data, "🏀", "NBA")]:
            if league_data:
                title, summary, url = league_data[0]
                clean_title = title.replace('*', '').replace('_', '').strip()
                if len(clean_title) > 50:
                    clean_title = clean_title[:47] + "..."
                message += f"**{emoji} {name}:** {clean_title}\n"
                message += f"  {summary[:100]}{'...' if len(summary) > 100 else ''}\n"
                message += f"  [Read more]({url})\n\n"
        
        # Motivational quote at the end
        message += "💡 **Motivational Quote:**\n"
        message += f"*\"{motivational_quote}\"*\n\n"
        
        message += "Have a fantastic day! 🚀"
        
        print(f"[Briefing] 📤 Sending briefing message (length: {len(message)} chars)...")
        
        # Send the DM
        await user.send(message)
        print(f"[Briefing] ✅ Enhanced morning briefing sent to {user.display_name}")
        
    except Exception as e:
        print(f"[Briefing] ❌ Error sending enhanced morning briefing: {e}")
        import traceback
        traceback.print_exc()
        
        # Fallback to legacy briefing if enhanced version fails
        try:
            print("[Briefing] � Attempting fallback to legacy briefing...")
            await send_legacy_briefing(user_id)
        except Exception as fallback_error:
            print(f"[Briefing] ❌ Fallback briefing also failed: {fallback_error}")

async def send_legacy_briefing(user_id):
    """Fallback briefing using legacy functions (simple search results)."""
    try:
        user = await client.fetch_user(user_id)
        if not user:
            return
        
        # Use legacy functions
        tech_headlines = get_tech_headlines()
        sports_updates = get_sports_updates()
        weather_info = format_weather_info()
        daily_quote = get_daily_quote()
        
        # Format legacy message
        message = "☀️ **Good morning, Jason!** (Legacy Mode)\n\n"
        
        # Tech & AI Headlines (legacy format)
        message += "�📰 **Tech & AI Headlines:**\n"
        if tech_headlines:
            for i, headline in enumerate(tech_headlines, 1):
                message += f"{i}. {headline}\n"
        else:
            message += "No headlines available today.\n"
        message += "\n"
        
        # Sports Updates (legacy format)
        for team, update in sports_updates.items():
            message += f"{team}: {update}\n"
        message += "\n"
        
        # Weather & Quote (unchanged)
        message += f"{weather_info}\n\n"
        message += "💡 **Quote of the Day:**\n"
        message += f"*\"{daily_quote}\"*\n\n"
        message += "Have a fantastic day! 🚀"
        
        await user.send(message)
        print(f"[Briefing] ✅ Legacy morning briefing sent to {user.display_name}")
        
    except Exception as e:
        print(f"[Briefing] ❌ Error sending legacy briefing: {e}")

@client.event
async def on_ready():
    global USER_ID, BRIEFING_SENT
    print(f"🍀 Logged in as {client.user}")
    
    # Try to load USER_ID from a config file if it exists
    try:
        with open("user_config.json", "r") as f:
            config = json.load(f)
            USER_ID = config.get("user_id")
            print(f"[Config] Loaded user ID: {USER_ID}")
    except FileNotFoundError:
        print("[Config] No user_config.json found, will detect user from first DM")
    
    # Send morning briefing immediately if we have a user ID
    if USER_ID and not BRIEFING_SENT:
        print("[Briefing] 🌅 Sending morning briefing on startup...")
        await send_morning_briefing(USER_ID)
        BRIEFING_SENT = True

@client.event
async def on_message(message):
    global USER_ID, BRIEFING_SENT
    
    # ignore other bots (including yourself)
    if message.author.bot:
        return

    # You can scope this to just DMs or a particular channel:
    if isinstance(message.channel, discord.DMChannel):
        # Set user ID for morning briefings (first time they DM)
        if USER_ID is None:
            USER_ID = message.author.id
            print(f"[Config] User ID detected: {USER_ID}")
            
            # Save user ID to config for future sessions
            try:
                with open("user_config.json", "w") as f:
                    json.dump({"user_id": USER_ID}, f)
                print("[Config] User ID saved to user_config.json")
            except Exception as e:
                print(f"[Config] Failed to save user ID: {e}")
            
            # Send briefing immediately for new user
            if not BRIEFING_SENT:
                print("[Briefing] 🌅 Sending morning briefing for new user...")
                await send_morning_briefing(message.author.id)
                BRIEFING_SENT = True
        
        user_input = message.content.strip()
        
        # Check for manual briefing request
        if user_input.lower() in ["briefing", "morning briefing", "daily briefing", "!briefing"]:
            print("[Command] Manual briefing requested")
            await send_morning_briefing(message.author.id)
            return
        
        # Ask Jarvis in text mode
        reply = ask_jarvis(user_input, text_mode=True)
        # Send the reply back
        await message.channel.send(reply)
        # Store the conversation in memory for persistence (synchronous for immediate availability)
        auto_remember_sync(user_input, reply)
        print(f"[Discord] Stored memory: {user_input[:30]}... -> {reply[:30]}...")

# Gracefully rebuild memory index on shutdown
@client.event
async def on_close():
    schedule_index_rebuild()

if __name__ == "__main__":
    client.run(TOKEN)
