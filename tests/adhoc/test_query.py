import json
from phase2_rag.chroma_db import get_vector_store
vectorstore = get_vector_store()
results = vectorstore.similarity_search("Show me the fund manager for Groww Value Fund", k=3, filter={"document_type": "Web"})
for doc in results:
    print(doc.metadata.get("chunk_type"))
    print(doc.page_content[:100])
