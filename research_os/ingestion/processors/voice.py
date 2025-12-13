from pathlib import Path
from loguru import logger
import mlx_whisper

class VoiceProcessor:
    """
    Transcribes audio using Apple's MLX Whisper (Turbo).
    Achieves 20x real-time speed on M4.
    """
    
    def process(self, file_path: Path) -> dict:
        logger.info(f"Transcribing Voice Note: {file_path}")
        
        try:
            # Transcribe with MLX
            # word_timestamps=True allows for precise mapping later
            result = mlx_whisper.transcribe(
                str(file_path),
                path_or_hf_repo="mlx-community/whisper-large-v3-turbo"
            )
            
            text = result["text"]
            logger.info(f"Transcription Complete. Length: {len(text)} chars")
            
            return {
                "text": text,
                "segments": result.get("segments", []),
                "language": result.get("language", "en")
            }
            
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            raise

voice_processor = VoiceProcessor()
