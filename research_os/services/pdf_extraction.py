"""
ResearchOS Grobid Client.
Communicates with a Dockerized Grobid instance to extracting structured metadata.
"""
import httpx
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class GrobidClient:
    def __init__(self, host: str = "http://localhost:8070"):
        self.host = host.rstrip('/')
        self.client = httpx.AsyncClient(timeout=30.0)

    async def is_alive(self) -> bool:
        """Check if Grobid container is running."""
        try:
            resp = await self.client.get(f"{self.host}/api/isalive")
            return resp.status_code == 200
        except Exception:
            return False

    async def process_pdf(self, pdf_bytes: bytes) -> Dict[str, Any]:
        """
        Send PDF to Grobid for 'processFulltextDocument'.
        Returns structured TEI XML (simplified implementation returning raw XML for now).
        TODO: Implement TEI -> JSON parser.
        """
        try:
            files = {'input': pdf_bytes}
            resp = await self.client.post(
                f"{self.host}/api/processFulltextDocument",
                files=files,
                data={'consolidateHeader': '1', 'consolidateCitations': '1'}
            )
            
            if resp.status_code == 200:
                # Success
                return {"xml": resp.text}
            else:
                logger.error(f"Grobid Error {resp.status_code}: {resp.text}")
                return {}
        except Exception as e:
            logger.error(f"Grobid Connection Error: {e}")
            return {}

grobid = GrobidClient()
