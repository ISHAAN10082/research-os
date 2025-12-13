import asyncio
from pathlib import Path
from research_os.ingestion.router import input_router, ResearchType
from research_os.ingestion.processors.paper import paper_processor
from research_os.ingestion.processors.voice import voice_processor
from loguru import logger

class IngestionHydra:
    """
    Parallel Ingestion Engine.
    'Cut off one head, two more grow' -> Handles massive file streams.
    """
    
    async def ingest_file(self, file_path: str):
        """Route and process a single file."""
        path = Path(file_path)
        try:
            r_type = input_router.route(str(path))
            logger.info(f"Hydra detected {r_type.value} for {path.name}")
            
            if r_type == ResearchType.PAPER:
                # Run CPU-bound task in executor
                return await asyncio.to_thread(paper_processor.process, path)
                
            elif r_type == ResearchType.VOICE:
                return await asyncio.to_thread(voice_processor.process, path)
                
            elif r_type == ResearchType.CODE:
                logger.warning("Code processor not yet implemented.")
                return None
                
            else:
                logger.warning(f"Unknown type for {path.name}")
                return None
                
        except Exception as e:
            logger.error(f"Hydra failed on {path.name}: {e}")
            return None

    async def ingest_directory(self, dir_path: str):
        """Process a directory in parallel."""
        tasks = []
        for f in Path(dir_path).rglob("*"):
            if f.is_file():
                tasks.append(self.ingest_file(str(f)))
        
        results = await asyncio.gather(*tasks)
        return [r for r in results if r]

hydra = IngestionHydra()
