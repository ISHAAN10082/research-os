"""
ColPali Multimodal Indexer - Vision-First Document Retrieval (Dec 2024)
License: MIT (FREE & Open Source)

SOTA Features:
- Treats PDF pages as images (no OCR pipeline needed)
- Late interaction with multi-vector per page
- #1 on ViDoRe benchmark for visual document retrieval
- Captures tables, figures, layouts that text-only misses
"""
import asyncio
from pathlib import Path
from typing import List, Optional, Union
import numpy as np
from loguru import logger

# Lazy loading
_COLPALI_MODEL = None
_COLPALI_PROCESSOR = None
_COLPALI_AVAILABLE = None


def _check_colpali():
    """Check if ColPali dependencies are available."""
    global _COLPALI_AVAILABLE
    if _COLPALI_AVAILABLE is None:
        try:
            import torch
            from PIL import Image
            _COLPALI_AVAILABLE = True
        except ImportError:
            _COLPALI_AVAILABLE = False
            logger.warning("ColPali requires torch and PIL. Run: pip install torch pillow")
    return _COLPALI_AVAILABLE


class ColPaliIndexer:
    """
    ColPali - SOTA multimodal document retrieval.
    
    Key Innovation: Instead of extracting text from PDFs, ColPali:
    1. Converts each page to an image
    2. Encodes the image using a Vision-Language Model
    3. Returns multiple vectors per page (one per image patch)
    4. Uses late interaction (MaxSim) for fine-grained matching
    
    This captures visual elements (tables, figures, layout) that
    traditional text extraction misses.
    
    Example:
        indexer = ColPaliIndexer()
        embeddings = await indexer.index_pdf("paper.pdf")
        results = await indexer.search("attention mechanism diagram", embeddings)
    """
    
    def __init__(self, model_name: str = "vidore/colpali-v1.2"):
        self.model_name = model_name
        self.device = self._get_device()
        self._model = None
        self._processor = None
        self._initialized = False
    
    def _get_device(self) -> str:
        """Detect best available device."""
        try:
            import torch
            if torch.backends.mps.is_available():
                return "mps"
            elif torch.cuda.is_available():
                return "cuda"
        except ImportError:
            pass
        return "cpu"
    
    def _lazy_init(self):
        """Lazy load ColPali model."""
        if self._initialized:
            return True
            
        if not _check_colpali():
            return False
        
        logger.info(f"Loading ColPali model: {self.model_name}")
        
        try:
            import torch
            from colpali_engine.models import ColPali, ColPaliProcessor
            
            self._model = ColPali.from_pretrained(
                self.model_name,
                torch_dtype=torch.float16 if self.device != "cpu" else torch.float32,
                device_map=self.device
            ).eval()
            
            self._processor = ColPaliProcessor.from_pretrained(self.model_name)
            
            self._initialized = True
            logger.info(f"✅ ColPali loaded on {self.device}")
            return True
            
        except ImportError:
            logger.warning("colpali-engine not installed. Run: pip install colpali-engine")
            return False
        except Exception as e:
            logger.error(f"Failed to load ColPali: {e}")
            return False
    
    async def index_pdf(self, pdf_path: str, max_pages: int = 50) -> List[dict]:
        """
        Index a PDF by converting pages to images and encoding.
        
        Args:
            pdf_path: Path to PDF file
            max_pages: Maximum pages to index (memory constraint)
            
        Returns:
            List of dicts with page embeddings and metadata
        """
        return await asyncio.to_thread(self._index_pdf_sync, pdf_path, max_pages)
    
    def _index_pdf_sync(self, pdf_path: str, max_pages: int = 50) -> List[dict]:
        """Synchronous PDF indexing."""
        if not self._lazy_init():
            return self._fallback_index(pdf_path)
        
        import torch
        from PIL import Image
        
        pdf_path = Path(pdf_path)
        logger.info(f"📄 ColPali indexing: {pdf_path.name}")
        
        # Convert PDF pages to images
        images = self._pdf_to_images(pdf_path, max_pages)
        
        if not images:
            logger.warning(f"No images extracted from {pdf_path.name}")
            return []
        
        indexed_pages = []
        
        for page_num, img in enumerate(images):
            try:
                # Process image
                inputs = self._processor(images=[img], return_tensors="pt").to(self.device)
                
                # Generate embeddings
                with torch.no_grad():
                    embeddings = self._model(**inputs)
                
                # Convert to numpy for storage
                page_embedding = embeddings[0].cpu().numpy()
                
                indexed_pages.append({
                    "page_num": page_num,
                    "embedding": page_embedding,  # Shape: [num_patches, embed_dim]
                    "source": str(pdf_path),
                    "num_patches": page_embedding.shape[0]
                })
                
            except Exception as e:
                logger.error(f"Failed to index page {page_num}: {e}")
                continue
        
        logger.info(f"✅ Indexed {len(indexed_pages)} pages from {pdf_path.name}")
        return indexed_pages
    
    def _pdf_to_images(self, pdf_path: Path, max_pages: int) -> List:
        """Convert PDF pages to PIL Images."""
        from PIL import Image
        
        try:
            import fitz  # PyMuPDF
            
            doc = fitz.open(pdf_path)
            images = []
            
            for page_num in range(min(len(doc), max_pages)):
                page = doc[page_num]
                # Render at 150 DPI for good quality without excessive memory
                pix = page.get_pixmap(dpi=150)
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                images.append(img)
            
            doc.close()
            return images
            
        except ImportError:
            logger.error("PyMuPDF required for PDF rendering. Run: pip install pymupdf")
            return []
        except Exception as e:
            logger.error(f"Failed to render PDF: {e}")
            return []
    
    async def search(
        self, 
        query: str, 
        page_embeddings: List[dict], 
        top_k: int = 5
    ) -> List[dict]:
        """
        Search indexed pages using late interaction.
        
        Args:
            query: Search query
            page_embeddings: List from index_pdf()
            top_k: Number of results to return
            
        Returns:
            List of results with scores and page info
        """
        return await asyncio.to_thread(self._search_sync, query, page_embeddings, top_k)
    
    def _search_sync(
        self, 
        query: str, 
        page_embeddings: List[dict], 
        top_k: int = 5
    ) -> List[dict]:
        """Synchronous search."""
        if not self._lazy_init():
            # Fallback: return all pages with equal score
            return [{"page_num": p["page_num"], "score": 1.0, "source": p["source"]} 
                    for p in page_embeddings[:top_k]]
        
        import torch
        
        # Encode query
        query_inputs = self._processor(text=[query], return_tensors="pt").to(self.device)
        
        with torch.no_grad():
            query_embedding = self._model.get_text_embeddings(**query_inputs)
        
        query_emb = query_embedding[0].cpu().numpy()  # Shape: [num_tokens, embed_dim]
        
        # Compute MaxSim scores
        results = []
        
        for page in page_embeddings:
            page_emb = page["embedding"]  # Shape: [num_patches, embed_dim]
            
            # Late interaction: for each query token, find max similarity with any patch
            # Then sum across all query tokens
            similarity_matrix = np.matmul(query_emb, page_emb.T)  # [query_tokens, patches]
            max_sims = similarity_matrix.max(axis=1)  # [query_tokens]
            score = float(max_sims.sum())
            
            results.append({
                "page_num": page["page_num"],
                "score": score,
                "source": page["source"],
                "num_patches": page["num_patches"]
            })
        
        # Sort by score descending
        results.sort(key=lambda x: x["score"], reverse=True)
        
        return results[:top_k]
    
    def _fallback_index(self, pdf_path: str) -> List[dict]:
        """Fallback when ColPali is not available."""
        logger.warning("ColPali not available, using text-based fallback")
        
        # Return empty - retriever will use text embeddings instead
        return []
    
    async def index_image(self, image_path: str) -> Optional[np.ndarray]:
        """Index a single image (for figures, screenshots, etc.)."""
        return await asyncio.to_thread(self._index_image_sync, image_path)
    
    def _index_image_sync(self, image_path: str) -> Optional[np.ndarray]:
        """Synchronous image indexing."""
        if not self._lazy_init():
            return None
        
        import torch
        from PIL import Image
        
        try:
            img = Image.open(image_path).convert("RGB")
            inputs = self._processor(images=[img], return_tensors="pt").to(self.device)
            
            with torch.no_grad():
                embeddings = self._model(**inputs)
            
            return embeddings[0].cpu().numpy()
            
        except Exception as e:
            logger.error(f"Failed to index image: {e}")
            return None


# Singleton instance
_colpali_indexer: Optional[ColPaliIndexer] = None

def get_colpali_indexer() -> ColPaliIndexer:
    """Get or create singleton ColPali indexer."""
    global _colpali_indexer
    if _colpali_indexer is None:
        _colpali_indexer = ColPaliIndexer()
    return _colpali_indexer
