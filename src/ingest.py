import os
import time
import requests
from bs4 import BeautifulSoup
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
from config import GOOGLE_API_KEY, FAISS_INDEX_PATH, EMBEDDING_MODEL

SOURCES = [
    {
        "title": "Wikivoyage: Singapore Travel Guide",
        "url": "https://en.wikivoyage.org/wiki/Singapore"
    },
    {
        "title": "Visit Singapore: Essential Travel Information",
        "url": "https://www.visitsingapore.com/travel-tips/essential-travel-information/"
    },
    {
        "title": "Visit Singapore: Sample Itineraries",
        "url": "https://www.visitsingapore.com/travel-tips/travelling-to-singapore/itineraries/"
    },
    {
        "title": "Visit Singapore: Things to Do",
        "url": "https://www.visitsingapore.com/things-to-do/top-things-to-do/"
    },
    {
        "title": "Visit Singapore: Singapore Tours",
        "url": "https://www.visitsingapore.com/things-to-do/singapore-tours/"
    }
]

def fetch_webpage_content(url: str) -> str:
    """Fetch webpage HTML and parse clean paragraph text."""
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Remove navigation, script, and style noise
        for element in soup(["script", "style", "nav", "footer", "header"]):
            element.decompose()
            
        paragraphs = [p.get_text(strip=True) for p in soup.find_all(["p", "h2", "h3", "li"])]
        return "\n".join(filter(None, paragraphs))
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return ""

def build_knowledge_base():
    """Scrape sources, generate embeddings, and persist in FAISS."""
    documents = []
    
    for src in SOURCES:
        print(f"Fetching: {src['title']}...")
        text = fetch_webpage_content(src["url"])
        if text:
            # Retain title and URL as metadata for RAG citations
            doc = Document(
                page_content=text,
                metadata={"source_title": src["title"], "source_url": src["url"]}
            )
            documents.append(doc)

    # Chunk text to preserve context boundaries
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=700, chunk_overlap=100)
    splits = text_splitter.split_documents(documents)
    print(f"Generated {len(splits)} semantic chunks.")

    # Embed and save FAISS index locally
    embeddings = GoogleGenerativeAIEmbeddings(model=EMBEDDING_MODEL, google_api_key=GOOGLE_API_KEY)
    
    # Process chunks in small batches with a delay to avoid 429 quota errors
    batch_size = 5
    vectorstore = None
    
    for i in range(0, len(splits), batch_size):
        batch = splits[i:i + batch_size]
        if vectorstore is None:
            vectorstore = FAISS.from_documents(batch, embeddings)
        else:
            vectorstore.add_documents(batch)
        time.sleep(2)  # Wait 2 seconds between batches to respect free tier limits

    # 4. Save locally
    vectorstore.save_local(FAISS_INDEX_PATH)
    print("FAISS vector database successfully created and saved!")

if __name__ == "__main__":
    build_knowledge_base()