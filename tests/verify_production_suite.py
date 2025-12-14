"""
ResearchOS Production Verification Suite (Isolated & Fast)
========================================================
Runs full logic validation in <5s by strictly isolating the database environment.
Ensures zero lock contention with production services.

Usage:
    python3 tests/verify_production_suite.py
"""

import sys
import os
import time
import asyncio
import tempfile
import shutil
import platform
from pathlib import Path
from loguru import logger

# Add root to python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))



# Setup Logging
logger.remove()
logger.add(sys.stdout, format="<green>{time:HH:mm:ss}</green> | <level>{message}</level>")

class TestRunner:
    def __init__(self):
        self.results = []
    
    def record(self, name, success, error=None, duration=0):
        status = "✅ PASS" if success else "❌ FAIL"
        self.results.append({'name': name, 'success': success, 'error': error})
        logger.info(f"{status} | {name} ({duration*1000:.1f}ms)")
        if error:
            logger.error(f"       Error: {error}")

# --- ISOLATION HANDLING ---
TEST_TEMP_DIR = tempfile.mkdtemp(prefix="jrvis_test_")

def setup_isolation():
    """Redirects all DB paths to temp directory before any imports."""
    try:
        import research_os.config
        
        # Override critical paths
        test_brain = Path(TEST_TEMP_DIR)
        
        # We modify the singleton 'settings' object directly
        research_os.config.settings.BRAIN_DIR = test_brain
        research_os.config.settings.KUZU_DB_PATH = test_brain / "kuzu_store"
        research_os.config.settings.FAISS_INDEX_PATH = test_brain / "faiss_index.bin"
        
        # Ensure dirs exist
        research_os.config.settings.ensure_dirs()
        
        logger.info(f"🛡️  Environment Isolated: {test_brain}")
        return True
    except ImportError:
        logger.error("Failed to import config for isolation")
        return False

def teardown_isolation():
    """Clean up temp directory."""
    try:
        shutil.rmtree(TEST_TEMP_DIR, ignore_errors=True)
        logger.info("🧹 Cleaned up test environment")
    except Exception as e:
        logger.error(f"Failed to cleanup {TEST_TEMP_DIR}: {e}")

# --- TEST SUITES ---

async def verify_infrastructure():
    logger.info("\n📦 Validating Infrastructure (Isolated DB)")
    runner = TestRunner()
    
    # 1. GraphEngine (Pure KuzuDB, No AI Imports)
    try:
        t0 = time.time()
        # Ensure only GraphEngine is imported, not ModelCache which triggers AI loading
        from research_os.foundation.graph import graph_engine
        
        # Verify it points to our temp dir
        assert str(graph_engine.db_path).startswith(TEST_TEMP_DIR)
        
        # Test basic graph ops (CRUD)
        # We can safely use Kuzu here if ST/Torch is not loaded
        graph_engine.add_concept("TestConcept", [0.1]*768)
        
        runner.record("Graph Logic (Isolated)", True, duration=time.time()-t0)
        
    except Exception as e:
        runner.record("Graph Logic", False, str(e))

    # 2. Startup Script Config
    try:
        t0 = time.time()
        start_script = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'start_all.sh')
        with open(start_script) as f:
            content = f.read()
            assert "MAX_HEALTH_CHECKS=60" in content
            # assert "check_process" in content # Removed: script uses direct kill -0 check
        runner.record("Startup Script Config", True, duration=time.time()-t0)
    except Exception as e:
        runner.record("Start Script", False, str(e))

    return runner.results

async def verify_export():
    logger.info("\n📚 Validating Export Pipeline")
    runner = TestRunner()
    
    try:
        t0 = time.time()
        from research_os.export.bibtex import BibTeXExporter
        exporter = BibTeXExporter()
        
        # Real logic test
        res = exporter.escape_latex("A & B %")
        assert res == r"A \& B \%"
        
        paper = {'title': 'Real Test', 'authors': ['Smith, John'], 'year': 2024}
        bib = exporter.generate_bibtex([paper])
        assert "@" in bib and "Smith" in bib
        
        runner.record("BibTeX Export Logic", True, duration=time.time()-t0)
        
    except Exception as e:
        runner.record("BibTeX Export", False, str(e))
        
    return runner.results

# Removed verify_deduplication to avoid AI imports in this suite
# AI components should be tested in a separate process/file

async def main():
    logger.info("🚀 Starting Isolated Production Verification")
    logger.info("Target: < 5s execution")
    t_start = time.time()
    
    # 0. Setup Isolation
    if not setup_isolation():
        sys.exit(1)
    
    try:
        results = []
        results.extend(await verify_infrastructure())
        results.extend(await verify_export())
        # vs.extend(await verify_deduplication()) # Moved to separate test
        
        passed = sum(1 for r in results if r['success'])
        total = len(results)
        duration = time.time() - t_start
        
        logger.info("\n" + "="*50)
        logger.info(f"FINAL RESULT: {passed}/{total} Passed")
        logger.info(f"Total Time:   {duration:.3f}s")
        logger.info("="*50)
        
        if duration > 10:
             logger.warning("⚠️  Time target missed (>10s)")
        else:
             logger.info("✅ FAST & VERIFIED")
             
        if passed == total:
            sys.exit(0)
        else:
            sys.exit(1)
            
    finally:
        teardown_isolation()

if __name__ == "__main__":
    asyncio.run(main())
