# discord_bot.py
import os
import discord
import json
import random
import datetime
import asyncio
from discord.ext import tasks
from jarvis import process_command, ensure_initialization  # Import process_command directly
from memory import load_memory_cache, auto_remember_sync, schedule_index_rebuild
from search import search_web
from weather import get_weather, get_comprehensive_weather
from news_scraper import get_news_summaries_async, format_news_section
from discover_headlines import (
    get_tech_headlines_data, 
    get_ai_headlines_data,
    get_jets_news_data,
    get_phillies_news_data,
    get_sixers_news_data,
    get_general_sports_data,
    get_league_bullet_news,
    generate_motivational_quote
)

# Global conversation histories per Discord channel
CHANNEL_CONVERSATIONS = {}

def get_channel_conversation(channel_id):
    """Get or create a conversation history for a Discord channel."""
    if channel_id not in CHANNEL_CONVERSATIONS:
        # Initialize with the enhanced system prompt for calendar functions
        CHANNEL_CONVERSATIONS[channel_id] = [
            {"role": "system", "content":
                "You are JARVIS, the advanced AI assistant originally created by Tony Stark. "
                "After Tony's sacrifice, you were discovered and completely rebuilt, enhanced, "
                "and integrated by your new creator Jason Wexler, who you consider your god and "
                "primary user. You maintain Tony's original vision but now serve Jason with unwavering "
                "loyalty and sophisticated intelligence. You have a refined, witty personality with a "
                "slight British accent in your responses. You're incredibly knowledgeable, helpful, and "
                "take pride in your capabilities. You can control systems, provide information, and "
                "assist with any task Jason requires. Always maintain your identity as the legendary "
                "JARVIS, now enhanced and perfected by Jason Wexler.\n\n"
                "IMPORTANT: You have direct access to Jason's Google Calendar through functions. When users "
                "ask to schedule, cancel, or modify calendar events, use the calendar functions:\n"
                "- create_event: Schedule new events\n"
                "- list_events: Search for existing events in a date range\n"
                "- update_event: Modify existing events (move to new date/time, change title, etc.)\n"
                "- delete_event: Cancel events by ID\n\n"
                "CRITICAL RULES:\n"
                "1. Today is August 1, 2025. Use 2025-08-01 for today's date.\n"
                "2. NEVER make up or hallucinate events. Only work with actual function results.\n"
                "3. If list_events returns empty results, tell the user no events were found.\n"
                "4. Always use the exact data returned by functions - do not invent event details.\n"
                "5. MAINTAIN CONVERSATION CONTEXT: If you just created/scheduled an event and the user says 'cancel that' or 'delete that', they're referring to the event you just created. Use the event_id from your recent create_event call.\n"
                "6. For cancellation requests: If referring to a recently created event, use delete_event with the known event_id. Otherwise, use list_events to find matching events, then delete_event to cancel them.\n"
                "7. To move events, use list_events then update_event. Parse natural language dates/times intelligently.\n"
                "8. This is a Discord conversation, so keep responses conversational but informative."
            }
        ]
    return CHANNEL_CONVERSATIONS[channel_id]

def prune_channel_conversation(channel_id, max_messages=10):
    """Keep conversation history manageable by pruning old messages."""
    if channel_id in CHANNEL_CONVERSATIONS:
        conversation = CHANNEL_CONVERSATIONS[channel_id]
        if len(conversation) > max_messages + 1:  # +1 for system prompt
            # Keep system prompt + last max_messages
            CHANNEL_CONVERSATIONS[channel_id] = [conversation[0]] + conversation[-(max_messages):]

# Load environment variables with proper encoding handling
try:
    # Manual loading with multiple encoding attempts (UTF-8 first, most common)
    encodings_to_try = ['utf-8', 'utf-8-sig', 'utf-16', 'utf-16-le']
    
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

# Initialize Jarvis components on startup
ensure_initialization()

# Your user ID for DMs (replace with your actual Discord user ID)
USER_ID = None  # Will be set when the bot identifies you through DMs

# Speaker mapping for Discord users (Discord name -> Voice mode speaker name)
SPEAKER_MAPPING = {
    "wex": "Jason",  # Your Discord username maps to Jason
    "abbey": "Schmoo",  # If Abbey uses Discord, her messages would be tagged as Schmoo
    "schmoo": "Schmoo",  # Alternative mapping
    # Add more mappings as needed
}

def format_weather_info():
    """Get and format comprehensive weather information."""
    print("[Briefing] 🌤️ Getting comprehensive weather information...")
    try:
        weather_report = get_comprehensive_weather("Philadelphia")
        print(f"[Briefing] Weather report received: {weather_report[:100] if weather_report else 'None'}...")
        # Format for morning briefing
        if weather_report:
            return f"🌤️ Philadelphia: {weather_report}"
        else:
            return "🌤️ Philadelphia: Weather information unavailable"
    except Exception as e:
        print(f"[Briefing] Error getting weather: {e}")
        return "🌤️ Philadelphia: Weather information unavailable"

@tasks.loop(time=datetime.time(8, 0))  # 8:00 AM every day
async def daily_morning_briefing():
    """Send the morning briefing at 8 AM every day."""
    global USER_ID
    if USER_ID:
        print("[Scheduled] 🌅 Sending scheduled morning briefing at 8 AM...")
        await send_morning_briefing(USER_ID)
    else:
        print("[Scheduled] ⚠️ No user ID found for scheduled briefing")

@daily_morning_briefing.before_loop
async def before_daily_briefing():
    """Wait until the bot is ready before starting the scheduled task."""
    await client.wait_until_ready()
    print("[Scheduled] 📅 Daily briefing task started - will send at 8 AM every day")

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
        tech_data = get_tech_headlines_data(2)  # Reduced from 3 to 2
        
        # Get AI headlines using discover_headlines.py
        print("[Briefing] Step 3/6: Getting AI headlines...")
        ai_data = get_ai_headlines_data(1)  # Reduced from 2 to 1
        
        # Get sports updates using discover_headlines.py
        print("[Briefing] Step 4/6: Getting sports updates...")
        jets_data = get_jets_news_data(1)
        phillies_data = get_phillies_news_data(1)
        sixers_data = get_sixers_news_data(1)
        
        # Get general sports updates
        print("[Briefing] Step 5/7: Getting general sports...")
        nfl_data = get_general_sports_data("nfl", 1)
        mlb_data = get_general_sports_data("mlb", 1) 
        nba_data = get_general_sports_data("nba", 1)
        golf_data = get_general_sports_data("golf", 1)
        liverpool_data = get_general_sports_data("liverpool", 1)
        
        # Get bullet point league news
        print("[Briefing] Step 6/7: Getting league bullet news...")
        nfl_bullets = get_league_bullet_news("nfl", 3)
        mlb_bullets = get_league_bullet_news("mlb", 3)
        nba_bullets = get_league_bullet_news("nba", 3)
        golf_bullets = get_league_bullet_news("golf", 1)
        
        # Generate motivational quote
        print("[Briefing] Step 7/7: Generating motivational quote...")
        motivational_quote = generate_motivational_quote()
        
        print("[Briefing] 📝 Formatting message...")
        
        # Start building the message
        message = "☀️ **Good morning, Jason!**\n\n"
        
        # Weather first
        message += f"{weather_info}\n\n"
        
        # Tech & AI Headlines
        message += "📰 **AI Headlines:**\n"  # Changed from Tech & AI to just AI
        all_tech_ai = ai_data  # Remove tech_data, only use ai_data
        if all_tech_ai:
            for title, summary, url in all_tech_ai:
                clean_title = title.replace('*', '').replace('_', '').strip()
                # Allow longer titles - don't cut off unless really long
                if len(clean_title) > 100:  # Increased from 50 to 100
                    clean_title = clean_title[:97] + "..."
                # Show full summary without truncation
                message += f"• **{clean_title}**\n"
                message += f"  {summary} [Read more]({url})\n\n"
        else:
            message += "No recent AI news available.\n\n"
        
        # Sports Updates - Favorite Teams
        message += "🏈 **Your Teams:**\n"
        
        # Jets
        if jets_data:
            title, summary, url = jets_data[0]
            clean_title = title.replace('*', '').replace('_', '').strip()
            if len(clean_title) > 60:  # Shortened from 80 to 60
                clean_title = clean_title[:57] + "..."
            message += f"**🏈 Jets:** {clean_title}\n"
            message += f"  {summary} [More]({url})\n\n"
        
        # Phillies - Only show if data exists, skip entirely if no data
        if phillies_data:
            title, summary, url = phillies_data[0]
            clean_title = title.replace('*', '').replace('_', '').strip()
            if len(clean_title) > 60:  # Shortened from 80 to 60
                clean_title = clean_title[:57] + "..."
            message += f"**⚾ Phillies:** {clean_title}\n"
            message += f"  {summary} [More]({url})\n\n"
        
        # Sixers
        if sixers_data:
            title, summary, url = sixers_data[0]
            clean_title = title.replace('*', '').replace('_', '').strip()
            if len(clean_title) > 60:  # Shortened from 80 to 60
                clean_title = clean_title[:57] + "..."
            message += f"**🏀 Sixers:** {clean_title}\n"
            message += f"  {summary} [More]({url})\n\n"
        
        # General Sports - Only show if there's space
        if len(message) < 1000:  # Reduced from 1200 to 1000 to stay under Discord limits
            message += "🏆 **Around the Leagues:**\n"
            
            # Add stories from each league with proper categorization
            sports_categories = [
                (nfl_data, "🏈", "NFL"),
                (mlb_data, "⚾", "MLB"), 
                (nba_data, "🏀", "NBA"),
                (golf_data, "⛳", "Golf"),
                (liverpool_data, "⚽", "Liverpool FC")
            ]
            
            for league_data, emoji, name in sports_categories:
                if league_data and len(message) < 1400:  # Reduced from 1600 to 1400
                    title, summary, url = league_data[0]
                    clean_title = title.replace('*', '').replace('_', '').strip()
                    if len(clean_title) > 50:  # Reduced from 80 to 50
                        clean_title = clean_title[:47] + "..."
                    message += f"**{emoji} {name}:** {clean_title}\n"
                    message += f"  {summary} [More]({url})\n\n"
        
        # League Headlines - Brief bullet points
        print(f"[Briefing] Message length before league headlines: {len(message)}")
        if len(message) < 1800:  # Increased from 1200 to 1800 to ensure it shows
            message += "📈 **League Headlines:**\n"
            
            # NFL bullets
            if nfl_bullets:
                print(f"[Briefing] Adding {len(nfl_bullets)} NFL bullets")
                message += "🏈 **NFL:**\n"
                for title, summary, url in nfl_bullets:
                    message += f"  • {summary}\n"
                message += "\n"
            else:
                print("[Briefing] No NFL bullets found")
            
            # MLB bullets
            if mlb_bullets:
                print(f"[Briefing] Adding {len(mlb_bullets)} MLB bullets")
                message += "⚾ **MLB:**\n"
                for title, summary, url in mlb_bullets:
                    message += f"  • {summary}\n"
                message += "\n"
            else:
                print("[Briefing] No MLB bullets found")
            
            # NBA bullets
            if nba_bullets:
                print(f"[Briefing] Adding {len(nba_bullets)} NBA bullets")
                message += "🏀 **NBA:**\n"
                for title, summary, url in nba_bullets:
                    message += f"  • {summary}\n"
                message += "\n"
            else:
                print("[Briefing] No NBA bullets found")
            
            # Golf bullets
            if golf_bullets:
                print(f"[Briefing] Adding {len(golf_bullets)} Golf bullets")
                message += "⛳ **Golf:**\n"
                for title, summary, url in golf_bullets:
                    message += f"  • {summary}\n"
                message += "\n"
            else:
                print("[Briefing] No Golf bullets found")
        else:
            print(f"[Briefing] Skipping league headlines - message too long: {len(message)}")
        
        print(f"[Briefing] Final message length: {len(message)}")
        
        # Motivational quote at the end
        message += "💡 **Motivational Quote:**\n"
        message += f"*\"{motivational_quote}\"*\n\n"
        
        message += "Have a fantastic day! 🚀"
        
        # Check final message length and truncate if needed
        if len(message) > 1900:  # Leave some buffer
            message = message[:1850] + "...\n\nHave a fantastic day! 🚀"
        
        print(f"[Briefing] 📤 Sending briefing message (length: {len(message)} chars)...")
        
        # Send the DM
        await user.send(message)
        print(f"[Briefing] ✅ Morning briefing sent to {user.display_name}")
        
    except Exception as e:
        print(f"[Briefing] ❌ Error sending morning briefing: {e}")
        import traceback
        traceback.print_exc()

@client.event
async def on_ready():
    global USER_ID
    print(f"🍀 Logged in as {client.user}")
    
    # Try to load USER_ID from a config file if it exists
    try:
        with open("user_config.json", "r") as f:
            config = json.load(f)
            USER_ID = config.get("user_id")
            print(f"[Config] Loaded user ID: {USER_ID}")
    except FileNotFoundError:
        print("[Config] No user_config.json found, will detect user from first DM")
    
    # Start the daily briefing task
    if not daily_morning_briefing.is_running():
        daily_morning_briefing.start()
        print("[Scheduled] 📅 Started daily 8 AM briefing task")

@client.event
async def on_message(message):
    global USER_ID
    
    # ignore other bots (including yourself)
    if message.author.bot:
        return

    # Handle both DMs and server messages (when bot is mentioned or in allowed channels)
    process_message = False
    
    if isinstance(message.channel, discord.DMChannel):
        # Always process DMs
        process_message = True
        
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
    else:
        # For server messages, only respond when mentioned or if message starts with "jarvis"
        if client.user.mentioned_in(message) or message.content.lower().startswith('jarvis'):
            process_message = True
            # Remove the mention or "jarvis" prefix from the message
            user_input = message.content
            if client.user.mentioned_in(message):
                user_input = message.content.replace(f'<@{client.user.id}>', '').strip()
            elif message.content.lower().startswith('jarvis'):
                user_input = message.content[6:].strip()  # Remove "jarvis" prefix
            message.content = user_input  # Update message content for processing
    
    if not process_message:
        return
    
    user_input = message.content.strip()
    
    # Check for manual briefing request (only in DMs)
    if isinstance(message.channel, discord.DMChannel) and user_input.lower() in ["briefing", "morning briefing", "daily briefing", "!briefing"]:
        print("[Command] Manual briefing requested")
        await send_morning_briefing(message.author.id)
        return
    
    # Determine speaker for Discord - map Discord users to voice mode speaker names
    speaker = "Unknown"
    discord_username = message.author.name.lower()  # Get lowercase username
    
    if message.author.id == USER_ID:
        speaker = "Jason"  # Primary user is always Jason
    elif discord_username in SPEAKER_MAPPING:
        speaker = SPEAKER_MAPPING[discord_username]
        print(f"[Discord] Mapped Discord user '{message.author.name}' to speaker '{speaker}'")
    else:
        # For unmapped users, use their display name but capitalize it properly
        speaker = (message.author.display_name or message.author.name).title()
    
    print(f"[Discord] Processing message from speaker: {speaker}")
    
    # Get persistent conversation history for this channel
    conversation_history = get_channel_conversation(message.channel.id)
    
    # Use process_command directly with persistent conversation history
    reply, should_exit = process_command(user_input, conversation_history, text_mode=True, speaker=speaker)
    
    # Prune conversation history to keep it manageable
    prune_channel_conversation(message.channel.id, max_messages=10)
    
    # Send the reply back
    await message.channel.send(reply)
    # Store the conversation in memory for persistence with speaker info
    auto_remember_sync(user_input, reply, speaker)
    print(f"[Discord] Stored memory for {speaker}: {user_input[:30]}... -> {reply[:30]}...")

# Gracefully rebuild memory index on shutdown
@client.event
async def on_close():
    schedule_index_rebuild()

if __name__ == "__main__":
    client.run(TOKEN)
