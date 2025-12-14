# External Integrations Reference

## Cloud Services

### Groq (LLM & Whisper)
| Item | Value |
|------|-------|
| **Service** | [Groq Cloud](https://console.groq.com/) |
| **Models Used** | `llama-3.3-70b-versatile` (chat), `distil-whisper-large-v3-en` (transcription) |
| **Client Library** | `groq>=0.9.0` |
| **Env Variable** | `GROQ_API_KEY` |
| **Use-Case** | Cloud fallback for complex reasoning & fast transcription |

### Semantic Scholar
| Item | Value |
|------|-------|
| **Service** | [Semantic Scholar API](https://www.semanticscholar.org/product/api) |
| **Client Library** | `semanticscholar` (runtime) |
| **Env Variable** | None (free public API) |
| **Use-Case** | Paper Whispers ambient discovery, Serendipity walks |

---

## Databases

### KuzuDB (Knowledge Graph)
| Item | Value |
|------|-------|
| **Type** | Embedded C++ graph database |
| **Library** | `kuzudb>=0.6.0` |
| **Storage Path** | `~/.gemini/antigravity/brain/kuzu_store` |
| **Use-Case** | Entity & relation storage for knowledge graph |

### FAISS (Vector Store)
| Item | Value |
|------|-------|
| **Type** | Dense vector similarity search |
| **Library** | `faiss-cpu>=1.8.0` |
| **Storage Path** | `~/.gemini/antigravity/brain/faiss_index.bin` |
| **Use-Case** | Retrieval embeddings storage |

### usearch (Alternative ANN)
| Item | Value |
|------|-------|
| **Type** | Lightweight ANN search |
| **Library** | `usearch>=2.11.0` |
| **Use-Case** | Faster approximate nearest-neighbor search |

---

## Environment Variables Summary

| Variable | Required | Description |
|----------|----------|-------------|
| `GROQ_API_KEY` | Optional | Cloud LLM & Whisper access |
| `DEBATE_MODEL_PATH` | Optional | Override default debate LLM path |

---

## Configuration File

All settings are centralized in [`research_os/config.py`](file:///Users/ishaanmajumdar/Desktop/Jrvis/research_os/config.py) via Pydantic `BaseSettings`. Environment variables and `.env` files are loaded automatically.
