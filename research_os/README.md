# ResearchOS: Frontier M4

> **SOTA Local Research Assistant** optimized for Apple Silicon (M4)  
> All components are **FREE & Open Source** (Apache 2.0 / MIT)

---

## 🚀 Quick Start

### 1. Create Conda Environment

```bash
conda create -n research_os python=3.11 -y
conda activate research_os
```

### 2. Install Dependencies

```bash
cd /Users/ishaanmajumdar/Desktop/Jrvis/research_os

# Core dependencies
pip install pydantic pydantic-settings loguru pymupdf kuzu mlx mlx-lm groq rank-bm25

# Embeddings & Reranking (SOTA)
pip install FlagEmbedding sentence-transformers

# Optional: MinerU for advanced PDF parsing
pip install magic-pdf
```

### 3. Run ResearchOS

```bash
python -m research_os.main
```

---

## 📖 Commands

| Command | Description |
|---------|-------------|
| `ingest <path>` | Process PDF with MinerU/PyMuPDF |
| `search <query>` | Hybrid retrieval (Dense + BM25 + Rerank) |
| `ask <question>` | Full RAG: Retrieve context + Generate answer |
| `visualize <topic>` | Generate 3Blue1Brown-style animation |
| `benchmark` | Run performance tests |
| `topology` | Show knowledge graph statistics |
| `exit` | Quit |

---

## 🧠 SOTA Models Used

| Component | Model | License |
|-----------|-------|---------|
| **PDF Parsing** | MinerU 1.3+ / PyMuPDF | Apache 2.0 |
| **Embeddings** | BGE-M3 (MTEB: 71.67) | Apache 2.0 |
| **Reranking** | BGE-Reranker-v2-m3 | Apache 2.0 |
| **Local LLM** | Qwen2.5-7B-Instruct | Apache 2.0 |
| **Cloud LLM** | Groq Llama-3.3-70B | Free Tier |
| **Graph DB** | KuzuDB | MIT |

---

## ⚡ Performance Targets (M4 Air 24GB)

| Metric | Target |
|--------|--------|
| PDF Ingestion (100 pages) | < 5 seconds |
| Query Response | < 200ms |
| Retrieval Recall@10 | > 95% |
| Memory Usage | < 14GB |

---

## 🔧 Configuration

### Enable Cloud LLM (Optional)

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key_here
```

Get a free API key at: https://console.groq.com/

### Config Location

All settings are in `research_os/config.py`:

```python
LOCAL_LLM_MODEL = "mlx-community/Qwen2.5-7B-Instruct-4bit"
EMBEDDING_MODEL = "BAAI/bge-m3"
RERANKER_MODEL = "BAAI/bge-reranker-v2-m3"
```

---

## 📁 Project Structure

```
research_os/
├── config.py                 # Configuration & model paths
├── main.py                   # CLI entry point
├── benchmark.py              # Performance testing
├── requirements.txt          # Dependencies
│
├── foundation/
│   ├── core.py               # LLM generation (local + cloud)
│   ├── vector.py             # BGE-M3 embeddings
│   └── graph.py              # KuzuDB graph
│
├── ingestion/
│   ├── hydra.py              # Parallel ingestion
│   └── processors/
│       ├── paper.py          # PDF processing pipeline
│       └── mineru_parser.py  # MinerU integration
│
├── search/
│   ├── retriever.py          # Hybrid retrieval pipeline
│   ├── reranker.py           # BGE cross-encoder
│   ├── colpali_indexer.py    # Visual document retrieval
│   └── grover.py             # Quantum-inspired search
│
├── manifold/
│   └── topology.py           # Knowledge graph analysis
│
└── interface/
    └── cinema.py             # Manim visualizations
```

---

## 🧪 Testing

### Run Benchmarks
```bash
python -m research_os.benchmark
```

### Quick Test
```bash
python -c "from research_os.foundation.core import foundation; print('✅ Ready')"
```

---

## 🐛 Troubleshooting

### "No module named 'mlx'"
```bash
pip install mlx mlx-lm
```

### "No module named 'kuzu'"
```bash
pip install kuzu
```

### MinerU installation fails
The system will automatically fallback to PyMuPDF. No action needed.

### Embedding model download slow
First run downloads ~1.5GB. This is normal.

---

## 📜 License

All components are **FREE for personal and commercial use**:
- Apache 2.0: MinerU, BGE-M3, BGE-Reranker, Qwen2.5, MLX
- MIT: KuzuDB, ColPali, rank-bm25

---

## 🔗 Resources

- [MLX Documentation](https://ml-explore.github.io/mlx/)
- [BGE-M3 on HuggingFace](https://huggingface.co/BAAI/bge-m3)
- [MinerU GitHub](https://github.com/opendatalab/MinerU)
- [KuzuDB Docs](https://kuzudb.com/docs/)
- [Groq Console](https://console.groq.com/)

---

*Built with ❤️ for local-first AI research*
