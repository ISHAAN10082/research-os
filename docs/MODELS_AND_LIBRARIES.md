# Models, Libraries & Tools Reference

> **Generated**: 2024-12-14  
> **Codebase**: ResearchOS / Jrvis

---

## 1. Language Models (LLMs)

| Model | Version / Variant | License | Use-Case in Jrvis |
|-------|-------------------|---------|-------------------|
| **Phi-3.5-mini-instruct** (4-bit) | `mlx-community/phi-3.5-mini-instruct-4bit` | MIT | Default local LLM for chat, claim extraction, debate agents |
| **Qwen2.5-7B-Instruct** (4-bit) | `mlx-community/Qwen2.5-7B-Instruct-4bit` | Apache 2.0 | Alternate local LLM (configurable in `config.py`) |
| **Llama-3.3-70B-Versatile** | `llama-3.3-70b-versatile` (via Groq) | Meta Llama 3.3 License | Cloud fallback for complex reasoning / large contexts |
| **Whisper Large v3 Turbo** | `mlx-community/whisper-large-v3-turbo` | MIT | Local voice transcription |
| **Groq Whisper** | `distil-whisper-large-v3-en` | Apache 2.0 | Fast cloud transcription (Groq API) |

---

## 2. Embedding & Retrieval Models

| Model | Version / Variant | License | Use-Case |
|-------|-------------------|---------|----------|
| **BGE-M3** | `BAAI/bge-m3` | Apache 2.0 | Dense embeddings (1024-dim), multi-vector retrieval |
| **BGE-Reranker-v2-M3** | `BAAI/bge-reranker-v2-m3` | Apache 2.0 | Cross-encoder reranking for search results |
| **all-MiniLM-L6-v2** | `sentence-transformers/all-MiniLM-L6-v2` | Apache 2.0 | Fast, lightweight embeddings for claim extraction |
| **all-mpnet-base-v2** | `sentence-transformers/all-mpnet-base-v2` | Apache 2.0 | High-quality claim embeddings (replaces SPECTER2) |
| **ms-marco-MiniLM-L-6-v2** | `cross-encoder/ms-marco-MiniLM-L-6-v2` | Apache 2.0 | Fallback cross-encoder when FlagEmbedding unavailable |
| **ColPali v1.2** | `vidore/colpali-v1.2` | MIT | Visual retrieval for figure/table search |

---

## 3. Vector & Graph Databases

| Database | Min Version | License | Use-Case |
|----------|-------------|---------|----------|
| **FAISS (CPU)** | `>=1.8.0` | MIT | Dense vector similarity search |
| **usearch** | `>=2.11.0` | Apache 2.0 | Alternative lightweight ANN search |
| **KuzuDB** | `>=0.6.0` | MIT | Embedded C++ knowledge graph (entities & relations) |

---

## 4. Cloud Services & APIs

| Service | Client Library | Version | Use-Case |
|---------|---------------|---------|----------|
| **Groq** | `groq` | `>=0.9.0` | Cloud LLM inference (Llama-3.3-70B), Whisper transcription |

> **Environment Variable**: `GROQ_API_KEY`

---

## 5. Ingestion & Parsing

| Library | Min Version | License | Use-Case |
|---------|-------------|---------|----------|
| **marker-pdf** | `>=0.2.0` | Apache 2.0 | PDF text & layout extraction |
| **tree-sitter** | `>=0.21.0` | MIT | Code parsing for code-related papers |
| **trafilatura** | `>=1.9.0` | Apache 2.0 | Web scraping & boilerplate removal |
| **rank-bm25** | (runtime) | Apache 2.0 | Sparse (BM25) retrieval in `HybridRetriever` |

---

## 6. Audio & Voice

| Library | Min Version | Use-Case |
|---------|-------------|----------|
| **sounddevice** | `>=0.4.0` | Real-time audio capture / playback |
| **webrtcvad** | `>=2.0.10` | Voice-activity detection |

---

## 7. Data Processing

| Library | Min Version | Use-Case |
|---------|-------------|----------|
| **numpy** | `>=1.26.0` | Numerical operations throughout |
| **pandas** | `>=2.2.0` | Tabular metadata handling |
| **polars** | `>=1.0.0` | Faster DataFrame alternative |
| **orjson** | `>=3.10.0` | High-performance JSON (de)serialization |
| **fsspec** | `>=2024.0.0` | Abstract filesystem I/O |

---

## 8. LLM & Workflow Frameworks

| Library | Min Version | Use-Case |
|---------|-------------|----------|
| **mlx** | `>=0.19.0` | Apple-silicon native tensor ops |
| **mlx-lm** | `>=0.19.0` | Load & run local LLMs on Apple Silicon |
| **LangGraph** | (bundled) | StateGraph-based multi-agent workflows (Debate pipeline) |
| **sentence-transformers** | (runtime) | Embedding models & cross-encoders |
| **FlagEmbedding** | (runtime) | BGE Reranker integration |

---

## 9. Visualization & UI

| Library | Min Version | Use-Case |
|---------|-------------|----------|
| **manim** | `>=0.18.0` | Programmatic research animations |
| **rich** | `>=13.0.0` | Console logging & progress bars |
| **prompt_toolkit** | (runtime) | Interactive terminal UI |

---

## 10. Utilities

| Library | Min Version | Use-Case |
|---------|-------------|----------|
| **pydantic** | `>=2.9.0` | Data validation & settings |
| **python-dotenv** | `>=1.0.0` | Load `.env` files |
| **loguru** | `>=0.7.0` | Structured logging |
| **uvloop** | `>=0.21.0` | Fast asyncio event loop |
| **httpx** | (runtime) | Async HTTP client |
| **scikit-learn** | (runtime) | TF-IDF & cosine similarity in recommender |
| **spacy** | (runtime) | Entity extraction NLP pipeline |

---

## Quick Reference: Environment Variables

| Variable | Purpose |
|----------|---------|
| `GROQ_API_KEY` | API key for Groq cloud services |
| `DEBATE_MODEL_PATH` | Override default debate LLM |

---

*See `pyproject.toml` and individual service files for authoritative version constraints.*
