# tests/benchmark_full_pipeline.py
import time
import asyncio
import os
import sys

# Add parent directory to path so we can import modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../jarvis_m4')))

from jarvis_m4.main_v2 import UnifiedPipelineV2

async def monitor_performance():
    """Run pipeline and measure latency"""
    
    # 1. Setup Data
    paper_path = "data/benchmark_paper.txt"
    os.makedirs("data", exist_ok=True)
    with open(paper_path, "w") as f:
        # Generate a reasonable length paper
        f.write("# Introduction\n" + "Scientific research is accelerating.\n" * 50)
        f.write("# Method\n" + "We employ deep learning for extraction.\n" * 50)
        f.write("# Results\n" + "Latency was reduced by 90%.\n" * 50)

    # 2. Init Pipeline
    print("⏳ Initializing Pipeline...")
    start_init = time.time()
    pipeline = UnifiedPipelineV2(backend_type="inmemory")
    print(f"✅ Init took {time.time() - start_init:.2f}s")
    
    # 3. Benchmark Stream
    print("🚀 Starting Benchmark Stream...")
    start_stream = time.time()
    
    claim_count = 0
    first_claim_time = None
    
    async for claim in pipeline.process_paper_stream(paper_path, "bench_001"):
        if first_claim_time is None:
            first_claim_time = time.time() - start_stream
            print(f"⚡ Time to First Token (Claim): {first_claim_time:.3f}s")
        claim_count += 1
        
    total_time = time.time() - start_stream
    print(f"✅ Total Processing Time: {total_time:.3f}s")
    print(f"📊 Claims Processed: {claim_count}")
    print(f"🏎️ Average Time per Claim: {total_time/max(1, claim_count):.3f}s")
    
    # Assertions for CI
    if first_claim_time > 5.0:
        print("❌ FAILED: Time to first claim too slow (>5s)")
        sys.exit(1)
        
    if total_time > 30.0:
        print("❌ FAILED: Total time too slow (>30s)")
        sys.exit(1)
        
    print("✅ BENCHMARK PASSED")

if __name__ == "__main__":
    asyncio.run(monitor_performance())
