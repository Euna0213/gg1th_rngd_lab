import os

from dotenv import load_dotenv

load_dotenv(override=True)

# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

# API_KEY = os.getenv("LLM_API_KEY")
BASE_URL = os.getenv("OPENAI_BASE_URL")

MODEL = os.getenv("MODEL_ID", "gpt-4o-mini")
TEMPERATURE = os.getenv("LLM_TEMPERATURE", 2)
MAX_TOKENS = os.getenv("LLM_MAX_TOKENS", 2086)

EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL",
    "text-embedding-3-small"
)

# QDRANT_URL = os.getenv(
#     "QDRANT_URL",
#     "http://localhost:6333"
# )