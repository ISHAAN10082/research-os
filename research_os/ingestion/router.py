import filetype
from pathlib import Path
from loguru import logger
from enum import Enum

class ResearchType(Enum):
    PAPER = "paper"
    CODE = "code"
    VOICE = "voice"
    DATA = "data"
    UNKNOWN = "unknown"

class InputRouter:
    """
    High-speed file router using magic bytes detection.
    Prevents loading incorrect parsers.
    """
    
    def route(self, file_path: str) -> ResearchType:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"{file_path}")
            
        # 1. Fast Extension Check
        ext = path.suffix.lower()
        if ext == ".pdf":
            return ResearchType.PAPER
        if ext in [".py", ".js", ".rs", ".cpp", ".ipynb", ".md"]:
            return ResearchType.CODE
        if ext in [".csv", ".parquet", ".json"]:
            return ResearchType.DATA
            
        # 2. Magic Bytes (for Binary/Media)
        kind = filetype.guess(file_path)
        if kind:
            if kind.mime.startswith("audio/"):
                return ResearchType.VOICE
            if kind.mime == "application/pdf":
                return ResearchType.PAPER
                
        return ResearchType.UNKNOWN

input_router = InputRouter()
