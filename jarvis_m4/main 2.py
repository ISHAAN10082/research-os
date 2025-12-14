import asyncio
import os
import sys
import logging
from typing import Dict, Any, List

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("jarvis_pipeline_v2.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("ResearchOS_V2")

# Import V2 Services
# from jarvis_m4.services.graph_backend import create_backend (Moved to __init__)
from jarvis_m4.services.schema import UnifiedSchema
from jarvis_m4.services.extract import ClaimExtractorV2
from jarvis_m4.services.retrieval_engine import RetrievalEngine
from jarvis_m4.services.evidence_debate import EvidenceBasedDebate
from jarvis_m4.services.debate import DebateAgents
from jarvis_m4.services.causal_graph import CausalGraphV2
from jarvis_m4.services.palace import MemoryPalaceV2
from jarvis_m4.services.scene import SceneGenerator
from jarvis_m4.services.reporter import ResearchReporter

class UnifiedPipelineV2:
    def __init__(self, backend_type: str = "kuzu"):
        logger.info("🚀 Initializing ResearchOS 3.0 V2 Unified Pipeline...")
        
        try:
            # Graph backend (abstracted for migration)
            from jarvis_m4.services.graph_backend import create_backend
            self.graph_backend = create_backend(backend_type, db_path="data/research_v2.kuzu")
            logger.info(f"✅ Graph backend: {backend_type}")
            
            # Extraction with SPECTER2
            self.extractor = ClaimExtractorV2()
            logger.info("✅ ClaimExtractorV2 loaded")
            
            # Retrieval with FAISS + SPECTER2
            self.retrieval = RetrievalEngine()
            logger.info("✅ RetrievalEngine loaded")
            
            # Debate agents (legacy, for evidence_debate)
            self.debate_agents = DebateAgents()
            logger.info("✅ DebateAgents loaded")
            
            # Evidence-based debate
            self.evidence_debate = EvidenceBasedDebate(self.retrieval, self.debate_agents)
            logger.info("✅ EvidenceBasedDebate loaded")
            
            # Causal graph with NetworkX
            self.graph = CausalGraphV2(self.graph_backend, self.evidence_debate)
            logger.info("✅ CausalGraphV2 loaded")
            
            # Memory palace with SPECTER2
            self.palace = MemoryPalaceV2(schema=None)
            logger.info("✅ MemoryPalaceV2 loaded")
            
            # Scene generator
            self.scene_gen = SceneGenerator()
            logger.info("✅ SceneGenerator loaded")
            
            # Reporter
            self.reporter = ResearchReporter()
            logger.info("✅ Reporter loaded")
            
            logger.info("✅ All V2 services initialized successfully")
            
        except Exception as e:
            logger.critical(f"❌ Fatal Initialization Error: {e}")
            raise e

    async def process_paper_stream(self, paper_path: str, paper_id: str):
        """
        Async Generator: Yields claims as they are processed (streamed).
        Aggressive Optimization: Extracts, fast-embeds, indexes, and debates in parallel.
        """
        logger.info(f"📄 Streaming Processing: {paper_id} ({paper_path})")
        
        # 1. Ingestion
        try:
            import fitz
            doc = fitz.open(paper_path)
            text = ""
            for page in doc:
                text += page.get_text()
            logger.info(f"✅ Extracted {len(text)} chars from PDF")
        except Exception as e:
            logger.error(f"❌ PDF Read Failed: {e}. Trying text read...")
            try:
                with open(paper_path, 'r', errors='ignore') as f:
                    text = f.read()
            except:
                logger.error("❌ Fatal: Could not read file.")
                return

        # 2. Extract Claims (I/O Bound - simulated as blocking here but fast)
        # Note: Extractor is sync for now, but could be threaded
        try:
            logger.info("🔍 Extracting claims...")
            extracted_claims = await asyncio.to_thread(self.extractor.extract_from_paper, text, paper_id)
            if not extracted_claims:
                logger.warning("⚠️ No claims extracted.")
                return
        except Exception as e:
            logger.error(f"❌ Extraction Failed: {e}")
            return

        # 3. Batch Embed (Fast Stage with MiniLM, already happened in extract_from_paper)
        # Claims already have 'specter2_embedding' populated (actually MiniLM ebd)
        
        # 4. Stream Results & Fire-and-Forget Indexing/Debate
        
        # Prepare Batch Indexing
        claim_dicts = []
        for c in extracted_claims:
            c_dict = c.dict()
            c_dict['claim_id'] = f"{paper_id}_{hash(c_dict['text'])%100000}" # Reduced collision risk
            c_dict['paper_id'] = paper_id
            claim_dicts.append(c_dict)
        
        # Bulk Index (Fast)
        try:
            for cd in claim_dicts:
                self.retrieval.index_claim(
                    cd['claim_id'],
                    cd['specter2_embedding'],
                    cd
                )
        except Exception as e:
             logger.error(f"❌ Indexing Failed: {e}")
        
        # Fire Debate Tasks (Async)
        debate_tasks = []
        for i, c_dict in enumerate(claim_dicts):
            # Yield back to UI/Caller immediately
            yield c_dict
            
            # Start Debate in Background
            task = asyncio.create_task(self._async_debate_claim(c_dict))
            debate_tasks.append(task)
            
        # Wait for debates to finish (optional, or let them run)
        # For this pipeline, we await them to ensure completion before reporting
        if debate_tasks:
            await asyncio.gather(*debate_tasks)
            
        logger.info(f"🏁 Paper {paper_id} Processing Complete.")

    async def _async_debate_claim(self, c_dict):
        """Helper to run debate logic async without blocking main stream"""
        try:
            # Find similar
            similar_claims = self.retrieval.search_by_embedding(
                c_dict['specter2_embedding'],
                top_k=5,
                min_similarity=0.6
            )
            
            for similar in similar_claims[:2]:
                if similar['claim_id'] == c_dict['claim_id']: continue
                
                # Check cache/should debate (sync check is fast)
                if self.evidence_debate.should_debate_claims(c_dict, similar['metadata']):
                    # Run debate (can be slow, run in thread if LLM is blocking)
                    # Note: debate_claim_pair calls LLM which might be blocking. 
                    # Ideally, run_debate should be async. Wrapping in to_thread.
                    result = await asyncio.to_thread(
                        self.evidence_debate.debate_claim_pair, c_dict, similar['metadata']
                    )
                    
                    # Add to graph
                    self.graph.add_relationship(
                        c_dict['claim_id'],
                        similar['claim_id'],
                        result.dict()
                    )
        except Exception as e:
            logger.error(f"background debate error: {e}")

async def main():
    """Example usage of V2 async pipeline"""
    
    pipeline = UnifiedPipelineV2(backend_type="inmemory")  # Use inmemory for quick test
    
    # Create dummy file if not exists
    os.makedirs("data", exist_ok=True)
    if not os.path.exists("data/test_paper_v2.txt"):
        with open("data/test_paper_v2.txt", "w") as f:
            f.write("""
## Method
We used a transformer-based architecture with self-attention mechanisms.
The model achieved 95% accuracy on the validation set.

## Results
Our approach outperforms all baselines by a significant margin.
The method shows strong generalization across domains.

## Discussion
These findings suggest that attention mechanisms are crucial for performance.
However, computational cost remains a concern for large-scale deployment.
""")
            
    print("🚀 Starting Stream Processing...")
    
    async for claim in pipeline.process_paper_stream("data/test_paper_v2.txt", "paper_v2_001"):
        print(f"  ⚡ Yielded Claim: {claim['text'][:50]}... (Type: {claim['claim_type']})")
    
    print("✅ V2 PIPELINE STREAM TEST FINISHED")

if __name__ == "__main__":
    asyncio.run(main())
