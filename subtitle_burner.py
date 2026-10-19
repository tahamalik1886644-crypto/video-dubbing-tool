import os
import subprocess

def format_timestamp(seconds):
    millis = int((seconds % 1) * 1000)
    seconds = int(seconds)
    mins = seconds // 60
    hours = mins // 60
    mins = mins % 60
    secs = seconds % 60
    return f"{hours:02d}:{mins:02d}:{secs:02d},{millis:03d}"

def generate_srt(segments, srt_path, lang="ur"):
    valid_segments = []
    for seg in segments:
        text = str(seg.get("text", "")).strip() if isinstance(seg, dict) else str(seg).strip()
        if text:
            valid_segments.append(seg)

    if not valid_segments:
        raise ValueError("No valid subtitle text was generated. The uploaded video may not contain clear speech.")

    with open(srt_path, "w", encoding="utf-8") as f:
        for idx, seg in enumerate(valid_segments, start=1):
            start_str = format_timestamp(seg["start"])
            end_str = format_timestamp(seg["end"])
            text = str(seg["text"]).strip()

            f.write(f"{idx}\n")
            f.write(f"{start_str} --> {end_str}\n")
            f.write(f"{text}\n\n")

def burn_subtitles(video_path, srt_path, output_path):
    # Standardize path for Windows FFmpeg compatibility
    clean_srt_path = srt_path.replace("\\", "/").replace(":", "\\:")
    
    # Use Arial / Noto / Segoe UI for clean joined RTL rendering
    command = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-vf", f"subtitles='{clean_srt_path}':force_style='FontName=Arial,FontSize=20,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BorderStyle=1,Outline=2'",
        "-c:a", "copy",
        output_path
    ]
    
    subprocess.run(command, check=True)