from deep_translator import GoogleTranslator

def translate_to_uz(text: str) -> str:
    """
    Translate `text` into Uzbek (uz) using deep-translator's GoogleTranslator.
    If translation fails, return the original text.
    """
    if not text:
        return ''
    try:
        translated = GoogleTranslator(source='auto', target='uz').translate(text)
        # Keep it reasonably short
        if len(translated) > 1000:
            return translated[:1000] + '...'
        return translated
    except Exception:
        return text
