"""
Configuration module for GDG-USAR AI Document Assistant.
Handles paths, model settings, chunking parameters, and similarity thresholds.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Base directory paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
EVAL_DIR = BASE_DIR / "eval"
CHROMA_PERSIST_DIR = BASE_DIR / "chroma_db"

# Load .env from project root
ENV_FILE = BASE_DIR / ".env"
if ENV_FILE.exists():
    load_dotenv(ENV_FILE)
else:
    load_dotenv()

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
DEFAULT_TOP_K = int(os.getenv("TOP_K", "3"))
# Cosine similarity threshold (0.0 to 1.0; distance = 1 - similarity)
# Scores below this threshold trigger the retrieval guard fallback
SIMILARITY_THRESHOLD = float(os.getenv("SIMILARITY_THRESHOLD", "0.40"))

# Fallback response mandated for out-of-scope / unanswerable questions
FALLBACK_RESPONSE = "This information is not available in the handbook."

# LLM Provider Configuration
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini").lower()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# Model names
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
