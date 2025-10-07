import streamlit as st
import speech_recognition as sr
from pydub import AudioSegment
from moviepy.editor import VideoFileClip
import tempfile
import os
import shutil

# ---------- Streamlit Page Setup ----------
st.set_page_config(page_title="🎙️ Audio/Video to Text", layout="centered")
st.title("🎙️ Audio/Video to Text")

uploaded_file = st.file_uploader(
    "Upload audio/video file",
    type=["wav", "mp3", "m4a", "mp4", "mov", "mkv"]
)

if uploaded_file:
    # Preview file
    if uploaded_file.type.startswith("video"):
        st.video(uploaded_file)
    else:
        st.audio(uploaded_file)

    # Save uploaded file to temporary location
    temp_path = None
    audio_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp:
            tmp.write(uploaded_file.read())
            temp_path = tmp.name

        # Extract or convert audio to WAV
        if uploaded_file.type.startswith("video"):
            st.info("🎬 Extracting audio from video...")
            video = VideoFileClip(temp_path)
            audio_path = temp_path.replace(os.path.splitext(temp_path)[1], "_audio.wav")
            video.audio.write_audiofile(
                audio_path,
                fps=16000,
                nbytes=2,
                buffersize=2000,
                codec="pcm_s16le"
            )
            video.close()  # Release the video file
        else:
            st.info("🎧 Processing audio...")
            audio = AudioSegment.from_file(temp_path)
            audio = audio.set_frame_rate(16000).set_channels(1)
            audio_path = temp_path.replace(os.path.splitext(temp_path)[1], "_converted.wav")
            audio.export(audio_path, format="wav")
            audio = None  # Release audio

        # Initialize recognizer
        recognizer = sr.Recognizer()
        with sr.AudioFile(audio_path) as source:
            st.info("🎧 Listening...")
            audio_data = recognizer.record(source)

        # Automatic language detection
        languages = {"English": "en-US", "Hindi": "hi-IN", "Telugu": "te-IN"}
        best_text = ""
        detected_language = ""
        max_words = 0

        for lang_name, lang_code in languages.items():
            try:
                text = recognizer.recognize_google(audio_data, language=lang_code)
                word_count = len(text.split())
                if word_count > max_words:
                    best_text = text
                    detected_language = lang_name
                    max_words = word_count
            except sr.UnknownValueError:
                continue

        if best_text:
            st.success(f"✅ Transcribed Successfully! Detected Language: {detected_language}")
            st.text_area("📝 Transcript", best_text, height=200)
            st.download_button("⬇️ Download Transcript", best_text, file_name="transcript.txt")
        else:
            st.error("😕 Could not understand the audio clearly in any supported language.")

    except sr.RequestError:
        st.error("🌐 Could not connect to Google Speech API. Check your internet connection.")
    except Exception as e:
        st.error(f"❌ Error: {e}")
    finally:
        # Cleanup temporary files safely
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
        if audio_path and os.path.exists(audio_path):
            os.remove(audio_path)
