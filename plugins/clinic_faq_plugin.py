import json
import logging
from typing import Dict, Any, Optional
from aiogram.types import Message
from aiogram.enums import ChatType

from core.plugin_base import BasePlugin, PluginResponse
from core.llm_client import LLMClient
from config import CLINIC_DATA_PATH, MODEL_NAME

logger = logging.getLogger("ClinicFAQPlugin")

class ClinicFAQPlugin(BasePlugin):
    name = "ClinicFAQ"
    description = "Klinikaga oid savollarni (manzil, ish vaqti, narxlar, shifokorlar) tahlil qilib tayyor javob berish plugini"
    priority = 80

    def __init__(self):
        with open(CLINIC_DATA_PATH, "r", encoding="utf-8") as f:
            self.data = json.load(f)
        
        self.clinic_name = self.data.get("clinic_name", "Klinika")
        self.categories = self.data.get("categories", {})
        self.llm = LLMClient()

        cat_descriptions = []
        for code, info in self.categories.items():
            cat_descriptions.append(f"- {code} : {info['name']}")

        self.system_prompt = (
            f"Siz «{self.clinic_name}» Telegram guruhidagi aqlli yordamchisiz.\n"
            "Foydalanuvchi xabarining ASL MAZMUNINI tushunib, unga mos toifani aniqlang.\n"
            "Toifalar:\n"
            "- NONE : Klinikaga umuman aloqasi yo'q xabarlar\n"
            + "\n".join(cat_descriptions) + "\n\n"
            "Format: {\"category\": \"TOIFA_KODI\"}"
        )

    def match_by_keywords(self, text: str) -> Optional[str]:
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
            return max(scores, key=scores.get)
        return None

    async def can_handle(self, message: Message, context: Dict[str, Any]) -> bool:
        if message.text:
            text = message.text.strip().lower()
            if text.startswith("/"):
                return False
            medical_keywords = [
                "klinika", "vrach", "shifokor", "do'xtir", "doktor", "tahlil", "analiz", 
                "uzi", "mrt", "bemor", "davolash", "stomatolog", "terapevt", "kardiolog", 
                "lor", "qon", "siydik", "rentgen"
            ]
            return any(kw in text for kw in medical_keywords)
        return False

    async def handle(self, message: Message, context: Dict[str, Any]) -> Optional[PluginResponse]:
        text = message.text.strip()
        chat_id = message.chat.id
        is_group = message.chat.type in [ChatType.GROUP, ChatType.SUPERGROUP]

        # 1. Tezkor kalit so'zlar orqali tekshirish (0.001 soniya)
        quick_match = self.match_by_keywords(text)
        if quick_match and quick_match in self.categories:
            logger.info(f"FAQ tezkor topildi: [{quick_match}] <- '{text}'")
            return PluginResponse(text=self.categories[quick_match]["response"], handled=True)

        # 2. Kalit so'z topilmasa, LLM orqali JSON tahlil
        category = None
        try:
            raw = await self.llm.chat(
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": f"Foydalanuvchi xabari: «{text}»"}
                ],
                temperature=0.0,
                json_format=True,
                timeout=25.0
            )
            if raw:
                parsed = json.loads(raw)
                cat = parsed.get("category", "").upper()
                if cat in self.categories:
                    category = cat
                elif cat == "NONE":
                    category = None
        except Exception as e:
            logger.error(f"FAQ LLM tahlilida xatolik: {e}")

        if category and category in self.categories:
            logger.info(f"FAQ LLM orqali topildi: [{category}] <- '{text}'")
            return PluginResponse(text=self.categories[category]["response"], handled=True)

        # Agar guruhda bo'lsa va klinika savoli bo'lmasa -> jim turish
        if is_group:
            return PluginResponse(handled=False)

        # Shaxsiy yozishmada yo'naltirish
        return PluginResponse(
            text="Tushunmadim. Klinikamiz xizmatlari, narxlar, manzil yoki shifokorlar haqida so'rashingiz mumkin.",
            handled=True
        )
