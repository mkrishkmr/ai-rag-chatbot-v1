import os
import json
import shutil
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_core.documents import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter

load_dotenv()

CHROMA_DIR = "./chroma_db"

def get_vector_store():
    """Initializes and returns the Chroma vector store connection."""
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001",
        google_api_key=os.getenv("GOOGLE_API_KEY")
    )
    vector_store = Chroma(
        collection_name="groww_funds",
        embedding_function=embeddings,
        persist_directory=CHROMA_DIR
    )
    return vector_store

def clean_chroma_db():
    if os.path.exists(CHROMA_DIR):
        shutil.rmtree(CHROMA_DIR)
        print("🗑️ Cleaned up old ChromaDB.")

def ingest_fact_sheet(json_path: str = "groww_advanced_scraped.json"):
    """Reads the generated JSON and ingests it into ChromaDB with proper metadata."""
    if not os.path.exists(json_path):
        print(f"❌ Fact sheet {json_path} not found. Run Scraping first.")
        return

    with open(json_path, "r") as f:
        data = json.load(f)

    docs = []
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    
    for item in data:
        fund_name = item.get("fund_name", "Unknown Fund")
        source_url = item.get("source_url", "")
        scraped_fields = item.get("scraped_fields", {})
        
        # 1. Ingest Web Metrics Document (Structured Facts)
        web_text = f"Fund Name: {fund_name}\n"
        for key, value in scraped_fields.items():
            web_text += f"{key}: {value}\n"
            
        web_doc = Document(
            page_content=web_text,
            metadata={
                "source_url": source_url,
                "fund_name": fund_name,
                "document_type": "Web"
            }
        )
        docs.append(web_doc)
        
        # 2. Ingest the Fallback Text (Chunked)
        fallback_text = item.get("full_scraped_text_fallback", "")
        if fallback_text:
            chunks = text_splitter.split_text(fallback_text)
            for chunk in chunks:
                docs.append(Document(
                    page_content=f"Fund Name: {fund_name}\nAdditional Context: {chunk}",
                    metadata={
                        "source_url": source_url,
                        "fund_name": fund_name,
                        "document_type": "Web_Fallback"
                    }
                ))
        
        # 3. Ingest PDF Rules Document (Mocked for testing limits)
        pdf_text = f"Fund Name: {fund_name}\n"
        pdf_text += f"Exit Load Constraints:\n{scraped_fields.get('Exit Load', 'Nil')}\n"
        
        # Explicitly testing the 'ELSS lock-in'
        if "Elss" in fund_name or "ELSS" in fund_name:
            pdf_text += "ELSS lock-in: 3 Years Mandatory.\n"
            
        pdf_doc = Document(
            page_content=pdf_text,
            metadata={
                "source_url": source_url + "/sid.pdf",
                "fund_name": fund_name,
                "document_type": "PDF"
            }
        )
        docs.append(pdf_doc)

    vector_store = get_vector_store()
    print(f"🚀 Adding {len(docs)} documents to ChromaDB...")
    vector_store.add_documents(docs)
    print("✅ Ingestion to ChromaDB complete.")

if __name__ == "__main__":
    clean_chroma_db()
    ingest_fact_sheet()
