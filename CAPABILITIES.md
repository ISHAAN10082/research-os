# ResearchOS 2.0 Capabilities ⚡️

ResearchOS is distinguished by its hybrid "Local-First / Cloud-Boosted" architecture, spatial visualization, and cognitive modeling.

## 🧠 System Intelligence

### 1. Hybrid Inference Engine
*   **Smart Routing**: Dynamically routes queries between local and cloud models based on complexity and privacy needs.
    *   **Local**: Phi-3.5 (Quantized) running on Apple Silicon (MLX). Zero latency, 100% private.
    *   **Cloud**: Llama-3-70b (via Groq). Massive reasoning capability for synthesis.
*   **Streaming**: Real-time token streaming for all interactions, ensuring the interface feels "alive".

### 2. Viscera (Data Ingestion)
*   **Grobid Integration**: Transforming PDF "blobs" into structured semantic data (Title, Abstract, Citations, Tables).
*   **Entity Extraction**: SpaCy-powered Named Entity Recognition (NER) to identify authors, institutions, and concepts.
*   **Automated Recursive Search**: (Coming Soon) Autonomous agent searching ArXiv for cited papers.

### 3. Spatial Telemetry
*   **Consciousness Logs**: Every scroll, click, and dwell time is logged to a high-concurrency SQLite WAL database.
*   **Analytical Engine**: DuckDB performs real-time OLAP queries on user behavior to calculate "Reading Velocity" and "Crystallization Rates".

---

## 🖥 Frontend Experience

### 1. Citation Graph (The "Galaxy")
*   **Technology**: Three.js + InstancedMesh.
*   **Performance**: Renders 2,000+ nodes at 60fps.
*   **Physics**: Real-time Force-Directed Layout (`d3-force-3d`) simulating academic gravity (citations pull papers together).

### 2. Reading Copilot
*   **Context-Aware**: The chat knows what you are reading.
*   **Rich Text**: Full Markdown and LaTeX support for rendering mathematical proofs and code blocks.
*   **State**: Persisted via `Zustand`.

### 3. Real-Time Sync
*   **WebSockets**: Bi-directional communication.
    *   *Chat Channel*: Streaming tokens.
    *   *Canvas Channel*: Syncing graph state and telemetry events.
*   **Collaboration**: (In Progress) Yjs integration for multi-user research sessions.

---

## 🛡 Privacy & Security
*   **Local Persistence**: Your library and logs live on your disk.
*   **Optional Cloud**: Cloud is only used when you explicitly toggle it or for complex queries (requires API Key).
