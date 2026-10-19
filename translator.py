from googletrans import Translator

def translate_segments(segments, target_lang: str = "ur"):
    lang_map = {
        "en": "en",  # English
        "ur": "ur",  # Urdu
        "ar": "ar",  # Arabic
        "es": "es",  # Spanish
        "fr": "fr",  # French
        "de": "de",  # German
        "hi": "hi"   # Hindi
    }
    
    selected_lang = lang_map.get(target_lang, "en")
    translator = Translator()
    translated_segments = []

    for seg in segments:
        if isinstance(seg, dict):
            original_text = seg.get("text", "").strip()
            start = seg.get("start", 0)
            end = seg.get("end", 0)
        else:
            original_text = str(seg).strip()
            start, end = 0, 0

        translated_text = original_text

        if original_text:
            try:
                res = translator.translate(original_text, dest=selected_lang)
                translated_text = res.text
            except Exception:
                translated_text = original_text

        translated_segments.append({
            "start": start,
            "end": end,
            "text": translated_text
        })

    return translated_segments