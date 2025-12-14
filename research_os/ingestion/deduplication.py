"""
Deduplication System for Research Papers (Enhanced)

Prevents duplicate papers from being ingested using:
1. File hash-based deduplication (exact duplicates)
2. Title/abstract embedding similarity (near-duplicates)
3. DOI matching
4. arXiv version detection (NEW: handles v1 → v2 updates)

Usage:
    dedup = DeduplicationEngine()
    
    # Check if paper is duplicate
    result = await dedup.check_duplicate(file_path, metadata)
    
    if result.status == DuplicateStatus.EXACT_DUPLICATE:
        print("Already ingested this exact file")
    elif result.status == DuplicateStatus.VERSION_UPDATE:
        print(f"Newer version available: {result.message}")
        # Optionally replace old version
    elif result.status == DuplicateStatus.SEMANTIC_DUPLICATE:
        print("Similar paper already exists")
    else:
        # Proceed with ingestion
        await ingest_paper(file_path)

Environment Variables:
    DEDUP_VALIDATION_MODE: If "true", logs duplicate detections but allows ingestion
"""

import os
import re
import hashlib
import json
from pathlib import Path
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from loguru import logger

# Validation mode - log but don't block
VALIDATION_MODE = os.getenv("DEDUP_VALIDATION_MODE", "false").lower() == "true"

try:
    import numpy as np
    from sklearn.metrics.pairwise import cosine_similarity
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logger.warning("sklearn not available for semantic deduplication")


class DuplicateStatus(Enum):
    """Status of duplicate check"""
    NEW = "new"  # Not a duplicate
    EXACT_DUPLICATE = "exact_duplicate"  # Same file hash
    SEMANTIC_DUPLICATE = "semantic_duplicate"  # Similar content
    DOI_DUPLICATE = "doi_duplicate"  # Same DOI
    VERSION_UPDATE = "version_update"  # Newer version of existing paper (arXiv v2)


@dataclass
class DuplicateResult:
    """Result of duplicate check"""
    status: DuplicateStatus
    existing_id: Optional[str] = None
    similarity_score: Optional[float] = None
    message: str = ""
    should_replace: bool = False  # True if this is a newer version
    version_info: Dict = field(default_factory=dict)  # Version details


class DeduplicationEngine:
    """
    Manages deduplication of research papers.
    
    Stores:
    - File hashes (SHA256)
    - Title/abstract embeddings
    - DOI mappings
    - arXiv IDs with version tracking (NEW)
    """
    
    def __init__(self, storage_path: str = ".dedup_cache"):
        """
        Initialize deduplication engine.
        
        Args:
            storage_path: Directory to store deduplication cache
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True)
        
        # Validation mode flag
        self.validation_mode = VALIDATION_MODE
        if self.validation_mode:
            logger.info("🔍 Deduplication running in VALIDATION MODE (log only)")
        
        # Load existing data
        self.hash_db_path = self.storage_path / "file_hashes.json"
        self.doi_db_path = self.storage_path / "doi_mapping.json"
        self.arxiv_db_path = self.storage_path / "arxiv_mapping.json"  # NEW
        self.embeddings_path = self.storage_path / "embeddings.npz"
        
        self.file_hashes = self._load_json(self.hash_db_path, {})
        self.doi_mapping = self._load_json(self.doi_db_path, {})
        self.arxiv_mapping = self._load_json(self.arxiv_db_path, {})  # NEW
        
        # Load embeddings if they exist
        if self.embeddings_path.exists() and SKLEARN_AVAILABLE:
            data = np.load(self.embeddings_path, allow_pickle=True)
            self.embedding_ids = data['ids'].tolist()
            self.embedding_vectors = data['vectors']
        else:
            self.embedding_ids = []
            self.embedding_vectors = np.array([])
    
    # --- arXiv Version Handling (NEW) ---
    
    def _extract_arxiv_id(self, metadata: Dict) -> Optional[str]:
        """
        Extract arXiv ID from URL or metadata.
        
        Handles:
        - https://arxiv.org/abs/2103.12345
        - https://arxiv.org/pdf/2103.12345v2.pdf
        - metadata['arxiv_id'] = '2103.12345'
        
        Returns:
            arXiv ID with optional version (e.g., '2103.12345v2')
        """
        # Check direct field
        if arxiv_id := metadata.get('arxiv_id'):
            return arxiv_id.strip()
        
        # Check URL
        for field in ['url', 'pdf_url', 'source_url']:
            url = metadata.get(field, '')
            if 'arxiv.org' in url:
                # Match patterns like 2103.12345 or 2103.12345v2
                match = re.search(r'(\d{4}\.\d{4,5})(v\d+)?', url)
                if match:
                    base = match.group(1)
                    version = match.group(2) or ''
                    return f"{base}{version}"
        
        # Check title for arXiv format
        if title := metadata.get('title', ''):
            match = re.search(r'\[arXiv[:\s]*(\d{4}\.\d{4,5})(v\d+)?\]', title, re.IGNORECASE)
            if match:
                return f"{match.group(1)}{match.group(2) or ''}"
        
        return None
    
    def _parse_arxiv_version(self, arxiv_id: str) -> Tuple[str, int]:
        """
        Parse arXiv ID into base ID and version number.
        
        Args:
            arxiv_id: e.g., '2103.12345v2' or '2103.12345'
            
        Returns:
            Tuple of (base_id, version_num) e.g., ('2103.12345', 2)
        """
        if 'v' in arxiv_id:
            match = re.match(r'(.+)v(\d+)$', arxiv_id)
            if match:
                return (match.group(1), int(match.group(2)))
        return (arxiv_id, 1)
    
    def _load_json(self, path: Path, default: Any) -> Any:
        """Load JSON file or return default"""
        if path.exists():
            with open(path) as f:
                return json.load(f)
        return default
    
    def _save_json(self, path: Path, data: Any):
        """Save data to JSON file"""
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def compute_file_hash(self, file_path: str) -> str:
        """
        Compute SHA256 hash of file.
        
        Args:
            file_path: Path to file
            
        Returns:
            str: Hexadecimal hash
        """
        sha256 = hashlib.sha256()
        
        with open(file_path, 'rb') as f:
            while True:
                data = f.read(65536)  # Read in 64kb chunks
                if not data:
                    break
                sha256.update(data)
        
        return sha256.hexdigest()
    
    async def check_duplicate(
        self,
        file_path: str,
        metadata: Optional[Dict[str, Any]] = None,
        embedding: Optional[List[float]] = None,
        similarity_threshold: float = 0.95
    ) -> DuplicateResult:
        """
        Check if paper is a duplicate.
        
        Args:
            file_path: Path to paper file
            metadata: Optional metadata (should include 'doi', 'title', 'url')
            embedding: Optional title/abstract embedding
            similarity_threshold: Cosine similarity threshold for semantic dup
            
        Returns:
            DuplicateResult with status and details
        """
        metadata = metadata or {}
        
        def _apply_validation_mode(result: DuplicateResult) -> DuplicateResult:
            """In validation mode, log but return NEW status"""
            if self.validation_mode and result.status != DuplicateStatus.NEW:
                logger.info(f"[VALIDATION] Would detect: {result.status.value} - {result.message}")
                return DuplicateResult(
                    status=DuplicateStatus.NEW,
                    message=f"[VALIDATION MODE] {result.message}",
                    version_info=result.version_info
                )
            return result
        
        # 1. Check file hash (exact duplicate)
        file_hash = self.compute_file_hash(file_path)
        
        if file_hash in self.file_hashes:
            existing_id = self.file_hashes[file_hash]
            logger.info(f"Exact duplicate found: {existing_id}")
            return _apply_validation_mode(DuplicateResult(
                status=DuplicateStatus.EXACT_DUPLICATE,
                existing_id=existing_id,
                message=f"Exact duplicate of {existing_id}"
            ))
        
        # 2. Check DOI (if available)
        doi = metadata.get('doi')
        if doi and doi in self.doi_mapping:
            existing_id = self.doi_mapping[doi]
            logger.info(f"DOI duplicate found: {doi}")
            return _apply_validation_mode(DuplicateResult(
                status=DuplicateStatus.DOI_DUPLICATE,
                existing_id=existing_id,
                message=f"DOI {doi} already exists as {existing_id}"
            ))
        
        # 3. Check arXiv version (NEW!)
        arxiv_id = self._extract_arxiv_id(metadata)
        if arxiv_id:
            base_id, new_version = self._parse_arxiv_version(arxiv_id)
            
            if base_id in self.arxiv_mapping:
                existing_data = self.arxiv_mapping[base_id]
                existing_id = existing_data['paper_id']
                existing_version = existing_data.get('version', 1)
                
                if new_version > existing_version:
                    # This is a newer version!
                    logger.info(f"arXiv version update: {base_id} v{existing_version} → v{new_version}")
                    return _apply_validation_mode(DuplicateResult(
                        status=DuplicateStatus.VERSION_UPDATE,
                        existing_id=existing_id,
                        message=f"Newer arXiv version: v{existing_version} → v{new_version}",
                        should_replace=True,
                        version_info={
                            'arxiv_id': base_id,
                            'old_version': existing_version,
                            'new_version': new_version,
                            'old_paper_id': existing_id
                        }
                    ))
                else:
                    # Same or older version
                    logger.info(f"arXiv: Same or older version {arxiv_id}")
                    return _apply_validation_mode(DuplicateResult(
                        status=DuplicateStatus.EXACT_DUPLICATE,
                        existing_id=existing_id,
                        message=f"arXiv {base_id} v{existing_version} already exists"
                    ))
        
        # 3. Check semantic similarity (if embedding provided)
        if embedding and SKLEARN_AVAILABLE and len(self.embedding_vectors) > 0:
            # Compute similarity to all existing embeddings
            embedding_array = np.array([embedding])
            similarities = cosine_similarity(
                embedding_array,
                self.embedding_vectors
            )[0]
            
            max_sim_idx = np.argmax(similarities)
            max_similarity = similarities[max_sim_idx]
            
            if max_similarity >= similarity_threshold:
                existing_id = self.embedding_ids[max_sim_idx]
                logger.info(
                    f"Semantic duplicate found: {existing_id} "
                    f"(similarity: {max_similarity:.3f})"
                )
                return DuplicateResult(
                    status=DuplicateStatus.SEMANTIC_DUPLICATE,
                    existing_id=existing_id,
                    similarity_score=float(max_similarity),
                    message=f"Similar to {existing_id} (sim: {max_similarity:.3f})"
                )
        
        # Not a duplicate
        return DuplicateResult(
            status=DuplicateStatus.NEW,
            message="New paper, no duplicates found"
        )
    
    async def register_paper(
        self,
        paper_id: str,
        file_path: str,
        metadata: Optional[Dict[str, Any]] = None,
        embedding: Optional[List[float]] = None
    ):
        """
        Register a paper after successful ingestion.
        
        Args:
            paper_id: Unique ID for this paper
            file_path: Path to paper file
            metadata: Optional metadata (should include 'doi', 'url' for arXiv)
            embedding: Optional title/abstract embedding
        """
        metadata = metadata or {}
        
        # Register file hash
        file_hash = self.compute_file_hash(file_path)
        self.file_hashes[file_hash] = paper_id
        self._save_json(self.hash_db_path, self.file_hashes)
        
        # Register DOI
        doi = metadata.get('doi')
        if doi:
            self.doi_mapping[doi] = paper_id
            self._save_json(self.doi_db_path, self.doi_mapping)
        
        # Register arXiv ID with version (NEW!)
        arxiv_id = self._extract_arxiv_id(metadata)
        if arxiv_id:
            base_id, version = self._parse_arxiv_version(arxiv_id)
            self.arxiv_mapping[base_id] = {
                'paper_id': paper_id,
                'version': version,
                'registered_at': datetime.now().isoformat()
            }
            self._save_json(self.arxiv_db_path, self.arxiv_mapping)
            logger.info(f"Registered arXiv {base_id} v{version}")
        
        # Register embedding
        if embedding and SKLEARN_AVAILABLE:
            self.embedding_ids.append(paper_id)
            
            embedding_array = np.array([embedding])
            
            if len(self.embedding_vectors) == 0:
                self.embedding_vectors = embedding_array
            else:
                self.embedding_vectors = np.vstack([
                    self.embedding_vectors,
                    embedding_array
                ])
            
            # Save embeddings
            np.savez_compressed(
                self.embeddings_path,
                ids=np.array(self.embedding_ids),
                vectors=self.embedding_vectors
            )
        
        logger.info(f"Registered paper: {paper_id}")
    
    def remove_paper(self, paper_id: str):
        """
        Remove a paper from deduplication cache.
        
        Args:
            paper_id: ID of paper to remove
        """
        # Remove from hash mapping
        self.file_hashes = {
            h: pid for h, pid in self.file_hashes.items()
            if pid != paper_id
        }
        self._save_json(self.hash_db_path, self.file_hashes)
        
        # Remove from DOI mapping
        self.doi_mapping = {
            doi: pid for doi, pid in self.doi_mapping.items()
            if pid != paper_id
        }
        self._save_json(self.doi_db_path, self.doi_mapping)
        
        # Remove from embeddings
        if paper_id in self.embedding_ids:
            idx = self.embedding_ids.index(paper_id)
            self.embedding_ids.pop(idx)
            self.embedding_vectors = np.delete(
                self.embedding_vectors,
                idx,
                axis=0
            )
            
            if len(self.embedding_ids) > 0:
                np.savez_compressed(
                    self.embeddings_path,
                    ids=np.array(self.embedding_ids),
                    vectors=self.embedding_vectors
                )
        
        logger.info(f"Removed paper from dedup cache: {paper_id}")
    
    def get_stats(self) -> Dict[str, int]:
        """Get deduplication statistics"""
        return {
            'total_hashes': len(self.file_hashes),
            'total_dois': len(self.doi_mapping),
            'total_embeddings': len(self.embedding_ids)
        }


# Example usage
if __name__ == "__main__":
    import asyncio
    
    async def test_deduplication():
        dedup = DeduplicationEngine(storage_path=".test_dedup")
        
        # Simulate checking a paper
        result = await dedup.check_duplicate(
            "test_paper.pdf",
            metadata={'doi': '10.1234/test', 'title': 'Test Paper'},
            embedding=[0.1] * 768  # Dummy embedding
        )
        
        print(f"Status: {result.status}")
        print(f"Message: {result.message}")
        
        if result.status == DuplicateStatus.NEW:
            # Register the paper
            await dedup.register_paper(
                paper_id="paper_001",
                file_path="test_paper.pdf",
                metadata={'doi': '10.1234/test'},
                embedding=[0.1] * 768
            )
            print("Paper registered")
        
        # Check again - should be duplicate
        result2 = await dedup.check_duplicate(
            "test_paper.pdf",
            metadata={'doi': '10.1234/test'},
            embedding=[0.1] * 768
        )
        print(f"\nSecond check - Status: {result2.status}")
        
        print(f"\nStats: {dedup.get_stats()}")
    
    asyncio.run(test_deduplication())
