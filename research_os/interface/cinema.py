import asyncio
from pathlib import Path
from research_os.foundation.core import foundation
from research_os.config import settings
from loguru import logger
import subprocess

class CinemaEngine:
    """
    The Visual Director.
    Generates 3Blue1Brown-style animations for research concepts.
    """
    def __init__(self):
        self.output_dir = Path("render_output")
        self.output_dir.mkdir(exist_ok=True)

    async def create_scene(self, concept: str, context: str):
        """
        End-to-End Video Generation:
        1. Context -> Script (LLM)
        2. Script -> Video (Manim)
        """
        logger.info(f"🎬 Directed by ResearchOS: '{concept}'")
        
        # 1. Generate Script
        script_path = await self._write_script(concept, context)
        if not script_path:
            return None
            
        # 2. Render
        video_path = await self._render(script_path)
        return video_path

    async def _write_script(self, concept: str, context: str) -> Path:
        """Ask the LLM to write a Manim python script."""
        prompt = f"""
        Write a COMPLETE Python script using 'manim'.
        The scene should visually explain this concept: {concept}
        Context: {context}
        
        Requirements:
        - Class name must be 'ResearchScene'
        - Use Manim Community syntax
        - Visualise it as a geometric transformation or graph
        - Output ONLY the python code, no markdown backticks.
        """
        
        # Use Groq if available for speed/quality, else MLX
        code = foundation.generate(prompt, use_cloud=True)
        
        # Sanitize
        code = code.replace("```python", "").replace("```", "").strip()
        
        script_file = self.output_dir / f"{concept.replace(' ', '_')}_scene.py"
        script_file.write_text(code)
        logger.info(f"Script written to {script_file}")
        return script_file

    async def _render(self, script_path: Path) -> Path:
        """Execute Manim Render Command."""
        logger.info("Rendering Scene... (This uses heavy CPU/GPU)")
        
        # Command: manim -ql -v WARNING script.py ResearchScene
        # -ql = Quality Low (for speed during preview), use -qh for prod
        cmd = ["manim", "-ql", "-v", "WARNING", str(script_path), "ResearchScene"]
        
        try:
            # Run in thread to not block event loop
            await asyncio.to_thread(subprocess.run, cmd, cwd=self.output_dir)
            
            # Find output
            # Manim structure: media/videos/script_name/1080p60/ResearchScene.mp4
            # Simplified check
            logger.info("Render Complete.")
            return script_path.with_suffix(".mp4") # Placeholder path logic
            
        except Exception as e:
            logger.error(f"Render failed: {e}")
            return None

cinema_engine = CinemaEngine()
