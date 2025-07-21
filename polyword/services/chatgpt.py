import os
from openai import OpenAI

api_key = ""

client = OpenAI(api_key=api_key or os.getenv('OPENAI_API_KEY'))

class ChatGPTService:
    DEFAULT_SYSTEM_PROMPT = """I want you to edit the following text while following the rules below:
    - In your response, you should only return the edited text, no other text or comments.
    - Keep as much of the original content as possible
    - Keep the original meaning and intent of the text
    - Make sure the text is grammatically correct
    """

    def __init__(self, api_key: str = None, model: str = 'gpt-4o-mini'):
        self.model = model

    def refine_text(self, text: str, system_prompt: str = DEFAULT_SYSTEM_PROMPT) -> str:
        """
        Sends the translated text to ChatGPT for refinement.
        """
        if not text:
            return ''
        response = client.chat.completions.create(model=self.model,
        messages=[
            # The 'system' role provides high-level instructions and context to the model
            # This helps set the behavior and tone for the entire conversation
            {'role': 'system', 'content': system_prompt},
        
            # The 'user' role contains the actual input text that needs to be processed
            # This is the content that the model will refine based on the system instructions
            {'role': 'user', 'content': text}
        ])
        return response.choices[0].message.content.strip()
    

    def split_paragraphs_20k(self, text):
        """Process up to 20,000 words in a single call"""
        
        # # Estimate tokens (rough: 1 word = 1.3 tokens)
        # estimated_tokens = len(text.split()) * 1.3
        
        # if estimated_tokens > 120000:  # Safety margin
        #     raise ValueError("Text too long for single API call")
        PROMPT =  """CRITICAL INSTRUCTIONS - READ CAREFULLY:

            You are a text formatter with ONE TASK ONLY: Insert paragraph breaks (double newlines "\\n\\n") where topics change.

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
            2. Insert double newlines ("\\n\\n") to create paragraph breaks at topic changes
            3. Add periods ONLY where sentences clearly end without punctuation

            FORBIDDEN ACTIONS:
            - Changing any word order
            - Replacing words with synonyms
            - Combining or splitting sentences
            - Adding connecting words like "however," "therefore," etc.
            - Smoothing transitions between ideas
            - Making any stylistic improvements

            OUTPUT REQUIREMENT: Return the exact original text with ONLY paragraph breaks added. No explanations, no comments, no improvements.

            Text to format:

            {}"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{
                "role": "system",
                "content": PROMPT
            }, {
                "role": "user", 
                "content": text
            }],
            temperature=0.0,
            max_tokens=16000,
            presence_penalty=0.0,    # Don't encourage new content
            frequency_penalty=0.0    # Don't penalize repetition
        )
        
        return response.choices[0].message.content