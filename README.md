# ResearchOS 2.0 🧠

**ResearchOS** is a self-aware, intelligent research companion designed to augment your cognitive workflow. It combines high-performance 3D visualization, reading co-pilots, and automated knowledge synthesis into a unified spatial interface.

![Citation Graph](http://localhost:5173/graph-preview.png)

## 🚀 Quick Start

### 1. Prerequisites
*   **Python 3.11+** (for the Brain)
*   **Node.js 18+** (for the Interface)
*   *[Optional]* **Docker** (for Deep PDF Extraction)

### 2. Environment Setup

Create a `.env` file in the project root (`/Users/ishaanmajumdar/Desktop/Jrvis/.env`) with the following variables:

```ini
# REQUIRED: For Cloud Intelligence (Llama-3-70b via Groq)
# Get one here: https://console.groq.com/keys
GROQ_API_KEY=gsk_...

# OPTIONAL: System Preferences
# LOG_LEVEL=INFO
# TELEMETRY_ENABLED=true
```

> **Note**: If you do not provide a `GROQ_API_KEY`, the system will automatically fall back to the **Local Phi-3.5 Model** (running on your Mac's Neural Engine via MLX).

### 3. Launch System

You need two terminal windows to run the full stack (Brain + Face).

**Terminal 1: The Brain (Backend)**
```bash
conda activate research_os
python -m research_os.web.server
```
*You should see logs indicating "GraphEngine connected" and "Uvicorn running on http://0.0.0.0:8000"*

**Terminal 2: The Face (Frontend)**
```bash
cd research_os/web/ui
npm run dev
```
*Click the link shown (usually http://localhost:5173) to open ResearchOS.*

---

## 🧭 User Guide

### **Synthesis Workspace**
*   **Purpose**: Your command center. Manage research threads, view system notifications, and generate high-level summaries.
*   **Interaction**: Use the chat bar to query your entire library.
    *   *Example*: "What are the key trends in transformer architecture from my papers?"

### **Reading Mode**
*   **Purpose**: Deep reading with an AI Copilot.
*   **How to use**:
    1.  Select a paper from the **Library Sidebar**.
    2.  The paper opens in a split view.
    3.  **Chat with the Paper**: Ask questions about specific sections. The context is automatically injected.
    4.  **Local vs Cloud**: Toggle the button in the top right to switch between **MLX (Local Privacy)** and **Groq 70B (Cloud Speed)**.

### **Graph Mode**
*   **Purpose**: Visualize the "Shape of Science".
*   **Interactions**:
    *   **Orbit**: Drag to rotate.
    *   **Zoom**: Scroll to dive in.
    *   **Click**: Click any node (sphere) to jump to that paper in Reading Mode.
    *   *Note*: This uses a high-performance 60fps renderer capable of handling thousands of nodes.

### **Deep Extraction (Optional)**
For academic-grade table and reference extraction, run:
```bash
docker-compose up -d
```
This starts the local Grobid server. ResearchOS automatically detects it.

---

## 🛠 Troubleshooting

*   **"ModuleNotFoundError"**: ensure you activated the environment (`conda activate research_os`).
*   **"Repetitive Text"**: Ensure you are using the latest frontend (refresh the page).
*   **"No Groq API Key"**: The system will warn you log but continue using the Local model transparently.
