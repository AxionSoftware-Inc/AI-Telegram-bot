import logging
import json
import httpx
from typing import Optional, List, Dict, Any
from config import OLLAMA_URL, MODEL_NAME, OPENROUTER_API_KEY

logger = logging.getLogger("LLMClient")

class LLMClient:
    def __init__(self, model_name: Optional[str] = None, base_url: Optional[str] = None, api_key: Optional[str] = None):
        self.model = model_name or MODEL_NAME
        self.base_url = (base_url or OLLAMA_URL).rstrip("/")
        self.api_key = api_key or OPENROUTER_API_KEY

    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.1,
        num_ctx: int = 4096,
        json_format: bool = False,
        timeout: float = 60.0
    ) -> Optional[str]:
        """OpenRouter API yoki Ollama orqali so'rov yuborish"""
        # 1. Agar OPENROUTER_API_KEY mavjud bo'lsa - OpenRouter API ishlatiladi
        if self.api_key:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            payload: Dict[str, Any] = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
            }
            if json_format:
                payload["response_format"] = {"type": "json_object"}

            try:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    resp = await client.post(
                        "https://openrouter.ai/api/v1/chat/completions",
                        headers=headers,
                        json=payload
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        choices = data.get("choices", [])
                        if choices:
                            return choices[0].get("message", {}).get("content", "").strip()
                        return ""
                    else:
                        logger.error(f"OpenRouter xatolik ({resp.status_code}): {resp.text}")
                        return None
            except Exception as e:
                logger.error(f"OpenRouter so'rovida ulanish xatosi: {e}")
                return None

        # 2. Aks holda - Lokal Ollama
        payload = {
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
            logger.error(f"Ollama so'rovida ulanish xatosi: {e}")
            return None
