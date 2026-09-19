import os
from pathlib import Path
from dotenv import load_dotenv

# Points to the project root (ai_travel_assistant/)
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"

load_dotenv(dotenv_path=ENV_PATH)

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
FAISS_INDEX_PATH = "faiss_index"
LLM_MODEL = os.getenv("GOOGLE_MODEL_NAME")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL")