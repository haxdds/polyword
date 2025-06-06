from google.cloud import translate_v2 as translate

class TranslationService:
    def __init__(self, translate_client=None):
        self.client = translate_client or translate.Client()

    def translate_text(self, text: str, target_language: str) -> str:
        """
        Translates input text into the target language.
        """
        if not text:
            return ''
        result = self.client.translate(text, target_language=target_language)
        return result['translatedText']
