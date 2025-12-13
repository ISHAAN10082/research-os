# Voice Loop: Push-to-Talk Research Ideation
"""
Captures spoken research insights, transcribes them, and auto-structures them
into actionable notes using the hybrid intelligence engine.

Uses:
- SoundDevice for audio capture
- Groq Whisper (distil-whisper-large-v3-en) for ultra-fast transcription
- Foundation for structuring
"""

import asyncio
import numpy as np
import sounddevice as sd
import scipy.io.wavfile as wav
import tempfile
import os
from datetime import datetime
from loguru import logger
from dataclasses import dataclass

@dataclass
class VoiceNote:
    transcript: str
    structured_content: str
    created_at: datetime
    audio_path: str

class VoiceLoop:
    """Voice capture and insight structuring engine."""
    
    def __init__(self, foundation):
        self.foundation = foundation
        self._recording = False
        self._audio_buffer = []
        self._sample_rate = 16000  # Whisper standard
        self._temp_dir = os.path.join(os.getcwd(), "downloads", "voice_notes")
        os.makedirs(self._temp_dir, exist_ok=True)
        
    def start_recording(self):
        """Start recording audio in background."""
        if self._recording:
            return
            
        self._recording = True
        self._audio_buffer = []
        
        def callback(indata, frames, time, status):
            if status:
                logger.warning(f"Audio status: {status}")
            if self._recording:
                self._audio_buffer.append(indata.copy())
        
        # Start non-blocking stream
        self.stream = sd.InputStream(
            samplerate=self._sample_rate,
            channels=1,
            callback=callback
        )
        self.stream.start()
        logger.info("🎙️ Recording started...")
    
    async def stop_processing(self) -> VoiceNote:
        """Stop recording, transcribe, and structure."""
        if not self._recording:
            return None
            
        logger.info("🛑 Stopping recording...")
        self._recording = False
        self.stream.stop()
        self.stream.close()
        
        if not self._audio_buffer:
            return None
            
        # Concatenate and save wav
        audio_data = np.concatenate(self._audio_buffer, axis=0)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(self._temp_dir, f"note_{timestamp}.wav")
        wav.write(filename, self._sample_rate, audio_data)
        
        # Transcribe
        transcript = await self.transcribe(filename)
        
        # Structure
        structured = await self.structure_insight(transcript)
        
        return VoiceNote(
            transcript=transcript,
            structured_content=structured,
            created_at=datetime.now(),
            audio_path=filename
        )
        
    async def transcribe(self, audio_path: str) -> str:
        """Transcribe audio using Groq Whisper API (or local fallback)."""
        logger.info("📝 Transcribing...")
        
        # Try Groq first (fastest)
        if self.foundation.groq:
            try:
                def _run_groq():
                    with open(audio_path, "rb") as file:
                        return self.foundation.groq.audio.transcriptions.create(
                            file=(audio_path, file.read()),
                            model="distil-whisper-large-v3-en",
                            response_format="text"
                        )
                
                # Check if it returns just text string or object
                result = await asyncio.to_thread(_run_groq)
                return str(result).strip()
            except Exception as e:
                logger.error(f"Groq transcription failed: {e}")
        
        return "(Transcription failed or no API Key)"

    async def structure_insight(self, transcript: str) -> str:
        """Covert rambling into structured research insight."""
        logger.info("🧠 Structuring insight...")
        
        prompt = f"""Structure this raw research voice note into a clean insight card:

RAW AUDIO: "{transcript}"

Format:
# 🎙️ Insight: [One sentence summary]
- **Core Idea**: [What is the main point?]
- **Context/Connection**: [How does this relate to broader research?]
- **Action**: [What should I do next?]"""

        return await self.foundation.generate_async(
            prompt=prompt,
            system="You are an expert research synthesizer. Clean up spoken thoughts.",
            max_tokens=300
        )
