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

from streamlit_webrtc import webrtc_streamer, WebRtcMode, ClientSettings

# Page config
st.set_page_config("🤖 Jarvis", layout="wide")
load_dotenv()
load_api_key()
load_memory_cache()

# Sidebar configuration
st.sidebar.title("🎛️ Controls")
mode = st.sidebar.radio("Mode", ["Text", "Voice"])

# Speaker selection for text mode
speaker_name = st.sidebar.text_input("Speaker Name (for text mode)", value="Jason", help="Who is using JARVIS?")

if st.sidebar.button("Clear Chat"):
    st.session_state.history = []
    st.rerun()

# Display speaker info
if has_speaker_memories(speaker_name):
    st.sidebar.success(f"✅ I remember {speaker_name}")
else:
    st.sidebar.info(f"👋 Nice to meet you, {speaker_name}!")

if "history" not in st.session_state:
    st.session_state.history = []

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
    user_input = st.text_input("You:", key="txt_input", placeholder="Ask JARVIS anything...")
    
    if user_input:
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
        
        # Display the new messages
        message(f"{speaker_name}: {user_input}", is_user=True, key=f"msg_new_user")
        message(f"JARVIS: {reply}", is_user=False, key=f"msg_new_jarvis")
        
        # Clear input and rerun to update chat
        st.rerun()

else:
    st.write("🎤 Click “Start” and speak; click again to stop.")
    client_settings = ClientSettings(
        media_stream_constraints={"audio": True, "video": False},
        rtc_configuration={"iceServers":[{"urls":["stun:stun.l.google.com:19302"]}]}
    )

    def recv_audio(frames):
        # collect frames into a WAV, process when user stops
        wav_bytes = b"".join([f.to_ndarray().tobytes() for f in frames])
        with open("tmp.wav", "wb") as f:
            f.write(wav_bytes)
        return frames

    ctx = webrtc_streamer(
        key="jarvis-voice",
        mode=WebRtcMode.SENDRECV,
        client_settings=client_settings,
        audio_receiver_size=1024,
        sendback_audio=False,
        video_processor_factory=None,
        audio_processor_factory=lambda: None
    )

    if ctx.audio_receiver and ctx.state.playing:
        frames = ctx.audio_receiver.get_frames(timeout=1)
        if frames:
            # Once you have some audio, save & process:
            import soundfile as sf
            arr = frames[0].to_ndarray().flatten().astype("float32")
            sf.write("tmp.wav", arr, samplerate=ctx.client_settings.media_stream_constraints["audio"]["sampleRate"])
            speaker = identify_speaker("tmp.wav")
            st.info(f"Detected speaker: {speaker}")
            transcription = transcribe_audio("tmp.wav")
            
            # Add user message to history with speaker info
            st.session_state.history.append({
                "role": "user",
                "text": transcription,
                "speaker": speaker
            })
            
            message(f"{speaker}: {transcription}", is_user=True)
            
            # Get JARVIS response using ask_jarvis
            reply = ask_jarvis(transcription, text_mode=True, speaker=speaker)
            
            # Add JARVIS response to history
            st.session_state.history.append({
                "role": "assistant",
                "text": reply,
                "speaker": "JARVIS"
            })
            
            message(f"JARVIS: {reply}")
            speak(reply)
