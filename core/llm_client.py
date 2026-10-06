import logging
import json
import httpx
from typing import Optional, List, Dict, Any
from config import OLLAMA_URL, MODEL_NAME

logger = logging.getLogger("LLMClient")

class LLMClient:
    def __init__(self, model_name: Optional[str] = None, base_url: Optional[str] = None):
        self.model = model_name or MODEL_NAME
        self.base_url = (base_url or OLLAMA_URL).rstrip("/")

    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.1,
        num_ctx: int = 4096,
        json_format: bool = False,
        timeout: float = 60.0
    ) -> Optional[str]:
        """Ollama chat endpointiga so'rov yuborish"""
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_ctx": num_ctx
            }
        }
        if json_format:
            payload["format"] = "json"

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.post(f"{self.base_url}/api/chat", json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    content = data.get("message", {}).get("content", "").strip()
                    return content
                else:
                    logger.error(f"Ollama xatolik ({resp.status_code}): {resp.text}")
                    return None
        except Exception as e:
            logger.error(f"LLM so'rovida ulanish xatosi: {e}")
            return None
