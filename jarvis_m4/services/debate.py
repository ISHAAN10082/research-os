from langgraph.graph import StateGraph, END
from typing import TypedDict, List, Optional
import mlx.core as mx
from mlx_lm import generate
import json
import os

# Define the state passed between agents
class DebateState(TypedDict):
    claim_a: str
    claim_b: str
    debate_history: List[str]
    verdict: str
    confidence: float
    explanation: str

class DebateAgents:
    """
    Three specialized roles (all Phi-3.5 with different system prompts).
    Designed to maximize perspective diversity without hallucination.
    Optimized for M4: Serial execution, single model loaded.
    """
    
    
    def __init__(self, model_path: str = "mlx-community/phi-3.5-mini-instruct-4bit"):
        # Allow override via env var
        env_model_path = os.getenv("DEBATE_MODEL_PATH")
        if env_model_path:
            model_path = env_model_path
            
        print(f"Loading Debate Model ({model_path})...")
        # Load model via cache (shared with Extractor)
        from research_os.foundation.model_cache import get_phi35
        self.model, self.tokenizer = get_phi35()
        
    def _generate_response(self, system_prompt: str, user_prompt: str, max_tokens: int = 150, temp: float = 0.7) -> str:
        """Helper for formatted generation"""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        text = self.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        return generate(
            self.model,
            self.tokenizer,
            prompt=text,
            max_tokens=max_tokens,
            temp=temp,
            verbose=False
        )

    # --- AGENT DEFINITIONS ---

    def agent_methodologist(self, state: DebateState) -> DebateState:
        """Role: Assess study rigor, sample size, and statistical power."""
        print("📐 Methodologist analyzing...")
        system = "You are a rigid Methodologist. You ignore the conclusion and focus ONLY on the study design, sample size, and p-hacking risks."
        prompt = f"""
Evaluate the methodology implied in these claims:
CLAIM A: {state['claim_a']}
CLAIM B: {state['claim_b']}

Detect:
1. Implicit sample size warnings (e.g. "case study", "preliminary")
2. Generalization overreach
3. Causal claims from observational language

Output critique.
"""
        response = self._generate_response(system, prompt, 150, 0.1)
        state['debate_history'].append(f"METHODOLOGIST: {response}")
        return state

    def agent_skeptic(self, state: DebateState) -> DebateState:
        """Role: Find flaws, weaknesses, confounds."""
        print("🤔 Skeptic analyzing...")
        system = "You are a professional Skeptic. Your goal is to find logical gaps and alternative explanations."
        prompt = f"""
Evaluate this claim:
CLAIM: {state['claim_a']}
Context: {state.get('claim_b', 'No alternative provided')}

Identify: 
1. Statistical weaknesses 
2. Methodological flaws 
3. Alternative explanations
Keep it brief (max 100 words).
"""
        response = self._generate_response(system, prompt, 200, 0.3)
        state['debate_history'].append(f"SKEPTIC: {response}")
        return state
    
    def agent_connector(self, state: DebateState) -> DebateState:
        """Role: Find unexpected connections, cross-domain relevance."""
        print("🔗 Connector analyzing...")
        system = "You are a lateral thinker. Your goal is to find analogous structures, historical precedents, and conceptual bridges across domains."
        prompt = f"""
Given this claim:
CLAIM: {state['claim_a']}
Critique so far: {state['debate_history'][-1]}

Find:
1. Analogous structures in other fields
2. Historical precedent
3. Conceptual bridges
Keep it brief (max 100 words).
"""
        response = self._generate_response(system, prompt, 200, 0.5)
        state['debate_history'].append(f"CONNECTOR: {response}")
        return state
    
    def agent_synthesizer(self, state: DebateState) -> DebateState:
        """Role: Integrate contradictions, determine verdict."""
        print("⚖️ Synthesizer deciding...")
        system = "You are an integrator. Your goal is to determine if two claims support, refute, or are orthogonal to each other based on proper evidence."
        prompt = f"""
Synthesize the debate:
CLAIM A: {state['claim_a']}
CLAIM B: {state['claim_b']}

Debate History:
{' '.join(state['debate_history'])}

Determine:
1. Verdict (supports | refutes | extends | orthogonal)
2. Confidence (0-100)
3. Explanation

Output ONLY valid JSON:
{{
    "verdict": "string",
    "confidence": int,
    "explanation": "string"
}}
"""
        response = self._generate_response(system, prompt, 250, 0.2)
        
        # Parse JSON (Real implementation would use Outlines here too for safety)
        try:
            # simple cleanup for json parsing if model chats too much
            clean_json = response.strip()
            if "```json" in clean_json:
                clean_json = clean_json.split("```json")[1].split("```")[0]
            elif "```" in clean_json:
                clean_json = clean_json.split("```")[1].split("```")[0]
                
            data = json.loads(clean_json)
            state['verdict'] = data.get('verdict', 'orthogonal')
            state['confidence'] = float(data.get('confidence', 50)) / 100.0
            state['explanation'] = data.get('explanation', '')
            state['debate_history'].append(f"SYNTHESIZER: Verdict is {state['verdict']} ({state['confidence']})")
        except Exception as e:
            print(f"JSON Parse Error: {e}")
            state['verdict'] = "orthogonal"
            state['confidence'] = 0.0
            state['explanation'] = f"Failed to parse synthesis: {response}"
            
        return state
    
    def build_workflow(self):
        """Build LangGraph workflow. SERIAL execution."""
        workflow = StateGraph(DebateState)
        
        # Add nodes
        workflow.add_node("skeptic", self.agent_skeptic)
        workflow.add_node("connector", self.agent_connector)
        workflow.add_node("synthesizer", self.agent_synthesizer)
        
        # Define edges (Linear pipeline)
        workflow.set_entry_point("skeptic")
        workflow.add_edge("skeptic", "connector")
        workflow.add_edge("connector", "synthesizer")
        workflow.add_edge("synthesizer", END)
        
        return workflow.compile()
    
    def build_adversarial_workflow(self):
        """Build Adversarial Workflow with Methodology check"""
        workflow = StateGraph(DebateState)
        
        workflow.add_node("methodologist", self.agent_methodologist)
        workflow.add_node("skeptic", self.agent_skeptic)
        workflow.add_node("connector", self.agent_connector)
        workflow.add_node("synthesizer", self.agent_synthesizer)
        
        # Parallel or Sequential? Sequential for single-GPU M4.
        workflow.set_entry_point("methodologist")
        workflow.add_edge("methodologist", "skeptic")
        workflow.add_edge("skeptic", "connector")
        workflow.add_edge("connector", "synthesizer")
        workflow.add_edge("synthesizer", END)
        
        return workflow.compile()
    
    def run_debate(self, claim_a: str, claim_b: str) -> dict:
        """Run full debate between two claims."""
        # Use new adversarial workflow
        app = self.build_adversarial_workflow()
        
        initial_state = DebateState(
            claim_a=claim_a, 
            claim_b=claim_b, 
            debate_history=[], 
            verdict="unknown", 
            confidence=0.0,
            explanation=""
        )
        
        final_state = app.invoke(initial_state)
        
        return {
            "claim_a": claim_a,
            "claim_b": claim_b,
            "verdict": final_state['verdict'],
            "confidence": final_state['confidence'],
            "explanation": final_state['explanation'],
            "log": final_state['debate_history']
        }

if __name__ == "__main__":
    # Test stub
    print("Initializing Debate System...")
    # debater = DebateAgents()
    # res = debater.run_debate("AI is conscious", "AI is just math")
    # print(res)
