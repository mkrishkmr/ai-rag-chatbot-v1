import os
import json
from phase2_rag.chroma_db import get_vector_store
from langchain_core.documents import Document

try:
    vectorstore = get_vector_store()
    # Get everything
    all_data = vectorstore._collection.get(include=['documents', 'metadatas'])
    ids = all_data['ids']
    docs = all_data['documents']
    metadatas = all_data['metadatas']
    
    print(f"Checking {len(ids)} documents...")
    bad_ids = []
    
    for i, (doc_id, text, meta) in enumerate(zip(ids, docs, metadatas)):
        # Check for null text
        if text is None:
            print(f"Found null document text at ID: {doc_id}")
            bad_ids.append(doc_id)
            continue
            
        # Try to instantiate a Document object to see if Pydantic fails
        try:
            # LangChain 0.3 Document creation
            d = Document(page_content=text, metadata=meta or {})
        except Exception as e:
            print(f"Pydantic validation failure at ID: {doc_id} - ERROR: {e}")
            bad_ids.append(doc_id)
            
    if bad_ids:
        print(f"Deleting {len(bad_ids)} corrupt documents...")
        vectorstore._collection.delete(ids=bad_ids)
        print("Done!")
    else:
        print("No corrupt documents found.")
        
except Exception as e:
    print(f"Fatal error during fix: {e}")
