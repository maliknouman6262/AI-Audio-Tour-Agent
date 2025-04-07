import streamlit as st
import asyncio
from manager import TourManager
from agents import set_default_openai_key
from pathlib import Path
from openai import OpenAI
import tempfile

def tts(text):
    """Generate audio from text using OpenAI's TTS API"""
    # Get API key from session state
    if "OPENAI_API_KEY" not in st.session_state:
        st.error("API key not found in session state")
        return None
        
    client = OpenAI(api_key=st.session_state["OPENAI_API_KEY"])
    
    # Create temp file
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp_file:
        speech_file_path = Path(tmp_file.name)
    
    try:
        response = client.audio.speech.create(
            model="tts-1",
            voice="nova",
            input=text
        )
        response.stream_to_file(speech_file_path)
        return speech_file_path
    except Exception as e:
        st.error(f"Audio generation failed: {str(e)}")
        return None

def run_async(func, *args, **kwargs):
    """Helper to run async functions"""
    try:
        return asyncio.run(func(*args, **kwargs))
    except RuntimeError:
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(func(*args, **kwargs))

# Set page config
st.set_page_config(
    page_title="AI Audio Tour Agent",
    page_icon="🎧",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Sidebar for API key
with st.sidebar:
    st.title("🔑 Settings")
    api_key = st.text_input("OpenAI API Key:", type="password", key="api_key_input")
    if api_key:
        st.session_state["OPENAI_API_KEY"] = api_key
        st.success("API key saved!")
        set_default_openai_key(api_key)

# Main content
st.title("🎧 AI Audio Tour Agent")
st.markdown("""
    <div class='welcome-card'>
        <h3>Welcome to your personalized audio tour guide!</h3>
        <p>I'll help you explore any location with an engaging, natural-sounding tour tailored to your interests.</p>
    </div>
""", unsafe_allow_html=True)

# Create layout
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("### 📍 Where would you like to explore?")
    location = st.text_input("location_input", placeholder="Enter a city, landmark, or location...")
    
    st.markdown("### 🎯 What interests you?")
    interests = st.multiselect(
        "interests_select",
        options=["History", "Architecture", "Culinary", "Culture"],
        default=["History", "Architecture"],
        help="Select the topics you'd like to learn about"
    )

with col2:
    st.markdown("### ⏱️ Tour Settings")
    duration = st.slider(
        "duration_slider",
        min_value=5,
        max_value=60,
        value=10,
        step=5,
        help="Choose how long you'd like your tour to be"
    )
    
    st.markdown("### 🎙️ Voice Settings")
    voice_style = st.selectbox(
        "voice_select",
        options=["Friendly & Casual", "Professional & Detailed", "Enthusiastic & Energetic"],
        help="Select the personality of your tour guide"
    )

# Generate Tour Button
if st.button("🎧 Generate Tour", type="primary", key="generate_button"):
    if "OPENAI_API_KEY" not in st.session_state:
        st.error("Please enter your OpenAI API key in the sidebar.")
    elif not location:
        st.error("Please enter a location.")
    elif not interests:
        st.error("Please select at least one interest.")
    else:
        with st.spinner(f"Creating your personalized tour of {location}..."):
            try:
                mgr = TourManager()
                final_tour = run_async(mgr.run, location, interests, duration)
                
                # Display tour content
                with st.expander("📝 Tour Content", expanded=True):
                    st.markdown(final_tour)
                
                # Generate audio
                with st.spinner("🎙️ Generating audio tour..."):
                    progress_bar = st.progress(0)
                    tour_audio = tts(final_tour)
                    progress_bar.progress(100)
                
                if tour_audio:
                    # Display audio player
                    st.markdown("### 🎧 Listen to Your Tour")
                    st.audio(str(tour_audio), format="audio/mp3")
                    
                    # Download button
                    with open(tour_audio, "rb") as file:
                        st.download_button(
                            label="📥 Download Audio Tour",
                            data=file,
                            file_name=f"{location.lower().replace(' ', '_')}_tour.mp3",
                            mime="audio/mp3"
                        )
            except Exception as e:
                st.error(f"Tour generation failed: {str(e)}")