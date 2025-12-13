"""
Paper Processor - SOTA PDF Ingestion Pipeline (Dec 2024)
Uses MinerU 2.5 for document understanding.
"""
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any
from loguru import logger

from research_os.ingestion.processors.mineru_parser import get_parser, MinerUParser
from research_os.foundation.core import foundation
from research_os.search.retriever import get_retriever, Chunk


class PaperProcessor:
    """
    SOTA Paper Processing Pipeline.
    
    1. Parse PDF with MinerU 2.5 (vision-language model)
    2. Extract text, tables, images, formulas
    3. Chunk with overlap for retrieval
    4. Index in hybrid retriever (dense + sparse)
    5. Add to knowledge graph
    
    Example:
        processor = PaperProcessor()
        result = await processor.process("paper.pdf")
    """
    
    def __init__(self):
        self.parser: MinerUParser = get_parser()
        self.retriever = get_retriever()
    
    async def process(self, file_path: Path) -> Dict[str, Any]:
        """
        Full paper ingestion pipeline.
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            dict with processing results and metadata
        """
        file_path = Path(file_path)
        logger.info(f"📄 Processing Paper: {file_path.name}")
        
        try:
            # 1. Parse with MinerU 2.5
            parsed = await self.parser.parse(str(file_path))
            markdown = parsed.get("markdown", "")
            
            if not markdown.strip():
                logger.warning(f"No content extracted from {file_path.name}")
                return {"status": "empty", "source": str(file_path)}
            
            # 2. Add to retrieval index
            await self.retriever.add_document(
                source=str(file_path),
                text=markdown,
                chunk_size=512,
                chunk_overlap=128
            )
            
            # 3. Add to knowledge graph
            await self._add_to_graph(file_path, parsed)
            
            # 4. Generate summary embedding (for fast lookup)
            summary_embedding = foundation.vector.embed_document(markdown[:2000])
            
            result = {
                "status": "success",
                "source": str(file_path),
                "title": file_path.stem,
                "content_length": len(markdown),
                "images_count": len(parsed.get("images", [])),
                "tables_count": len(parsed.get("tables", [])),
                "embedding": summary_embedding,
                "parser": parsed.get("metadata", {}).get("parser", "unknown")
            }
            
            logger.info(f"✅ Processed {file_path.name}: {result['content_length']} chars")
            return result
            
        except Exception as e:
            logger.error(f"Paper processing failed: {e}")
            return {"status": "error", "source": str(file_path), "error": str(e)}
    
    async def _add_to_graph(self, file_path: Path, parsed: Dict):
        """Add paper metadata to knowledge graph."""
        try:
            title = file_path.stem
            abstract = parsed.get("markdown", "")[:500]  # First 500 chars as abstract
            
            # Create paper node
            foundation.graph.execute(
                "MERGE (p:Paper {title: $title}) SET p.abstract = $abs, p.path = $path", 
                {"title": title, "abs": abstract, "path": str(file_path)}
            )
            
            logger.debug(f"Added {title} to knowledge graph")
            
        except Exception as e:
            logger.warning(f"Graph update failed: {e}")
    
    def process_sync(self, file_path: Path) -> Dict[str, Any]:
        """Synchronous wrapper for process()."""
        return asyncio.run(self.process(file_path))


# Singleton instance
_processor: Optional[PaperProcessor] = None

def get_paper_processor() -> PaperProcessor:
    """Get or create singleton paper processor."""
    global _processor
    if _processor is None:
        _processor = PaperProcessor()
    return _processor

# Backward compatibility
paper_processor = property(lambda self: get_paper_processor())

# For backward compat import
class _PaperProcessorModule:
    @property
    def paper_processor(self):
        return get_paper_processor()

import sys
sys.modules[__name__].__class__ = type(
    'PaperProcessorModule', 
    (type(sys.modules[__name__]),), 
    {'paper_processor': property(lambda self: get_paper_processor())}
)

