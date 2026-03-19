from phase2_rag.chroma_db import get_vector_store
vs = get_vector_store()
print(f"Total docs in DB: {vs._collection.count()}")
docs = vs.similarity_search("Nifty 50 Index Fund", k=2)
print(f"Results: {len(docs)}")
