import json
import logging
import re
import httpx
from typing import Optional, Tuple
from config import OLLAMA_URL, MODEL_NAME, CLINIC_DATA_PATH

logger = logging.getLogger(__name__)

class ClinicClassifier:
    def __init__(self):
        with open(CLINIC_DATA_PATH, "r", encoding="utf-8") as f:
            self.data = json.load(f)
        
        self.clinic_name = self.data.get("clinic_name", "Klinika")
        self.categories = self.data.get("categories", {})
        
        # Build prompt
        cat_descriptions = []
        for code, info in self.categories.items():
            cat_descriptions.append(f"- {code} : {info['name']}")
        
        self.system_prompt = (
            f"Siz «{self.clinic_name}» Telegram guruhidagi aqlli yordamchisiz.\n"
            "Foydalanuvchi xabarini tahlil qilib, faqat klinikaga tegishli toifani aniqlang.\n"
            "Toifalar:\n"
            "- NONE : Klinikaga umuman aloqasi yo'q xabarlar (salom-alik, ob-havo, minnatdorchilik, futbol, hazil, umumiy suhbatlar)\n"
            + "\n".join(cat_descriptions) + "\n\n"
            "MUHIM QOIDA: Agar xabar klinikaga tegishli bo'lmasa, FAQAT NONE deb javob bering.\n"
            "Agar tegishli bo'lsa, FAQAT yuqoridagi toifa kodini (masalan, LOCATION, PRICES_SERVICES va h.k.) yozing.\n"
            "Hech qanday qo'shimcha so'z, nuqta yoki izoh yozmang!"
        )

    def match_by_keywords(self, text: str) -> Optional[str]:
        """Tezkor kalit so'zlar orqali tekshirish (fallback / tezlatkich)"""
        text_lower = text.lower()
        # Maxsus kalit so'zlarni sanash
        scores = {}
        for code, info in self.categories.items():
            score = 0
            for kw in info.get("keywords", []):
                # Butun so'z yoki iborani qidirish
                if kw in text_lower:
                    score += 1
            if score > 0:
                scores[code] = score
        
        if scores:
            best_cat = max(scores, key=scores.get)
            # Kamida 1 ta aniq kalit so'z bo'lsa
            return best_cat
        return None

    async def classify_message(self, text: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Xabarni tahlil qiladi.
        Qaytaradi: (category_code, prepared_response) yoki (None, None)
        """
        text_clean = text.strip()
        if len(text_clean) < 4:
            return None, None

        # 1. Tezkor kalit so'zlar orqali tekshirish (0.001 soniya ichida)
        quick_match = self.match_by_keywords(text_clean)
        if quick_match and quick_match in self.categories:
            logger.info(f"Tezkor kalit so'z orqali aniqlandi: [{quick_match}]")
            return quick_match, self.categories[quick_match]["response"]

        # 2. Agar kalit so'zlar topilmasa, lekin xabarda so'rov/savol alomatlari bo'lsa, LLM ga yuborish
        category = None
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                payload = {
                    "model": MODEL_NAME,
                    "messages": [
                        {"role": "system", "content": self.system_prompt},
                        {"role": "user", "content": f"Foydalanuvchi xabari: «{text_clean}»\nToifa:"}
                    ],
                    "stream": False,
                    "options": {
                        "temperature": 0.0,
                        "num_predict": 25
                    }
                }
                resp = await client.post(f"{OLLAMA_URL}/api/chat", json=payload)
                if resp.status_code == 200:
                    ans = resp.json().get("message", {}).get("content", "").strip()
                    ans_clean = re.sub(r"[^A-Z_]", "", ans.upper())
                    
                    if "NONE" in ans_clean:
                        category = None
                    else:
                        for code in self.categories.keys():
                            if code in ans_clean:
                                category = code
                                break
                    logger.info(f"LLM tahlili natijasi: raw='{ans}', category={category}")
                else:
                    logger.warning(f"Ollama API xatosi ({resp.status_code}): {resp.text}")
        except Exception as e:
            logger.error(f"LLM so'rovida xatolik: {e}")

        if category and category in self.categories:
            return category, self.categories[category]["response"]
        
        return None, None
