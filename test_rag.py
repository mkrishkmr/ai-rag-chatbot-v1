from phase2_rag.chroma_db import get_vector_store
vs = get_vector_store()
docs = vs.similarity_search_with_score("What is the exit load for the Nifty 50 Index Fund?", k=5)
for doc, score in docs:
    print(f"Score: {score:.4f} | Content: {doc.page_content[:150]}...\n")
