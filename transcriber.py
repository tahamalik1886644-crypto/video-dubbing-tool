import os
import whisper

def transcribe_audio(audio_path: str, model_size: str = "tiny"):
    # Load model with download verification bypass if cache is corrupted
    try:
        model = whisper.load_model(model_size)
    except RuntimeError:
        # Clear corrupted file automatically if checksum fails
        cache_dir = os.path.expanduser(f"~/.cache/whisper/{model_size}.pt")
        if os.path.exists(cache_dir):
            os.remove(cache_dir)
        model = whisper.load_model(model_size)

    result = model.transcribe(audio_path)
    return result.get("segments", [])