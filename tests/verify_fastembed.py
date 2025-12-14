
import sys
import time
from loguru import logger

def verify_fastembed():
    logger.info("⚡ Verifying FastEmbed (No-Torch Alternative)")
    
    try:
        t0 = time.time()
        from fastembed import TextEmbedding
        
        # Load Model (Lightweight, ONNX based)
        # using 'BAAI/bge-small-en-v1.5' or similar default
        model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
        logger.info("✅ FastEmbed Loaded")
        
        # Generate
        embeddings = list(model.embed(["Hello World", "Another Sentence"]))
        logger.info(f"✅ Generated {len(embeddings)} embeddings")
        logger.info(f"   Shape: {len(embeddings[0])} dim")
        
        logger.info(f"⏱️ Duration: {time.time()-t0:.3f}s")
        return True
        
    except Exception as e:
        logger.error(f"❌ FastEmbed Failed: {e}")
        return False

if __name__ == "__main__":
    if verify_fastembed():
        sys.exit(0)
    else:
        sys.exit(1)
