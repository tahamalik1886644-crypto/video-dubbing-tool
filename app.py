import sys
import os
import subprocess

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
from modules.audio_extractor import extract_audio
from modules.transcriber import transcribe_audio
from modules.translator import translate_segments
from modules.subtitle_burner import generate_srt, burn_subtitles
from modules.dubber import create_dubbed_audio, merge_dubbed_audio

# 1. Page Configuration
st.set_page_config(
    page_title="SubDub AI Studio | Video Subtitling & Dubbing Platform",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Modern SaaS UI CSS Styling
custom_css = """
<style>
    .stApp {
        background-color: #0b0f19;
        color: #f3f4f6;
        font-family: 'Inter', system-ui, -apple-system, sans-serif;
    }
    .top-nav {
        background: rgba(17, 24, 39, 0.8);
        border-bottom: 1px solid #1f2937;
        padding: 15px 30px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-radius: 12px;
        margin-bottom: 25px;
    }
    .brand-logo {
        font-size: 1.6rem;
        font-weight: 800;
        background: linear-gradient(90deg, #6366f1, #a855f7);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .hero-box {
        background: linear-gradient(135deg, rgba(99,102,241,0.12) 0%, rgba(168,85,247,0.12) 100%);
        border: 1px solid rgba(99,102,241,0.3);
        border-radius: 20px;
        padding: 35px;
        text-align: center;
        margin-bottom: 25px;
    }
    .hero-title {
        font-size: 2.5rem;
        font-weight: 800;
        color: #ffffff;
        margin-bottom: 10px;
    }
    .hero-desc {
        color: #9ca3af;
        font-size: 1.1rem;
        max-width: 700px;
        margin: 0 auto;
    }
    section[data-testid="stFileUploader"] {
        background: #111827;
        border: 2px dashed #374151;
        border-radius: 16px;
        padding: 20px;
    }
    section[data-testid="stFileUploader"]:hover {
        border-color: #6366f1;
    }
    div.stButton > button {
        width: 100%;
        background: linear-gradient(90deg, #6366f1 0%, #8b5cf6 100%);
        color: #ffffff;
        font-size: 1.1rem;
        font-weight: 700;
        padding: 14px 28px;
        border-radius: 12px;
        border: none;
        box-shadow: 0 4px 20px rgba(99, 102, 241, 0.35);
        transition: all 0.2s ease;
    }
    div.stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 25px rgba(168, 85, 247, 0.5);
    }
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# 3. Directories Setup
TEMP_DIR = "temp"
OUTPUT_DIR = "outputs"
os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 4. Helper Function: Blur/cover the bottom subtitle strip using a stable FFmpeg filter
# delogo is unreliable in this FFmpeg build, so we use drawbox to cover the lower subtitle area.
def remove_existing_subtitles(input_video_path, output_video_path):
    filter_cmd = "drawbox=x=0:y=ih*4/5:w=iw:h=ih/5:color=black@1:t=fill"
    command = [
        "ffmpeg", "-y",
        "-i", input_video_path,
        "-vf", filter_cmd,
        "-c:a", "copy",
        output_video_path
    ]
    subprocess.run(command, check=True)

# 5. Header Navbar
st.markdown("""
<div class="top-nav">
    <div class="brand-logo">⚡ SubDub AI Studio</div>
    <div style="color: #9ca3af; font-size: 0.95rem;">Final Year Project | AI Video Platform</div>
</div>
""", unsafe_allow_html=True)

# 6. Main Navigation Tabs
tabs = st.tabs(["🏠 Dashboard & Processing", "📊 System Metrics", "👨‍💻 Project Info"])

with tabs[0]:
    st.markdown("""
    <div class="hero-box">
        <div class="hero-title">AI Video Subtitling & Dubbing Platform</div>
        <div class="hero-desc">Automated speech recognition, multilingual translation, subtitle removal, and AI voice dubbing engine.</div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([1.1, 1])

    with col1:
        st.subheader("1. Source Video Upload")
        uploaded_video = st.file_uploader("Select video file (MP4, MKV, AVI, MOV)", type=["mp4", "mkv", "avi", "mov"])
        
        remove_subtitles_flag = st.checkbox("Blur pre-existing subtitles from bottom of video", value=False)

    with col2:
        st.subheader("2. Workflow Options")
        
        task_option = st.radio(
            "Select Processing Task Mode:",
            [
                "1️⃣ Subtitles Only (Original Voice + Translated Subtitles)",
                "2️⃣ Voice Dubbing Only (AI Voice Replace + No Subtitles)",
                "3️⃣ Full Hybrid (AI Voice Replace + Translated Subtitles)"
            ]
        )

        target_lang = st.selectbox(
            "Target Output Language",
            options=["en", "ur", "ar", "es", "fr", "de", "hi"],
            format_func=lambda x: {
                "en": "🇬🇧 English",
                "ur": "🇵🇰 Urdu",
                "ar": "🇸🇦 Arabic",
                "es": "🇪🇸 Spanish",
                "fr": "🇫🇷 French",
                "de": "🇩🇪 German",
                "hi": "🇮🇳 Hindi"
            }.get(x, x)
        )

        model_size = st.selectbox("Whisper AI Model Engine", ["tiny", "base", "small", "medium"], index=1)

    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("🚀 Run AI Pipeline Engine"):
        if uploaded_video is not None:
            raw_video_path = os.path.join(TEMP_DIR, uploaded_video.name)
            video_path = os.path.join(TEMP_DIR, f"cleaned_{uploaded_video.name}") if remove_subtitles_flag else raw_video_path
            audio_path = os.path.join(TEMP_DIR, "extracted_audio.wav")
            srt_path = os.path.join(TEMP_DIR, "subtitles.srt")
            dubbed_audio_path = os.path.join(TEMP_DIR, "dubbed_audio.mp3")
            output_video_path = os.path.join(OUTPUT_DIR, f"final_{uploaded_video.name}")

            with open(raw_video_path, "wb") as f:
                f.write(uploaded_video.getbuffer())

            try:
                status = st.status("⚡ Executing AI Pipeline...", expanded=True)

                if remove_subtitles_flag:
                    status.write("🧼 [Preprocessing] Blurring pre-existing video subtitles...")
                    remove_existing_subtitles(raw_video_path, video_path)

                status.write("⚡ [Stage 1/4] Extracting raw audio stream via FFmpeg...")
                extract_audio(video_path, audio_path)

                status.write(f"🧠 [Stage 2/4] Running OpenAI Whisper ({model_size} model)...")
                segments = transcribe_audio(audio_path, model_size=model_size)

                status.write(f"🌍 [Stage 3/4] Translating speech into selected target language...")
                translated_segments = translate_segments(segments, target_lang=target_lang)

                if not translated_segments or not any(str(seg.get("text", "")).strip() for seg in translated_segments if isinstance(seg, dict)):
                    status.update(label="⚠️ No speech detected in the uploaded video", state="complete", expanded=False)
                    st.warning("No valid speech was detected, so there is no subtitle or dub content to generate.")
                    st.stop()

                if "1️⃣" in task_option:
                    status.write("🔥 [Stage 4/4] Hardcoding translated subtitles onto video...")
                    generate_srt(translated_segments, srt_path, lang=target_lang)
                    burn_subtitles(video_path, srt_path, output_video_path)

                elif "2️⃣" in task_option:
                    status.write("🎙️ [Stage 4/4] Generating AI Voice Dubbing & replacing audio...")
                    create_dubbed_audio(translated_segments, target_lang, dubbed_audio_path)
                    merge_dubbed_audio(video_path, dubbed_audio_path, output_video_path)

                elif "3️⃣" in task_option:
                    status.write("🚀 [Stage 4/4] Merging AI Voice Dubbing & burning subtitles...")
                    create_dubbed_audio(translated_segments, target_lang, dubbed_audio_path)
                    generate_srt(translated_segments, srt_path, lang=target_lang)

                    temp_dubbed = os.path.join(TEMP_DIR, "temp_dubbed.mp4")
                    merge_dubbed_audio(video_path, dubbed_audio_path, temp_dubbed)
                    burn_subtitles(temp_dubbed, srt_path, output_video_path)

                status.update(label="✅ Video Processing Finished!", state="complete", expanded=False)

                st.balloons()
                st.success("🎉 Video process successfully complete!")

                st.markdown("### 📹 Final Video Result")
                st.video(output_video_path)

            except Exception as e:
                st.error(f"❌ Processing Failed: {str(e)}")
        else:
            st.warning("⚠️ Pehle input video file select karke upload karein.")

with tabs[1]:
    st.subheader("📊 System Pipeline & Analytics")
    m1, m2, m3 = st.columns(3)
    m1.metric("Supported Languages", "7+", "+Global TTS")
    m2.metric("ASR Engine", "OpenAI Whisper", "Audio Demuxing")
    m3.metric("Subtitle Filter", "FFmpeg Delogo", "Auto Blur")

with tabs[2]:
    st.subheader("👨‍💻 Project Information")
    st.info("SubDub AI Studio: Automatic Subtitle Removal, Transcription, Translation, and Voice Dubbing Framework.") 