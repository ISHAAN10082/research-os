# 🎓 ResearchOS 3.0 V2 - User Guide

## 🚀 Quick Start (Web Interface)

ResearchOS features a high-fidelity **React 19 Canvas** for 3D exploration and synthesis.

### 1. Launch the UI
```bash
# Start the Backend Server (FastAPI)
export PYTHONPATH=$PYTHONPATH:.
python3 research_os/web/server.py
```
**Then open:** `http://localhost:8000`

### 2. Manual Batch Mode (Headless)
For processing thousands of papers without the UI:
```bash
python3 jarvis_m4/main.py
```

---

## 💾 Data Persistence & Obsidian (FAQ)

### "Will my data be deleted when I close the chat?"
**NO.** ResearchOS is **Local-First** and **Persistent**.
*   All claims, debates, and graphs are stored in an embedded database: `data/research.kuzu`.
*   This database persists on your hard drive. You can restart the computer, and your Knowledge Graph will be exactly as you left it.

### "How do I use this with Obsidian?"
ResearchOS automatically generates markdown reports.
1.  **Where are they?**
    *   `data/obsidian_vault/Papers/` (Analysis of each paper)
    *   `data/obsidian_vault/Hypotheses/` (Generated research ideas)
2.  **How to Sync:**
    *   Open Obsidian.
    *   Click "Open Folder as Vault".
    *   Select the `data/obsidian_vault` folder inside the `Jrvis` directory.
    *   **Done.** As ResearchOS processes papers in the background, new files will magically appear in Obsidian.

---

## 🌟 Feature List & Intuitive Usage

### 1. 🧠 **The Knowledge Graph (Visualized)**
*   **Intuition:** Navigate your research like a galaxy.
*   **Usage:** Click "Graph" mode in the sidebar. You'll see nodes (claims) and edges (relations).
    *   **Green Edges:** Support.
    *   **Red Edges:** Contradictions.
    *   **Size:** Confidence score.

### 2. ⚔️ **Adversarial Debate Engine**
*   **Intuition:** AI scientists arguing for you.
*   **Usage:** In the "Synthesis" tab, select two claims and click "Debate".
    *   Watch the **Methodologist** attack the sample size.
    *   Watch the **Skeptic** find logical fallacies.
    *   See the **Calibrated Score** (e.g., "42% Likely Truth").

### 3. 🎯 **Calibrated Confidence (The "Trust Score")**
*   **What it is:** A probability, not a guess.
*   **Intuitive Use:**
    *   **> 85%:** Confirmed Science.
    *   **40-60%:** Weak Evidence / Rumor.
    *   **< 30%:** Noise.

### 4. 🏰 **Memory Palace 3.0**
*   **Intuition:** Your library organized by *meaning*, not filenames.
*   **Usage:** Go to "reading" mode. The "Wings" (clusters) are dynamically labeled (e.g., "Transformer Architectures", "Bioinformatics").

---

## 🛠️ Advanced Configuration

### Toggling "Aggressive Mode"
Edit `jarvis_m4/services/evidence_debate.py`:
- `self.min_citations_required = 2` (Strict mode)

### Adding New Papers
1. **Drag & Drop:** Use the UI "Upload" button.
2. **Folder Drop:** Put files in `data/`, restart server.

---

## 📊 Technical Details
*   **Frontend:** React 19, Tailwind, Three.js (Fiber).
*   **Backend:** FastAPI + KuzuDB embedded.
*   **Logs:** `jarvis_pipeline_v2.log`.
