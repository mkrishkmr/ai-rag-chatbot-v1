import os
import chromadb
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from functools import lru_cache

load_dotenv()

@lru_cache(maxsize=1)
def get_vector_store():
    """
    Initializes and returns the persistent Chroma vector store connection.
    Uses persistent disk storage locally.
    """
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001",
        google_api_key=os.getenv("GOOGLE_API_KEY")
    )
    
    # Persistent client for local storage
    client = chromadb.PersistentClient(path="chroma_db/")
    
    vector_store = Chroma(
        client=client,
        collection_name="groww_funds",
        embedding_function=embeddings
    )
    return vector_store
