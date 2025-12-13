import os
import platform
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class SystemConfig(BaseSettings):
    """Hardware-aware system configuration for ResearchOS."""
    
    # --- Paths ---
    BASE_DIR: Path = Path(__file__).parent.parent
    BRAIN_DIR: Path = Path(os.path.expanduser("~/.gemini/antigravity/brain"))
    PARSED_OUTPUT_DIR: Path = BRAIN_DIR / "parsed_documents"
    
    # --- Hardware Constraints (M4 Air 24GB) ---
    MAX_RAM_GB: int = 18  # Safe limit for app
    USE_MPS: bool = Field(default=True, description="Force Metal Performance Shaders")
    
    # --- Service Configs ---
    KUZU_DB_PATH: Path = BRAIN_DIR / "kuzu_store"
    FAISS_INDEX_PATH: Path = BRAIN_DIR / "faiss_index.bin"
    
    # ========================================
    # SOTA Models (December 2024)
    # All FREE & Open Source (Apache 2.0 / MIT)
    # ========================================
    
    # --- Model Paths (Lazy Loading) ---
    LOCAL_LLM_MODEL: str = "mlx-community/phi-3.5-mini-instruct-4bit"
    # LOCAL_LLM_MODEL: str = "mlx-community/Qwen2.5-7B-Instruct-4bit"  # Best for SOTA
    WHISPER_MODEL: str = "mlx-community/whisper-large-v3-turbo"
    
    # --- Embeddings: BGE-M3 (Apache 2.0) ---
    # Multi-vector (dense+sparse+colbert), 100+ languages
    EMBEDDING_MODEL: str = "BAAI/bge-m3"
    EMBEDDING_DIM: int = 1024  # BGE-M3 dimension
    
    # --- Reranker: BGE-Reranker-v2 (Apache 2.0) ---
    # --- Reranker: BGE-Reranker-v2 (Apache 2.0) ---
    RERANKER_MODEL: str = "BAAI/bge-reranker-v2-m3"

    # --- Cloud Fallback (Tier 3) ---
    GROQ_MODEL: str = "llama3-70b-8192"
    GROQ_API_KEY: str = Field(default_factory=lambda: os.getenv("GROQ_API_KEY", ""))
    
    # --- ColPali: Visual Retrieval (MIT) ---
    COLPALI_MODEL: str = "vidore/colpali-v1.2"
    
    # --- Whisper: Speech Recognition ---
    WHISPER_MODEL: str = "mlx-community/whisper-large-v3-turbo"
    
    # --- Hybrid Engine (Groq - Free Tier) ---
    GROQ_API_KEY: str | None = Field(default=None, description="Optional Cloud Burst Key")
    GROQ_MODEL: str = "llama-3.3-70b-versatile"  # Free tier available
    
    # ========================================
    # Performance Tuning for M4
    # ========================================
    
    # Retrieval settings
    RETRIEVAL_TOP_K: int = 20  # Initial retrieval candidates
    RERANK_TOP_K: int = 5      # Final results after reranking
    CHUNK_SIZE: int = 512       # Characters per chunk
    CHUNK_OVERLAP: int = 128    # Overlap between chunks
    
    # Context management
    MAX_CONTEXT_TOKENS: int = 8192   # Max tokens for LLM context
    CLOUD_BURST_THRESHOLD: int = 4096  # Switch to cloud above this
    
    # Caching
    QUERY_CACHE_SIZE: int = 1000
    EMBEDDING_CACHE_SIZE: int = 10000
    
    # --- Audio ---
    SAMPLE_RATE: int = 16000
    
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        extra="ignore"
    )

    def is_apple_silicon(self) -> bool:
        return platform.system() == "Darwin" and platform.machine() == "arm64"

    def ensure_dirs(self):
        self.BRAIN_DIR.mkdir(parents=True, exist_ok=True)
        # KuzuDB manages its own directory. Do not pre-create it, 
        # or it will error if it finds an empty folder.

# Singleton Instance
settings = SystemConfig()

if not settings.is_apple_silicon():
    print("WARNING: Not running on Apple Silicon. Performance will be degraded.")
