# ResearchOS 9.8 Release Notes

**Date:** December 14, 2024  
**Focus:** Reliability, Data Quality, and Export  
**Status:** Production Ready

---

## 🚀 Highlights

### 1. Robust Deduplication Engine
- **arXiv Version Awareness:** Automatically detects `v1` → `v2` updates.
- **Validation Mode:** Safe dry-run mode (`DEDUP_VALIDATION_MODE=true`) to log duplicates without blocking.
- **Multi-Factor Detection:** Checks file hash, DOI, and semantic similarity.

### 2. BibTeX Export
- **One-Click Export:** Download your entire library as `research_library.bib`.
- **LaTeX Safe:** Automatic escaping of special characters (`&`, `%`, `$`, `#`, `_`) and Unicode handling.
- **Standard Compliant:** Validated output compatible with Overleaf, Zotero, and Mendeley.

### 3. Verification & Reliability
- **Model Cache:** Singleton cache prevents redundant model loading (4s saved per generic load).
- **Graceful Shutdown:** Automatic resource cleanup on server exit (avoids memory leaks).
- **Health Checks:** Extended startup checks (60s timeout) to prevent premature failure.

---

## ⚠️ Breaking Changes

- **Startup Script:** Must use `./start_all.sh` instead of running `server.py` directly to ensure health checks.
- **Environment:** `DEDUP_VALIDATION_MODE` env var added.

---

## 📝 Upgrade Instructions

1. **Stop existing server:**
   ```bash
   pkill -f "python.*server"
   ```

2. **Run new startup script:**
   ```bash
   ./start_all.sh
   ```

3. **Verify Health:**
   Check logs for `✅ Model cache initialized`.

---

## 📊 Verification

Run the production suite (requires server stopped):
```bash
python3 tests/verify_production_suite.py
```
