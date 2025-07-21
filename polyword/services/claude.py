import os
import anthropic

api_key = ""

client = anthropic.Anthropic(api_key=api_key or os.getenv('ANTHROPIC_API_KEY'))

class ClaudeService:
    DEFAULT_SYSTEM_PROMPT = """I want you to edit the following text while following the rules below:
    - In your response, you should only return the edited text, no other text or comments.
    - Keep as much of the original content as possible
    - Keep the original meaning and intent of the text
    - Make sure the text is grammatically correct
    """

    def __init__(self, api_key: str = None, model: str = 'claude-3-7-sonnet-latest'):
        self.model = model

    def refine_text(self, text: str, system_prompt: str = DEFAULT_SYSTEM_PROMPT) -> str:
        """
        Sends the translated text to Claude for refinement.
        """
        if not text:
            return ''
        
        response = client.messages.create(
            model=self.model,
            max_tokens=32000,
            system=system_prompt,
            messages=[
                {
                    "role": "user", 
                    "content": text
                }
            ]
        )
        
        return response.content[0].text.strip()

    def split_paragraphs_20k(self, text):
        """Process up to 20,000 words in a single call"""
        
        PROMPT = """CRITICAL INSTRUCTIONS - READ CAREFULLY:

You are a text formatter with ONE TASK ONLY: Insert paragraph breaks (double newlines) where topics change.

ABSOLUTE REQUIREMENTS:
- DO NOT truncate or cut off the text - return the COMPLETE formatted text
- EVERY single word from the original must appear in the output
- DO NOT change, edit, improve, or rewrite ANY words
- DO NOT rephrase ANYTHING for clarity or readability
- DO NOT remove or condense technical terms, proper nouns, or repeated words
- DO NOT summarize or shorten any content
- DO NOT fix grammar, spelling, or awkward phrasing 
- DO NOT remove repetitive content or technical jargon
- Keep ALL instances of words not usually used in English like "HIIHIQ", "Genotype", "Intellectual", etc.
- Keep ALL original errors, awkward translations, and poor grammar EXACTLY as written


YOUR ONLY ACTIONS:
1. Read the text to identify where topics change
2. Insert double newlines to create paragraph breaks at topic changes

OUTPUT REQUIREMENT: Return the exact original text with ONLY paragraph breaks added. Every single word must be preserved. No explanations, no comments, no improvements, no truncation notices, no content removal."""


        response = client.messages.create(
            model=self.model,
            max_tokens=32000,  # Claude can handle larger outputs
            temperature=0.0,
            system=PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": f"Text to format:\n\n{text}"
                }
            ]
        )
        
        return response.content[0].text.strip()
    
    def stream_split_paragraphs_20k(self, text):

        PROMPT = """CRITICAL INSTRUCTIONS - READ CAREFULLY:

    You are a text formatter with ONE TASK ONLY: Insert paragraph breaks (double newlines) where topics change.

    ABSOLUTE REQUIREMENTS:
    - DO NOT change, edit, improve, or rewrite ANY words
    - DO NOT fix grammar, spelling, or awkward phrasing 
    - DO NOT make text "flow better" or "sound smoother"
    - DO NOT add, remove, or substitute ANY words
    - DO NOT rephrase ANYTHING for clarity or readability
    - DO NOT correct punctuation except adding obvious missing periods at sentence ends
    - Keep ALL original errors, awkward translations, and poor grammar EXACTLY as written

    YOUR ONLY ACTIONS:
    1. Read the text to identify where topics change
    2. Insert double newlines to create paragraph breaks at topic changes
    3. Add periods ONLY where sentences clearly end without punctuation

    FORBIDDEN ACTIONS:
    - Changing any word order
    - Replacing words with synonyms
    - Combining or splitting sentences
    - Adding connecting words like "however," "therefore," etc.
    - Smoothing transitions between ideas
    - Making any stylistic improvements

    OUTPUT REQUIREMENT: Return the exact original text with ONLY paragraph breaks added. No explanations, no comments, no improvements."""

        output = ""

        with client.messages.stream(
            model=self.model,
            max_tokens=32000,
            temperature=0.0,
            system=PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": f"Text to format:\n\n{text}"
                }
            ]
        ) as stream:
            for text_chunk in stream.text_stream:
                output += text_chunk

        return output.strip()