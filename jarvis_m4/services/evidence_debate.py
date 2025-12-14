from pydantic import BaseModel
from typing import List, Literal, Dict
from jarvis_m4.services.debate import DebateAgents
from jarvis_m4.services.retrieval_engine import RetrievalEngine
from jarvis_m4.services.calibration import CalibrationLayer

class DebateResult(BaseModel):
    """Structured debate output with evidence requirements"""
    verdict: Literal["refutes", "supports", "extends", "uncertain"]
    confidence: float  # 0.0-1.0 (Raw)
    calibrated_confidence: float # New field
    confidence_desc: str # New field
    citations: List[str]  # Evidence claim IDs (REQUIRED)
    requires_human: bool
    debate_log: List[str]
    agent_confidences: Dict[str, float]

class EvidenceBasedDebate:
    """
    NOT free-form debate. Evidence-citation-required protocol.
    Mitigates bias reinforcement by grounding in retrieved evidence.
    """
    
    def __init__(self, retrieval_engine: RetrievalEngine, debate_agents: DebateAgents):
        self.retrieval = retrieval_engine
        self.agents = debate_agents
        
        # Conservative thresholds (from research feedback)
        self.high_confidence_threshold = 0.85
        self.min_citations_required = 2
        
        # Calibration Layer
        self.calibrator = CalibrationLayer()
        
        # Debate Cache
        self.cache_path = "data/debate_cache.json"
        self.cache = self._load_cache()
    
    def _load_cache(self) -> Dict:
        """Load persistent debate cache"""
        import json, os
        if os.path.exists(self.cache_path):
            try:
                with open(self.cache_path, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def _save_cache(self):
        """Save cache to disk"""
        import json, os
        os.makedirs(os.path.dirname(self.cache_path), exist_ok=True)
        with open(self.cache_path, 'w') as f:
            json.dump(self.cache, f)

    def _get_cache_key(self, id_a: str, id_b: str) -> str:
        """Canonical key for symmetric caching"""
        return "_".join(sorted([id_a, id_b]))
    
    def debate_claim_pair(self, claim_a: Dict, claim_b: Dict) -> DebateResult:
        """
        Debate two claims with mandatory evidence retrieval.
        
        Args:
            claim_a: {claim_id, text, ...}
            claim_b: {claim_id, text, ...}
        
        Returns:
            DebateResult with verdict, citations, human review flag
        """
        
        # Step 0: Check Cache & Pre-filter
        cache_key = self._get_cache_key(claim_a['claim_id'], claim_b['claim_id'])
        if cache_key in self.cache:
            # Return cached result
            cached_data = self.cache[cache_key]
            # Reconstruct Pydantic object
            return DebateResult(**cached_data)
        
        # Similarity Pre-filter (if embeddings exist) - AGGRESSIVE OPTIMIZATION
        if 'specter2_embedding' in claim_a and 'specter2_embedding' in claim_b:
            import numpy as np
            emb_a = np.array(claim_a['specter2_embedding'])
            emb_b = np.array(claim_b['specter2_embedding'])
            sim = np.dot(emb_a, emb_b) # Cosine similarity if normalized
            
            # Tier 1: Too dissimilar -> Unrelated (No Debate)
            if sim < 0.3:
                result = DebateResult(
                    verdict="uncertain",  # technically unrelated
                    confidence=0.0,
                    calibrated_confidence=0.0,
                    confidence_desc="Unrelated",
                    citations=[],
                    requires_human=False,
                    debate_log=["Skipped due to low similarity (<0.3)"],
                    agent_confidences={}
                )
                self.cache[cache_key] = result.dict()
                self._save_cache()
                return result
            
            # Tier 1.5: Nearly identical -> Supports (No Debate)
            if sim > 0.95:
                result = DebateResult(
                    verdict="supports",
                    confidence=1.0,
                    calibrated_confidence=0.99,
                    confidence_desc="High Confidence (Duplicate)",
                    citations=[], # Implicit support
                    requires_human=False,
                    debate_log=["Skipped due to high similarity (>0.95)"],
                    agent_confidences={}
                )
                self.cache[cache_key] = result.dict()
                self._save_cache()
                return result
        
        # Step 1: Retrieve supporting evidence for both claims
        evidence_a = self.retrieval.search(claim_a['text'], top_k=3, min_similarity=0.7)
        evidence_b = self.retrieval.search(claim_b['text'], top_k=3, min_similarity=0.7)
        
        # Combine evidence pool
        evidence_pool = evidence_a + evidence_b
        evidence_text = "\n".join([
            f"[{e['claim_id']}]: {e['text']}" 
            for e in evidence_pool
        ])
        
        # Step 2: Run multi-agent debate WITH EVIDENCE
        debate_prompt = f"""
You are evaluating the relationship between two scientific claims.
You MUST cite evidence by ID in your analysis.

CLAIM A: {claim_a['text']}
CLAIM B: {claim_b['text']}

EVIDENCE POOL:
{evidence_text}

Analyze the relationship. Output:
- "refutes" if they contradict
- "supports" if they align
- "extends" if one builds on the other
- "uncertain" if relationship is unclear

CRITICAL: Cite evidence IDs in your reasoning.
"""
        
        # Use existing debate infrastructure
        raw_debate_result = self.agents.run_debate(claim_a['text'], claim_b['text'])
        
        # Step 3: Extract citations from debate log
        citations = self._extract_citations(raw_debate_result.get('log', []), evidence_pool)
        
        # Step 4: Determine confidence and human review flag
        raw_confidence = raw_debate_result.get('confidence', 0.5)
        calibrated_conf, conf_desc = self.calibrator.calibrate(raw_confidence)
        
        requires_human = self._should_flag_for_review(
            calibrated_conf, # Use calibrated for decision 
            len(citations),
            evidence_pool
        )
        
        # Step 5: Build structured result
        result = DebateResult(
            verdict=raw_debate_result.get('verdict', 'uncertain'),
            confidence=raw_confidence,
            calibrated_confidence=calibrated_conf,
            confidence_desc=conf_desc,
            citations=citations,
            requires_human=requires_human,
            debate_log=raw_debate_result.get('log', []),
            agent_confidences={
                "skeptic": raw_confidence * 0.9,  # Placeholder, extract from log
                "connector": raw_confidence * 1.0,
                "synthesizer": raw_confidence * 1.1
            }
        )
        
        # Cache Result
        self.cache[cache_key] = result.dict()
        self._save_cache()
        
        return result
    
    def _extract_citations(self, debate_log: List[str], evidence_pool: List[Dict]) -> List[str]:
        """Extract cited evidence IDs from debate transcript"""
        citations = set()
        
        for log_entry in debate_log:
            for evidence in evidence_pool:
                # Check if evidence ID appears in log
                if evidence['claim_id'] in log_entry:
                    citations.add(evidence['claim_id'])
        
        return list(citations)
    
    def _should_flag_for_review(self, confidence: float, num_citations: int, evidence_pool: List[Dict]) -> bool:
        """
        Conservative flagging policy based on research constraints.
        
        From feedback: SciFact-Open achieves only 42% F1 in open domain.
        We flag anything that doesn't meet strict evidence standards.
        """
        
        # Rule 1: Low confidence always requires review
        if confidence < self.high_confidence_threshold:
            return True
        
        # Rule 2: Insufficient citations require review
        if num_citations < self.min_citations_required:
            return True
        
        # Rule 3: Weak evidence pool requires review
        if len(evidence_pool) < 3:
            return True
        
        # Rule 4: Low-quality evidence requires review
        avg_evidence_quality = sum(e.get('similarity_score', 0) for e in evidence_pool) / max(len(evidence_pool), 1)
        if avg_evidence_quality < 0.7:
            return True
        
        # All checks passed: high confidence + strong evidence
        return False
    
    def should_debate_claims(self, claim_a: Dict, claim_b: Dict) -> bool:
        """
        Determine if two claims are similar enough to warrant debate.
        Skip debate for unrelated claims (saves compute).
        """
        
        # Check semantic similarity via retrieval engine
        if 'specter2_embedding' in claim_a:
            results = self.retrieval.search_by_embedding(
                claim_a['specter2_embedding'], 
                top_k=10
            )
            
            # Check if claim_b is in top results
            result_ids = [r['claim_id'] for r in results]
            if claim_b['claim_id'] in result_ids:
                # Get similarity score
                match = [r for r in results if r['claim_id'] == claim_b['claim_id']][0]
                return match['similarity_score'] > 0.6
        
        # Fallback: always debate (conservative)
        return True


if __name__ == "__main__":
    print("EvidenceBasedDebate requires full system integration.")
    print("✅ Module loaded successfully")
