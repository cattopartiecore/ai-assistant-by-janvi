"""
Configuration module for GDG-USAR AI Document Assistant.
Handles paths, model settings, chunking parameters, and similarity thresholds.
Supports both local (.env / os.environ) and Streamlit Community Cloud (st.secrets) environments.
"""

# Streamlit Community Cloud SQLite3 compatibility fix for ChromaDB (Linux)
try:
    __import__("pysqlite3")
    import sys
    sys.modules["sqlite3"] = sys.modules.pop("pysqlite3")
except (ImportError, KeyError):
    pass

import os
from pathlib import Path
from dotenv import load_dotenv

# Base directory paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
EVAL_DIR = BASE_DIR / "eval"
CHROMA_PERSIST_DIR = BASE_DIR / "chroma_db"

# Load .env from project root if present
ENV_FILE = BASE_DIR / ".env"
if ENV_FILE.exists():
    load_dotenv(ENV_FILE)
else:
    load_dotenv()


def get_config_secret(key: str, default: str = "") -> str:
    """
    Retrieves configuration values by checking Streamlit secrets first,
    falling back to os.environ and .env. Works seamlessly in both local
    and Streamlit Community Cloud environments.
    """
    # 1. Check Streamlit secrets if running inside Streamlit
    try:
        import streamlit as st
        if hasattr(st, "secrets") and key in st.secrets:
            val = st.secrets[key]
            if val is not None and str(val).strip():
                return str(val).strip()
    except Exception:
        pass

    # 2. Check os.environ (populated via .env or system env)
    val = os.getenv(key)
    if val is not None and str(val).strip():
        return str(val).strip()

    return default


# Source Document
DEFAULT_PDF_PATH = DATA_DIR / "GDG_USAR_AI_Document_Assistant_Source_TASK3.pdf"

# Embedding Model
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

# Chunking Strategies
CHUNK_STRATEGIES = {
    "char_500": {
        "type": "character",
        "chunk_size": 500,
        "chunk_overlap": 50,
        "collection_name": "gdg_char_500",
        "description": "CharacterTextSplitter (size=500, overlap=50)",
    },
    "recursive_200": {
        "type": "recursive",
        "chunk_size": 200,
        "chunk_overlap": 40,
        "collection_name": "gdg_recursive_200",
        "description": "RecursiveCharacterTextSplitter (size=200, overlap=40)",
    },
}
DEFAULT_STRATEGY = "recursive_200"

# Retrieval Settings
DEFAULT_TOP_K = int(get_config_secret("TOP_K", "3"))
# Cosine similarity threshold (0.0 to 1.0; distance = 1 - similarity)
# Scores below this threshold trigger the retrieval guard fallback
SIMILARITY_THRESHOLD = float(get_config_secret("SIMILARITY_THRESHOLD", "0.40"))

# Fallback response mandated for out-of-scope / unanswerable questions
FALLBACK_RESPONSE = "This information is not available in the handbook."

# LLM Provider Configuration
LLM_PROVIDER = get_config_secret("LLM_PROVIDER", "gemini").lower()
GOOGLE_API_KEY = get_config_secret("GOOGLE_API_KEY", "")
GROQ_API_KEY = get_config_secret("GROQ_API_KEY", "")

# Model names
GEMINI_MODEL = get_config_secret("GEMINI_MODEL", "gemini-3.5-flash-lite")
GROQ_MODEL = get_config_secret("GROQ_MODEL", "llama-3.1-8b-instant")
