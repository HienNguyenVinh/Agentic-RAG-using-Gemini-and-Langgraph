import os
from google import genai
from dotenv import load_dotenv
load_dotenv()

GOOGLE_KEY = os.getenv("GEMINI_API_KEY")

class GeminiEmbedding:
    def __init__(self, model_name='text-embedding-004'):
        self.model_name = model_name
        self.client = genai.Client(api_key=GOOGLE_KEY)

    def get_embedding(self, text):
        if not text.strip():
            print("Attemp to embedding a empty text")
            return []
        vector =  self.client.models.embed_content(model=self.model_name, contents=text)
        
        return vector.embeddings[0].values

