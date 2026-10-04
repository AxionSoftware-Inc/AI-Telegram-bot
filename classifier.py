import json
import logging
import re
import httpx
from typing import Optional, Tuple
from config import OPENROUTER_API_KEY, MODEL_NAME, CLINIC_DATA_PATH

logger = logging.getLogger(__name__)

class ClinicClassifier:
    def __init__(self):
        with open(CLINIC_DATA_PATH, "r", encoding="utf-8") as f:
            self.data = json.load(f)
        
        self.clinic_name = self.data.get("clinic_name", "Klinika")
        self.categories = self.data.get("categories", {})
        
        # Build prompt descriptions
        cat_descriptions = []
        for code, info in self.categories.items():
            cat_descriptions.append(f"- {code} : {info['name']}")
        
        self.system_prompt = (
            f"Siz «{self.clinic_name}» Telegram guruhidagi aqlli yordamchisiz.\n"
            "Foydalanuvchi xabarining ASL MAZMUNINI tushunib, unga mos toifani aniqlang.\n"
            "Toifalar:\n"
            "- NONE : Klinikaga umuman aloqasi yo'q xabarlar (salom-alik, ob-havo, futbol, hazil, umumiy suhbatlar)\n"
            + "\n".join(cat_descriptions) + "\n\n"
            "MUHIM QOIDA: Javobni FAQAT JSON formatida qaytaring!\n"
            "Format: {\"category\": \"TOIFA_KODI\"}\n"
            "Misol: {\"category\": \"LOCATION\"} yoki {\"category\": \"NONE\"}"
        )

    def match_by_keywords(self, text: str) -> Optional[str]:
        """Tezkor kalit so'zlar orqali tekshirish (0.001 soniyada)"""
        text_lower = text.lower()
        scores = {}
        for code, info in self.categories.items():
            score = 0
            for kw in info.get("keywords", []):
                if kw in text_lower:
                    score += 1
            if score > 0:
                scores[code] = score
        
        if scores:
            best_cat = max(scores, key=scores.get)
            return best_cat
        return None

    async def classify_message(self, text: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Xabarni tahlil qiladi.
        Qaytaradi: (category_code, prepared_response) yoki (None, None)
        """
        text_clean = text.strip()
        if len(text_clean) < 3:
            return None, None

        # 1. Tezkor kalit so'zlar orqali tekshirish
        quick_match = self.match_by_keywords(text_clean)
        if quick_match and quick_match in self.categories:
            logger.info(f"Tezkor mos keldi: [{quick_match}] <- '{text_clean}'")
            return quick_match, self.categories[quick_match]["response"]

        # 2. Kalit so'z topilmasa, OpenRouter API orqali semantik tahlil
        if not OPENROUTER_API_KEY:
            logger.warning("OPENROUTER_API_KEY topilmadi!")
            return None, None

        category = None
        try:
            headers = {
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": MODEL_NAME,
                "messages": [
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": f"Foydalanuvchi xabari: «{text_clean}»"}
                ],
                "response_format": {"type": "json_object"},
                "temperature": 0.0,
                "max_tokens": 100
            }
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers=headers,
                    json=payload
                )
                if resp.status_code == 200:
                    raw_content = resp.json()["choices"][0]["message"]["content"].strip()
                    logger.info(f"LLM javobi (raw): {raw_content}")
                    try:
                        parsed = json.loads(raw_content)
                        cat = parsed.get("category", "").upper()
                        if cat in self.categories:
                            category = cat
                        elif cat == "NONE":
                            category = None
                    except Exception:
                        for code in self.categories.keys():
                            if code in raw_content.upper():
                                category = code
                                break
                else:
                    logger.warning(f"OpenRouter API xatosi ({resp.status_code}): {resp.text}")
        except Exception as e:
            logger.error(f"LLM tahlilida xatolik: {e}")

        if category and category in self.categories:
            logger.info(f"LLM orqali aniqlandi: [{category}] <- '{text_clean}'")
            return category, self.categories[category]["response"]
        
        return None, None
