from typing import List
from langchain_core.documents import Document
from phase2_rag.chroma_db import get_vector_store

def retrieve_hybrid_context(query: str, k: int = 4) -> List[Document]:
    """
    Retrieves context from ChromaDB using a hybrid logic.
    Web documents are prioritized for volatile metrics (NAV, Expense Ratio).
    PDF documents are prioritized for structural rules (Lock-in, Exit Load).
    """
    vector_store = get_vector_store()
    
    # Simple query routing heuristic
    query_lower = query.lower()
    
    # Determine the priority document type based on keywords
    if any(kw in query_lower for kw in ["lock-in", "exit load", "rule", "constraint", "tax"]):
        # Prioritize PDF documents
        print("🔍 Routing Query: Prioritizing 'PDF' documents for constraint-related query.")
        # We can implement a pre-filter using Chroma metadata filtering
        filter_dict = {"document_type": "PDF"}
        results = vector_store.similarity_search(query, k=k, filter=filter_dict)
        
        # If not enough results, fetch remaining from anything
        if len(results) < k:
            remaining = vector_store.similarity_search(query, k=k - len(results))
            results.extend(remaining)
            
    elif any(kw in query_lower for kw in ["nav", "expense ratio", "fee", "return", "aum"]):
        # Prioritize Web documents
        print("🔍 Routing Query: Prioritizing 'Web' documents for metric-related query.")
        filter_dict = {"document_type": "Web"}
        results = vector_store.similarity_search(query, k=k, filter=filter_dict)
        
        if len(results) < k:
            remaining = vector_store.similarity_search(query, k=k - len(results))
            results.extend(remaining)
            
    else:
        # Standard unstructured retrieval
        print("🔍 Routing Query: Standard semantic retrieval.")
        results = vector_store.similarity_search(query, k=k)
        
    # Deduplicate based on content
    seen_content = set()
    unique_results = []
    for doc in results:
        if doc.page_content not in seen_content:
            seen_content.add(doc.page_content)
            unique_results.append(doc)
            
    return unique_results[:k]

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    # Quick Test
    print("\n--- Testing ELSS Lock-in Retrieval ---")
    docs = retrieve_hybrid_context("What is the lock-in period for ELSS Tax Saver?")
    for i, doc in enumerate(docs):
        print(f"\n[Result {i+1}] Source: {doc.metadata.get('source_url')} Type: {doc.metadata.get('document_type')}")
        print(f"Content snippet: {doc.page_content[:150]}...")
