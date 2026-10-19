import asyncio
import edge_tts
import subprocess
import os

# Voice mappings for supported languages
VOICE_MAPPING = {
    "en": "en-US-ChristopherNeural",
    "ur": "ur-PK-AsadNeural",
    "ar": "ar-SA-HamedNeural",
    "es": "es-ES-AlvaroNeural",
    "fr": "fr-FR-HenriNeural",
    "de": "de-DE-KillianNeural",
    "hi": "hi-IN-MadhurNeural"
}

async def generate_audio_async(text, voice, output_path):
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)

def create_dubbed_audio(translated_segments, target_lang, output_audio_path):
    # Full translated text ko combine karna
    full_text = " ".join([seg.get('text', '') for seg in translated_segments])
    voice = VOICE_MAPPING.get(target_lang, "en-US-ChristopherNeural")
    
    # Async TTS execution
    asyncio.run(generate_audio_async(full_text, voice, output_audio_path))

def merge_dubbed_audio(original_video_path, new_audio_path, output_video_path):
    # FFmpeg command: original video audio remove karke naya audio replace karna
    command = [
        "ffmpeg", "-y",
        "-i", original_video_path,
        "-i", new_audio_path,
        "-c:v", "copy",
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-shortest",
        output_video_path
    ]
    subprocess.run(command, check=True)