"""
ResearchOS SOTA Benchmark Suite (December 2024)
Validates performance targets for the M4-optimized research assistant.
"""
import asyncio
import time
from pathlib import Path
from typing import Dict, Any
from loguru import logger


class Benchmark:
    """Performance benchmark for ResearchOS components."""
    
    def __init__(self):
        self.results = {}
    
    async def run_all(self) -> Dict[str, Any]:
        """Run complete benchmark suite."""
        logger.info("🏁 Starting ResearchOS Benchmark Suite...")
        
        results = {}
        
        # 1. Embedding benchmark
        results["embedding"] = await self._benchmark_embedding()
        
        # 2. Retrieval benchmark
        results["retrieval"] = await self._benchmark_retrieval()
        
        # 3. LLM benchmark
        results["llm"] = await self._benchmark_llm()
        
        # 4. End-to-end benchmark
        results["e2e"] = await self._benchmark_e2e()
        
        self.results = results
        self._print_summary()
        
        return results
    
    async def _benchmark_embedding(self) -> Dict:
        """Benchmark embedding generation."""
        logger.info("📊 Benchmarking Embeddings (BGE-M3)...")
        
        try:
            from research_os.foundation.vector import get_vector_engine
            engine = get_vector_engine()
            
            test_texts = [
                "The transformer architecture has revolutionized natural language processing.",
                "Attention mechanisms allow models to focus on relevant parts of the input.",
                "Large language models demonstrate emergent reasoning capabilities."
            ]
            
            # Warmup
            _ = engine.embed(["warmup"])
            
            # Benchmark
            start = time.perf_counter()
            embeddings = engine.embed(test_texts)
            elapsed = time.perf_counter() - start
            
            return {
                "status": "success",
                "texts_count": len(test_texts),
                "embedding_dim": len(embeddings[0]) if embeddings else 0,
                "total_ms": round(elapsed * 1000, 2),
                "per_text_ms": round(elapsed * 1000 / len(test_texts), 2)
            }
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def _benchmark_retrieval(self) -> Dict:
        """Benchmark hybrid retrieval pipeline."""
        logger.info("🔍 Benchmarking Retrieval Pipeline...")
        
        try:
            from research_os.search.retriever import get_retriever, Chunk
            retriever = get_retriever()
            
            # Add test documents
            test_chunks = [
                Chunk(text="Machine learning models learn from data to make predictions.", 
                      source="test", chunk_id="0"),
                Chunk(text="Deep learning uses neural networks with multiple layers.",
                      source="test", chunk_id="1"),
                Chunk(text="Transformers use self-attention for sequence modeling.",
                      source="test", chunk_id="2"),
                Chunk(text="BERT is a bidirectional encoder representation model.",
                      source="test", chunk_id="3"),
                Chunk(text="GPT models are autoregressive language models.",
                      source="test", chunk_id="4"),
            ]
            
            await retriever.add_chunks(test_chunks)
            
            # Benchmark search
            query = "How do transformers work?"
            
            start = time.perf_counter()
            results = await retriever.search(query, top_k=3)
            elapsed = time.perf_counter() - start
            
            # Cleanup
            retriever.clear()
            
            return {
                "status": "success",
                "indexed_chunks": len(test_chunks),
                "results_count": len(results),
                "search_ms": round(elapsed * 1000, 2),
                "top_result": results[0].chunk.text[:50] if results else None
            }
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def _benchmark_llm(self) -> Dict:
        """Benchmark local LLM generation."""
        logger.info("🤖 Benchmarking Local LLM (Qwen2.5-7B)...")
        
        try:
            from research_os.foundation.core import foundation
            
            prompt = "What is the capital of France? Answer in one word."
            
            start = time.perf_counter()
            response = foundation.generate(prompt, max_tokens=50)
            elapsed = time.perf_counter() - start
            
            # Estimate tokens generated
            estimated_tokens = len(response.split())
            
            return {
                "status": "success",
                "prompt_length": len(prompt),
                "response_length": len(response),
                "generation_ms": round(elapsed * 1000, 2),
                "estimated_tok_per_sec": round(estimated_tokens / elapsed, 2) if elapsed > 0 else 0,
                "response_preview": response[:100]
            }
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def _benchmark_e2e(self) -> Dict:
        """Benchmark end-to-end RAG pipeline."""
        logger.info("🎯 Benchmarking End-to-End RAG...")
        
        try:
            from research_os.search.retriever import get_retriever, Chunk
            from research_os.foundation.core import foundation
            
            retriever = get_retriever()
            
            # Add test context
            context_text = """
            Transformers are a type of neural network architecture that uses self-attention mechanisms.
            They were introduced in the paper "Attention is All You Need" by Vaswani et al. in 2017.
            The key innovation is the multi-head attention mechanism that allows the model to attend to 
            different positions and capture various aspects of the input.
            """
            
            test_chunks = [
                Chunk(text=context_text, source="test", chunk_id="context_0")
            ]
            await retriever.add_chunks(test_chunks)
            
            query = "When were transformers introduced?"
            
            # Full E2E: Retrieve + Generate
            start = time.perf_counter()
            
            # Retrieve
            results = await retriever.search(query, top_k=1)
            retrieve_time = time.perf_counter() - start
            
            # Generate
            context = results[0].chunk.text if results else ""
            gen_start = time.perf_counter()
            response = foundation.generate(query, context=context, max_tokens=100)
            gen_time = time.perf_counter() - gen_start
            
            total_time = time.perf_counter() - start
            
            # Cleanup
            retriever.clear()
            
            return {
                "status": "success",
                "retrieve_ms": round(retrieve_time * 1000, 2),
                "generate_ms": round(gen_time * 1000, 2),
                "total_ms": round(total_time * 1000, 2),
                "response_preview": response[:100]
            }
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def _print_summary(self):
        """Print benchmark summary."""
        print("\n" + "="*60)
        print("📊 BENCHMARK RESULTS")
        print("="*60)
        
        targets = {
            "embedding": {"per_text_ms": 50, "label": "Embedding (per text)"},
            "retrieval": {"search_ms": 200, "label": "Retrieval Search"},
            "llm": {"generation_ms": 2000, "label": "LLM Generation"},
            "e2e": {"total_ms": 3000, "label": "E2E RAG"}
        }
        
        for key, target in targets.items():
            result = self.results.get(key, {})
            if result.get("status") == "success":
                metric_key = list(target.keys())[0]
                actual = result.get(metric_key, 0)
                target_val = target[metric_key]
                passed = actual <= target_val
                status = "✅ PASS" if passed else "⚠️ SLOW"
                print(f"{target['label']}: {actual}ms (target: {target_val}ms) {status}")
            else:
                print(f"{target['label']}: ❌ ERROR - {result.get('error', 'Unknown')}")
        
        print("="*60)


async def run_benchmark():
    """Run the benchmark suite."""
    benchmark = Benchmark()
    return await benchmark.run_all()


if __name__ == "__main__":
    asyncio.run(run_benchmark())
