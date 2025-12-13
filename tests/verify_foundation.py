from research_os.foundation.core import foundation
from research_os.config import settings
from loguru import logger
import sys

def verify_foundation():
    logger.info("--- Starting Foundation Verification ---")
    
    # 1. Config Check
    logger.info(f"Checking Config: is_apple_silicon={settings.is_apple_silicon()}")
    logger.info(f"DB Path: {settings.KUZU_DB_PATH}")

    # 2. Vector Engine Check
    logger.info("Testing Vector Engine...")
    vec = foundation.vector.embed_query("Hello ResearchOS")
    logger.info(f"Vector Generated. Shape: {len(vec)}")
    
    # 3. Graph Engine Check
    logger.info("Testing Graph Engine...")
    foundation.graph.add_concept("TestConcept", vec)
    logger.info("Concept added to Kuzudb.")
    
    # Query back
    res = foundation.graph.execute("MATCH (c:Concept) RETURN c.name")
    while res.has_next():
        logger.info(f"Found in Graph: {res.get_next()}")

    logger.info("--- Foundation Verification Passed ---")

if __name__ == "__main__":
    verify_foundation()
