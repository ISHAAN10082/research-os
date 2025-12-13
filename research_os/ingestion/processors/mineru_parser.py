"""
MinerU 2.5 PDF Parser - SOTA Document Understanding (Dec 2024)
License: Apache 2.0 (FREE & Open Source)

Benchmarks:
- Outperforms GPT-4o, Gemini 2.5 Pro on OmniDocBench
- 1.2B parameters, runs efficiently on M4
- MLX support for Apple Silicon acceleration
"""
import asyncio
from pathlib import Path
from typing import Optional
from loguru import logger

# Lazy imports to avoid loading heavy models at startup
_MINERU_AVAILABLE = None

def _check_mineru():
    """Check if MinerU is installed."""
    global _MINERU_AVAILABLE
    if _MINERU_AVAILABLE is None:
        try:
            from magic_pdf.data.data_reader_writer import FileBasedDataReader
            _MINERU_AVAILABLE = True
        except ImportError:
            _MINERU_AVAILABLE = False
            logger.warning("MinerU not installed. Run: pip install magic-pdf[full]")
    return _MINERU_AVAILABLE


class MinerUParser:
    """
    MinerU 2.5 - SOTA PDF parsing engine.
    
    Features:
    - Vision-Language Model for document understanding
    - Automatic OCR detection
    - Table extraction → JSON/HTML
    - Formula extraction → LaTeX
    - Image extraction with captions
    - 109-language OCR support
    
    Example:
        parser = MinerUParser()
        result = await parser.parse("paper.pdf")
        print(result["markdown"])
    """
    
    def __init__(self, output_dir: str = "./parsed_output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._initialized = False
        
    def _lazy_init(self):
        """Lazy initialization of heavy MinerU components."""
        if self._initialized:
            return True
            
        if not _check_mineru():
            return False
            
        try:
            from magic_pdf.data.data_reader_writer import FileBasedDataReader, FileBasedDataWriter
            from magic_pdf.model.doc_analyze_by_custom_model import doc_analyze
            from magic_pdf.pipe.UNIPipe import UNIPipe
            from magic_pdf.pipe.OCRPipe import OCRPipe
            from magic_pdf.pipe.TXTPipe import TXTPipe
            
            self.FileBasedDataReader = FileBasedDataReader
            self.FileBasedDataWriter = FileBasedDataWriter
            self.doc_analyze = doc_analyze
            self.UNIPipe = UNIPipe
            self.OCRPipe = OCRPipe
            self.TXTPipe = TXTPipe
            
            self._initialized = True
            logger.info("MinerU 2.5 initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize MinerU: {e}")
            return False
    
    async def parse(self, pdf_path: str, use_ocr: bool = True) -> dict:
        """
        Parse PDF to structured output.
        
        Args:
            pdf_path: Path to the PDF file
            use_ocr: Whether to use OCR for scanned documents
            
        Returns:
            dict with keys:
                - markdown: Full document as markdown
                - content_list: List of content blocks with types
                - images: List of extracted image paths
                - tables: List of extracted tables
                - metadata: Document metadata
        """
        # Run in thread pool to avoid blocking
        return await asyncio.to_thread(self._parse_sync, pdf_path, use_ocr)
    
    def _parse_sync(self, pdf_path: str, use_ocr: bool = True) -> dict:
        """Synchronous parsing implementation."""
        if not self._lazy_init():
            # Fallback to basic extraction if MinerU not available
            return self._fallback_parse(pdf_path)
        
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")
        
        logger.info(f"🔬 MinerU parsing: {pdf_path.name}")
        
        try:
            # Read PDF bytes
            pdf_bytes = pdf_path.read_bytes()
            
            # Create output directory for this PDF
            pdf_output_dir = self.output_dir / pdf_path.stem
            pdf_output_dir.mkdir(parents=True, exist_ok=True)
            
            # Analyze document structure with VLM
            model_json = []
            try:
                model_json = self.doc_analyze(pdf_bytes)
                logger.debug(f"Document analysis complete: {len(model_json)} elements")
            except Exception as e:
                logger.warning(f"VLM analysis failed, using rule-based: {e}")
            
            # Create data writer
            image_writer = self.FileBasedDataWriter(str(pdf_output_dir / "images"))
            
            # Choose pipe based on content
            if use_ocr and self._needs_ocr(pdf_bytes):
                pipe = self.OCRPipe(pdf_bytes, model_json, image_writer)
                logger.info("Using OCR pipeline (scanned document detected)")
            else:
                pipe = self.UNIPipe(pdf_bytes, model_json, image_writer)
                logger.info("Using unified pipeline (native text detected)")
            
            # Execute parsing
            pipe.pipe_classify()
            pipe.pipe_analyze()
            pipe.pipe_parse()
            
            # Extract results
            markdown = pipe.pipe_mk_markdown(str(pdf_output_dir / "images"))
            content_list = pipe.pipe_mk_uni_format(str(pdf_output_dir / "images"))
            
            # Extract tables and images
            images = list((pdf_output_dir / "images").glob("*.png")) if (pdf_output_dir / "images").exists() else []
            tables = [item for item in content_list if item.get("type") == "table"]
            
            result = {
                "markdown": markdown,
                "content_list": content_list,
                "images": [str(img) for img in images],
                "tables": tables,
                "metadata": {
                    "source": str(pdf_path),
                    "title": pdf_path.stem,
                    "parser": "mineru_2.5",
                    "pages": len(model_json) if model_json else "unknown"
                }
            }
            
            logger.info(f"✅ Parsed {pdf_path.name}: {len(result['markdown'])} chars, {len(result['images'])} images, {len(result['tables'])} tables")
            return result
            
        except Exception as e:
            logger.error(f"MinerU parsing failed: {e}")
            return self._fallback_parse(pdf_path)
    
    def _needs_ocr(self, pdf_bytes: bytes) -> bool:
        """Detect if PDF is scanned/needs OCR."""
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            
            # Check first few pages for text
            text_chars = 0
            for page_num in range(min(3, len(doc))):
                page = doc[page_num]
                text_chars += len(page.get_text())
            
            doc.close()
            
            # If very little text, likely scanned
            return text_chars < 100
        except:
            return True  # Default to OCR if detection fails
    
    def _fallback_parse(self, pdf_path: str) -> dict:
        """Fallback parsing when MinerU is not available."""
        logger.warning("Using fallback PDF parser (install magic-pdf for better results)")
        
        pdf_path = Path(pdf_path)
        text = ""
        
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(pdf_path)
            for page in doc:
                text += page.get_text() + "\n\n"
            doc.close()
        except ImportError:
            text = f"[Content of {pdf_path.name} - install PyMuPDF for extraction]"
        except Exception as e:
            text = f"[Failed to extract: {e}]"
        
        return {
            "markdown": text,
            "content_list": [{"type": "text", "content": text}],
            "images": [],
            "tables": [],
            "metadata": {
                "source": str(pdf_path),
                "title": pdf_path.stem,
                "parser": "fallback_pymupdf"
            }
        }


# Convenience function for quick parsing
async def parse_pdf(pdf_path: str, use_ocr: bool = True) -> dict:
    """
    Quick PDF parsing with MinerU 2.5.
    
    Example:
        result = await parse_pdf("paper.pdf")
        print(result["markdown"][:500])
    """
    parser = MinerUParser()
    return await parser.parse(pdf_path, use_ocr)


# Module-level singleton
_parser_instance: Optional[MinerUParser] = None

def get_parser() -> MinerUParser:
    """Get singleton parser instance."""
    global _parser_instance
    if _parser_instance is None:
        _parser_instance = MinerUParser()
    return _parser_instance
