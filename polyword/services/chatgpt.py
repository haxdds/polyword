import os
from openai import OpenAI

api_key = ""

client = OpenAI(api_key=api_key or os.getenv('OPENAI_API_KEY'))

class ChatGPTService:
    DEFAULT_SYSTEM_PROMPT = """I want you to edit the following text while following the rules below:
    - Keep as much of the original content as possible
    - Keep the original meaning and intent of the text
    - Make sure the text is grammatically correct
    - Format the text as a markdown document
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