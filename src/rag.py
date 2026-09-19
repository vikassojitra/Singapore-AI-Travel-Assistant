from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain.tools import tool
from config import GOOGLE_API_KEY, FAISS_INDEX_PATH, EMBEDDING_MODEL

embeddings = GoogleGenerativeAIEmbeddings(model=EMBEDDING_MODEL, google_api_key=GOOGLE_API_KEY)
vectorstore = FAISS.load_local(FAISS_INDEX_PATH, embeddings, allow_dangerous_deserialization=True)
retriever = vectorstore.as_retriever(search_kwargs={"k": 4})

@tool
def singapore_knowledge_search(query: str) -> str:
    """Search the Singapore travel knowledge base for attractions, culture, transport, food, and itineraries."""
    docs = retriever.invoke(query)
    if not docs:
        return "No relevant destination information found in the knowledge base."
    
    results = []
    for doc in docs:
        title = doc.metadata.get("source_title", "Unknown Source")
        url = doc.metadata.get("source_url", "")
        results.append(f"Content: {doc.page_content}\nSource: {title} ({url})")
    
    return "\n\n---\n\n".join(results)