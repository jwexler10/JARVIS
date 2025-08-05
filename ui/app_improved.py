import streamlit as st
from streamlit_chat import message
from dotenv import load_dotenv
import sys
import os

# Add the parent directory to path to import jarvis modules
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

# Change working directory to parent so config files can be found
os.chdir(parent_dir)

from jarvis import ask_jarvis  # Use the main jarvis function
from transcribe import load_api_key, transcribe_audio
from speaker_id import identify_speaker
from memory import load_memory_cache, auto_remember_async, has_speaker_memories
from tts import speak

# Page config
st.set_page_config("🤖 JARVIS", layout="wide", page_icon="🤖")

# Load environment variables with encoding handling (like in discord_bot.py)
try:
    encodings_to_try = ['utf-16', 'utf-16-le', 'utf-8-sig', 'utf-8']
    
    for encoding in encodings_to_try:
        try:
            with open('.env', 'r', encoding=encoding) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key.strip()] = value.strip()
                break
        except (UnicodeDecodeError, FileNotFoundError):
            continue
    else:
        st.warning("⚠️ Could not read .env file with any encoding")
        
except Exception as e:
    st.warning(f"⚠️ Error loading .env: {e}")

# Load API keys and memory with error handling
try:
    load_api_key()
    st.success("✅ API keys loaded")
except Exception as e:
    st.error(f"❌ Error loading API keys: {e}")

try:
    load_memory_cache()
    st.success("✅ Memory cache loaded")
except Exception as e:
    st.error(f"❌ Error loading memory cache: {e}")

# Sidebar configuration
st.sidebar.title("🎛️ Controls")
mode = st.sidebar.radio("Mode", ["Text", "Voice"])

# Speaker selection for text mode
speaker_name = st.sidebar.text_input("Speaker Name", value="Jason", help="Who is using JARVIS?")

if st.sidebar.button("Clear Chat"):
    st.session_state.history = []
    st.rerun()

# Display speaker info
try:
    if has_speaker_memories(speaker_name):
        st.sidebar.success(f"✅ I remember {speaker_name}")
    else:
        st.sidebar.info(f"👋 Nice to meet you, {speaker_name}!")
except Exception as e:
    st.sidebar.warning(f"⚠️ Memory check failed: {e}")

# Initialize session state
if "history" not in st.session_state:
    st.session_state.history = []

# Main interface
st.title("🤖 JARVIS AI Assistant")
st.markdown(f"**Current Speaker:** {speaker_name}")

# Render chat history
if st.session_state.history:
    for i, turn in enumerate(st.session_state.history):
        if turn["role"] == "user":
            message(f"{turn['speaker']}: {turn['text']}", is_user=True, key=f"msg_{i}")
        else:
            message(f"JARVIS: {turn['text']}", is_user=False, key=f"msg_{i}")

if mode == "Text":
    st.subheader("💬 Text Mode")
    
    # Text input
    with st.form("text_input_form", clear_on_submit=True):
        user_input = st.text_input("You:", placeholder="Ask JARVIS anything...")
        submitted = st.form_submit_button("Send")
    
    if submitted and user_input:
        # Add user message to history
        st.session_state.history.append({
            "role": "user", 
            "text": user_input,
            "speaker": speaker_name
        })
        
        # Get JARVIS response using the main ask_jarvis function
        with st.spinner("🤖 JARVIS is thinking..."):
            reply = ask_jarvis(user_input, text_mode=True, speaker=speaker_name)
        
        # Add JARVIS response to history
        st.session_state.history.append({
            "role": "assistant", 
            "text": reply,
            "speaker": "JARVIS"
        })
        
        # Rerun to update chat display
        st.rerun()

else:
    st.subheader("🎤 Voice Mode")
    st.warning("⚠️ Voice mode is simplified in this web interface")
    st.info("💡 For full voice functionality with wake word detection, use the main `jarvis.py` script")
    
    # Audio file upload option
    st.markdown("### Upload Audio File")
    uploaded_file = st.file_uploader("Choose an audio file", type=['wav', 'mp3', 'flac'])
    
    if uploaded_file is not None:
        # Save uploaded file
        with open("temp_audio.wav", "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        if st.button("🎤 Process Audio"):
            with st.spinner("🔍 Processing audio..."):
                # Identify speaker
                try:
                    detected_speaker = identify_speaker("temp_audio.wav")
                    st.success(f"🔊 Detected speaker: {detected_speaker}")
                except Exception as e:
                    st.error(f"Speaker identification failed: {e}")
                    detected_speaker = "Unknown"
                
                # Transcribe audio
                try:
                    transcription = transcribe_audio("temp_audio.wav")
                    st.info(f"📝 Transcription: {transcription}")
                    
                    if transcription.strip():
                        # Add user message to history
                        st.session_state.history.append({
                            "role": "user", 
                            "text": transcription,
                            "speaker": detected_speaker
                        })
                        
                        # Get JARVIS response
                        reply = ask_jarvis(transcription, text_mode=True, speaker=detected_speaker)
                        
                        # Add JARVIS response to history
                        st.session_state.history.append({
                            "role": "assistant", 
                            "text": reply,
                            "speaker": "JARVIS"
                        })
                        
                        st.success("✅ Audio processed successfully!")
                        st.rerun()
                    else:
                        st.warning("No speech detected in audio file")
                        
                except Exception as e:
                    st.error(f"Transcription failed: {e}")
        
        # Clean up temp file
        if os.path.exists("temp_audio.wav"):
            try:
                os.remove("temp_audio.wav")
            except:
                pass

# Footer
st.markdown("---")
st.markdown("""
**Features:**
- 🗣️ Speaker-aware conversations
- 🧠 Cross-session memory
- 🎯 Personalized responses
- 🔄 Real-time chat interface

**💡 Pro Tip:** Use `python jarvis.py` for full voice functionality with wake word detection!
""")

# Debug info in sidebar
if st.sidebar.checkbox("Show Debug Info"):
    st.sidebar.markdown("### Debug Info")
    st.sidebar.write(f"Session history length: {len(st.session_state.history)}")
    st.sidebar.write(f"Current speaker: {speaker_name}")
    try:
        st.sidebar.write(f"Has memories: {has_speaker_memories(speaker_name)}")
    except Exception as e:
        st.sidebar.write(f"Memory check error: {e}")
