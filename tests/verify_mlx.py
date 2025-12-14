
import sys
import time
import os
from loguru import logger

def verify_mlx_stack():
    logger.info("🍎 Verifying Apple Silicon (MLX) Stack")

    # 1. Verify MLX Installation
    try:
        import mlx.core as mx
        logger.info(f"✅ MLX Imported (Device: {mx.default_device()})")
    except ImportError:
        logger.error("❌ MLX not installed")
        return

    # 2. Verify MLX LLM (Phi-3.5)
    try:
        from mlx_lm import load, generate
        logger.info("loading mlx-community/phi-3.5-mini-instruct-4bit...")
        # detailed load check
        t0 = time.time()
        model, tokenizer = load("mlx-community/phi-3.5-mini-instruct-4bit")
        logger.info(f"✅ Phi-3.5 Loaded in {time.time()-t0:.2f}s")
        
        # Test Generation
        prompt = "test"
        response = generate(model, tokenizer, prompt=prompt, max_tokens=10)
        logger.info(f"✅ Generation Check: {response.strip()}")
        
    except Exception as e:
        logger.warning(f"⚠️  MLX LLM Failed/Skipped: {e}")

    # 3. Test MLX Embeddings (Experimental)
    # Are there native MLX embedding models we can use instead of FastEmbed?
    # Usually people use 'mlx-embeddings' package or similar, or just BERT in MLX.
    # We will check if we can load a BERT model in MLX.
    try:
        logger.info("Checking MLX Embedding feasibility...")
        # This requires huggingface download of a compatible mlx model
        # We'll just check if we can import the functionality or if 'mlx_lm' supports 'bert'
        # mlx_lm is mostly for causal LM.
        pass
    except Exception as e:
        logger.warning(f"⚠️  MLX Embedding check failed: {e}")

if __name__ == "__main__":
    verify_mlx_stack()
