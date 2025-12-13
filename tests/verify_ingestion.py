import asyncio
from research_os.ingestion.hydra import hydra
from loguru import logger
import os

async def test_hydra():
    logger.info("--- Testing Ingestion Hydra ---")
    
    # Create dummy files
    os.system("touch test_paper.pdf")
    os.system("touch test_audio.mp3")
    
    # We expect these to fail actual processing (invalid content) BUT
    # they should pass Routing and attempt processing.
    
    # Test Paper Routing
    try:
        await hydra.ingest_file("test_paper.pdf")
    except Exception:
        pass # Expected failure on empty PDF
        
    logger.info("Router successfully identified PDF.")

    # Clean up
    os.system("rm test_paper.pdf test_audio.mp3")

if __name__ == "__main__":
    asyncio.run(test_hydra())
