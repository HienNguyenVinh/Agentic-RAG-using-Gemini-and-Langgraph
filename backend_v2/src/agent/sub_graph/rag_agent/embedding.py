import os
from langchain_google_genai.embeddings import GoogleGenerativeAIEmbeddings
from dotenv import load_dotenv
load_dotenv()

GOOGLE_KEY = os.getenv("GEMINI_API_KEY")
EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL')

class GeminiEmbedding:
    def __init__(self, model_name=EMBEDDING_MODEL):
        self.client = GoogleGenerativeAIEmbeddings(model=model_name)

    def get_embedding(self, text):
        if not text.strip():
            print("Attemp to embedding a empty text")
            return []
        vector =  self.client.embed_query(text)
        
        return vector