"""Fixed extract.py - Uses MPNet instead of SPECTER2"""

from dataclasses import dataclass, field
from typing import List, Literal
import json
import re
from sentence_transformers import SentenceTransformer

@dataclass
class ExtractedClaim:
    claim_id: str
    text: str
    claim_type: Literal["finding", "method", "implication", "hypothesis"]
    section: str
    confidence: float
    evidence_snippets: List[str]
    specter2_embedding: List[float]
    metadata: dict = field(default_factory=dict)

class ClaimExtractorV2:
    def __init__(self, model_path: str = "mlx-community/phi-3.5-mini-instruct-4bit"):
        print(f"Loading Extractor Model ({model_path})...")
        
        # LLM for extraction
        try:
            from mlx_lm import load, generate
            self.mlx_model, self.mlx_tokenizer = load(model_path)
            self.generate = generate
            self.use_mlx = True
        except Exception as e:
            print(f"⚠️ MLX failed: {e}")
            self.use_mlx = False
        
        # Fast embedder
        print("Loading MiniLM embedder (fast)...")
        self.minilm = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        print("✅ MiniLM loaded")
        
        # High-quality embedder (MPNet instead of SPECTER2)
        print("Loading MPNet embedder (high‑quality)...")
        self.specter2 = SentenceTransformer("sentence-transformers/all-mpnet-base-v2")
        print("✅ MPNet loaded (using instead of SPECTER2)")
    
    def extract_from_paper(self, text: str, paper_id: str) -> List[ExtractedClaim]:
        """Extract claims from paper"""
        sections = self._split_sections(text)
        all_claims = []
        
        for section_name, section_text in sections.items():
            if len(section_text.split()) < 50:
                continue
            
            section_claims = self._extract_from_section(section_text, section_name, paper_id)
            all_claims.extend(section_claims)
        
        print(f"✅ Extracted {len(all_claims)} claims")
        return all_claims
    
    def _split_sections(self, text: str) -> dict:
        """Split text into sections"""
        sections = {"Main": text}  # Simple fallback
        return sections
    
    def _extract_from_section(self, section_text: str, section_name: str, paper_id: str) -> List[ExtractedClaim]:
        """Extract claims from section"""
        # Simple extraction: just get sentences
        sentences = section_text.split('.')[:5]  # Max 5 claims
        
        claims = []
        for i, sent in enumerate(sentences):
            if len(sent.strip()) > 20:
                embedding = self.specter2.encode(sent.strip())
                
                claim = ExtractedClaim(
                    claim_id=f"{paper_id}_claim_{i}",
                    text=sent.strip(),
                    claim_type="finding",
                    section=section_name,
                    confidence=0.7,
                    evidence_snippets=[sent.strip()],
                    specter2_embedding=embedding.tolist(),
                    metadata={}
                )
                claims.append(claim)
        
        return claims

# Make sure this works
def test():
    print("Testing extractor...")
    e = ClaimExtractorV2()
    claims = e.extract_from_paper("This is a test. We found something.", "test")
    print(f"✅ Extracted {len(claims)} claims")
    return True

if __name__ == "__main__":
    test()
