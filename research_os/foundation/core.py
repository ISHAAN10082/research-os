import os
import asyncio
from typing import Optional, List
from research_os.config import settings
from research_os.foundation.graph import graph_engine, GraphEngine
from research_os.foundation.vector import get_vector_engine, VectorEngine
from groq import Groq
from loguru import logger

# Lazy imports for MLX
# import mlx_lm 


class Foundation:
    """
    The Core Layer 0 Daemon.
    Manages connections to Graph, Vector, and Intelligence engines.
    
    SOTA Features (Dec 2024):
    - Qwen2.5-7B-Instruct (Apache 2.0) - best local quality
    - Smart cloud routing to Groq (free tier)
    - Hybrid retrieval integration
    """
    
    def __init__(self):
        self.graph: GraphEngine = graph_engine
        self._vector_engine: Optional[VectorEngine] = None
        self._groq_client = None
        
        # MLX Model State
        self._mlx_model = None
        self._mlx_tokenizer = None
        self._model_loaded = False
    
    @property
    def vector(self) -> VectorEngine:
        """Lazy load vector engine."""
        if self._vector_engine is None:
            self._vector_engine = get_vector_engine()
        return self._vector_engine

    @property
    def groq(self):
        """Lazy load Groq client (free tier)."""
        if not self._groq_client and settings.GROQ_API_KEY:
            self._groq_client = Groq(api_key=settings.GROQ_API_KEY)
        return self._groq_client

    def load_mlx_model(self):
        """Load the local LLM into memory."""
        if self._model_loaded:
            return
        
        logger.info(f"Loading Local LLM: {settings.LOCAL_LLM_MODEL}")
        import mlx_lm
        
        self._mlx_model, self._mlx_tokenizer = mlx_lm.load(settings.LOCAL_LLM_MODEL)
        self._model_loaded = True
        logger.info(f"✅ Local LLM Loaded ({settings.LOCAL_LLM_MODEL.split('/')[-1]})")

    def unload_mlx_model(self):
        """Free up RAM for other tasks (like heavy rendering)."""
        self._mlx_model = None
        self._mlx_tokenizer = None
        self._model_loaded = False
        import gc
        gc.collect()
        logger.info("Local LLM Unloaded")
    
    def _estimate_tokens(self, text: str) -> int:
        """Rough token estimation (4 chars per token average)."""
        return len(text) // 4
    
    def _should_use_cloud(self, prompt: str, context: str = "") -> bool:
        """
        Smart routing decision.
        Use cloud when:
        1. Context is very large (> CLOUD_BURST_THRESHOLD)
        2. Complex multi-hop reasoning detected
        3. User explicitly requests
        """
        total_length = len(prompt) + len(context)
        estimated_tokens = self._estimate_tokens(prompt + context)
        
        # Check if above threshold
        if estimated_tokens > settings.CLOUD_BURST_THRESHOLD:
            logger.info(f"Cloud burst: {estimated_tokens} tokens > {settings.CLOUD_BURST_THRESHOLD}")
            return True
        
        # Check for complexity indicators
        complexity_keywords = ["compare", "analyze", "synthesize", "across", "multiple papers"]
        if any(kw in prompt.lower() for kw in complexity_keywords):
            return True
        
        return False

    def generate(
        self, 
        prompt: str, 
        system: str = "You are ResearchOS, an expert research assistant.", 
        context: str = "",
        use_cloud: bool = False,
        max_tokens: int = 2048,
        temperature: float = 0.7
    ) -> str:
        """
        Hybrid Generation with smart routing.
        
        - Local (Qwen2.5-7B): Fast, private, <150ms for short queries
        - Cloud (Groq 70B): Complex reasoning, large context
        
        Args:
            prompt: User query
            system: System prompt
            context: Retrieved context (from retriever)
            use_cloud: Force cloud usage
            max_tokens: Maximum generation length
            temperature: Sampling temperature
        """
        # Smart routing
        should_cloud = use_cloud or self._should_use_cloud(prompt, context)
        
        if should_cloud and self.groq:
            return self._generate_cloud(prompt, system, context, max_tokens, temperature)
        
        return self._generate_local(prompt, system, context, max_tokens, temperature)
    
    def _generate_cloud(
        self, 
        prompt: str, 
        system: str,
        context: str,
        max_tokens: int,
        temperature: float
    ) -> str:
        """Generate using Groq cloud (70B model)."""
        try:
            logger.info("☁️ Using Cloud (Groq) for generation...")
            
            # Build messages
            messages = [{"role": "system", "content": system}]
            
            if context:
                messages.append({
                    "role": "user", 
                    "content": f"Context:\n{context}\n\nQuestion: {prompt}"
                })
            else:
                messages.append({"role": "user", "content": prompt})
            
            chat_completion = self.groq.chat.completions.create(
                messages=messages,
                model=settings.GROQ_MODEL,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            return chat_completion.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Groq failed: {e}. Falling back to local.")
            return self._generate_local(prompt, system, context, max_tokens, temperature)
    
    def _generate_local(
        self, 
        prompt: str, 
        system: str,
        context: str,
        max_tokens: int,
        temperature: float
    ) -> str:
        """Generate using local MLX model (Phi-3.5)."""
        self.load_mlx_model()
        import mlx_lm
        
        logger.info("🏠 Using Local (MLX) for generation...")
        
        # Build messages for chat template
        messages = [{"role": "system", "content": system}]
        
        if context:
            user_content = f"Context:\n{context}\n\nQuestion: {prompt}"
        else:
            user_content = prompt
        
        messages.append({"role": "user", "content": user_content})
        
        # Apply chat template
        formatted_prompt = self._mlx_tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )
        
        # Use streaming generation and collect tokens
        tokens = []
        for chunk in mlx_lm.stream_generate(
            self._mlx_model,
            self._mlx_tokenizer,
            prompt=formatted_prompt,
            max_tokens=max_tokens
        ):
            # Extract text from GenerationResponse object
            if hasattr(chunk, 'text'):
                token_text = chunk.text
            elif isinstance(chunk, tuple):
                token_text = str(chunk[0])
            elif isinstance(chunk, str):
                token_text = chunk
            else:
                token_text = str(chunk)
            tokens.append(token_text)
        
        return "".join(tokens)
    
    async def generate_async(
        self, 
        prompt: str, 
        system: str = "You are ResearchOS, an expert research assistant.",
        context: str = "",
        use_cloud: bool = False,
        max_tokens: int = 512
    ) -> str:
        """Async wrapper for generation."""
        return await asyncio.to_thread(
            self.generate, 
            prompt, 
            system, 
            context, 
            use_cloud,
            max_tokens
        )

    async def generate_stream_async(
        self,
        prompt: str,
        system: str = "You are ResearchOS. Use Mermaid.js for diagrams (```mermaid).",
        context: str = "",
        max_tokens: int = 512,
        use_cloud: bool = False,
        callback = None
    ):
        """
        Smart Hybrid Streaming Generation.
        Routes to Local (MLX) or Cloud (Groq) based on complexity or Override.
        """
        from research_os.foundation.router import router, RouteDestination
        
        # 1. Route
        decision = router.route(prompt, len(context))
        
        # 2. Dispatch
        should_cloud = use_cloud or (decision.destination == RouteDestination.CLOUD)
        
        logger.info(f"🔀 Routing dispatch: {'CLOUD (Forced)' if use_cloud else decision.destination.name} ({decision.reason})")
        
        if should_cloud and self.groq:
            try:
                logger.info("☁️ Streaming from Groq (70B)...")
                return await self._stream_cloud(prompt, system, context, max_tokens, callback)
            except Exception as e:
                logger.error(f"Groq Stream failed: {e}. Fallback to Local.")
                # Fallthrough to local
        
        # Local Fallback / Default
        logger.info("🏠 Streaming from Local (MLX)...")
        return await self._stream_local(prompt, system, context, max_tokens, callback)

    async def _stream_cloud(self, prompt, system, context, max_tokens, callback):
        """Stream from Groq API."""
        messages = [{"role": "system", "content": system}]
        if context:
            messages.append({"role": "user", "content": f"Context:\n{context}\n\nQuestion: {prompt}"})
        else:
            messages.append({"role": "user", "content": prompt})
            
        # Run blocking network IO in thread
        def run_stream():
            stream = self.groq.chat.completions.create(
                messages=messages,
                model=settings.GROQ_MODEL,
                max_tokens=max_tokens,
                temperature=0.7,
                stream=True
            )
            
            full_text = []
            for chunk in stream:
                content = chunk.choices[0].delta.content
                if content:
                    full_text.append(content)
                    if callback:
                        callback(content)
            return "".join(full_text)
            
        return await asyncio.to_thread(run_stream)

    async def _stream_local(self, prompt, system, context, max_tokens, callback):
        """Stream from Local MLX."""
        self.load_mlx_model()
        import mlx_lm
        
        # Build messages and format
        messages = [{"role": "system", "content": system}]
        user_content = f"Context:\n{context}\n\nQuestion: {prompt}" if context else prompt
        messages.append({"role": "user", "content": user_content})
        
        formatted_prompt = self._mlx_tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        
        loop = asyncio.get_running_loop()

        def run_stream():
            tokens = []
            stop_tokens = ["<|end|>", "<|assistant|>", "<|user|>"]
            
            for chunk in mlx_lm.stream_generate(
                self._mlx_model,
                self._mlx_tokenizer,
                prompt=formatted_prompt,
                max_tokens=max_tokens
            ):
                if hasattr(chunk, 'text'):
                    token_text = chunk.text
                elif isinstance(chunk, tuple):
                    token_text = str(chunk[0])
                else:
                    token_text = str(chunk)
                
                # Check for stop tokens
                if any(s in token_text for s in stop_tokens):
                    break
                    
                tokens.append(token_text)
                
                # Double check accumulated text for stop tokens (sometimes they get split)
                full_text = "".join(tokens)
                if any(full_text.endswith(s) for s in stop_tokens):
                    # Remove the stop token and break
                    break

                if callback:
                    # Check if callback is a coroutine function or returns a coroutine
                    import inspect
                    if inspect.iscoroutinefunction(callback):
                        asyncio.run_coroutine_threadsafe(callback(token_text), loop)
                    else:
                        callback(token_text)
            return "".join(tokens)
            
        return await asyncio.to_thread(run_stream)


# Singleton
foundation = Foundation()

