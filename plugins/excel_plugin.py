import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import pandas as pd
from aiogram.types import Message

from core.plugin_base import BasePlugin, PluginResponse
from core.llm_client import LLMClient

logger = logging.getLogger("ExcelPlugin")

class ExcelPlugin(BasePlugin):
    name = "ExcelAnalyzer"
    description = "Excel (.xlsx, .xls) fayllarni yuklash, o'qish va Gemma 4 modeli orqali tahlil qilish plugini"
    priority = 20  # Yuqori prioritet, chunki fayllar va hisobot so'rovlari aniq

    def __init__(self):
        self.llm = LLMClient()
        self.active_files: Dict[int, str] = {}  # chat_id -> excel_file_path
        self.downloads_dir = Path(__file__).resolve().parent.parent / "data" / "downloads"
        self.downloads_dir.mkdir(parents=True, exist_ok=True)
        self.default_demo_file = Path(__file__).resolve().parent.parent / "data" / "klinika_hisoboti.xlsx"

    def _get_excel_summary_text(self, file_path: str, max_rows: int = 15) -> str:
        """Excel fayldan varaqlar va qisqacha ma'lumotlarni matn ko'rinishida olish"""
        try:
            excel = pd.ExcelFile(file_path)
            summary_parts = [f"📊 Excel fayl: {os.path.basename(file_path)}", f"Varaqlar soni: {len(excel.sheet_names)}"]
            
            for sheet_name in excel.sheet_names:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                summary_parts.append(f"\n--- VARAQ: «{sheet_name}» (Qatorlar: {len(df)}, Ustunlar: {len(df.columns)}) ---")
                summary_parts.append("Ustunlar: " + ", ".join(map(str, df.columns.tolist())))
                # Qisqa jadval ko'rinishi
                head_str = df.head(max_rows).to_string(index=False)
                summary_parts.append(head_str)

            return "\n".join(summary_parts)
        except Exception as e:
            logger.error(f"Excel faylni o'qishda xatolik: {e}")
            return f"Xatolik: Excel faylni o'qib bo'lmadi ({e})"

    async def can_handle(self, message: Message, context: Dict[str, Any]) -> bool:
        # 1. Hujjat yuborilgan bo'lsa va kengaytmasi .xlsx yoki .xls bo'lsa
        if message.document and message.document.file_name:
            fname = message.document.file_name.lower()
            if fname.endswith(".xlsx") or fname.endswith(".xls") or fname.endswith(".csv"):
                return True

        text = (message.text or message.caption or "").strip()
        # 2. Maxsus komandalar
        if text.startswith("/excel") or text.startswith("/excel_demo") or text.startswith("/hisobot"):
            return True

        # 3. Agar ushbu chatda faol Excel fayl bo'lsa va xabar tahlil/jadval haqida bo'lsa
        chat_id = message.chat.id
        if chat_id in self.active_files and len(text) > 3:
            keywords = [
                "excel", "jadval", "daromad", "tushum", "bemor", "hisobot", "qancha", 
                "eng ko'p", "eng kam", "jami", "o'rtacha", "statistika", "shifokor", 
                "narx", "tahlil", "mutaxassis", "murojaat", "varaq"
            ]
            text_lower = text.lower()
            if any(k in text_lower for k in keywords):
                return True

        return False

    async def handle(self, message: Message, context: Dict[str, Any]) -> Optional[PluginResponse]:
        chat_id = message.chat.id
        bot = message.bot
        text = (message.text or message.caption or "").strip()

        # HOLAT 1: Yangi Excel fayl yuborildi
        if message.document and message.document.file_name:
            file_name = message.document.file_name
            target_path = self.downloads_dir / f"{chat_id}_{file_name}"
            
            status_msg = await message.reply("📥 Excel fayl yuklab olinmoqda va tahlil qilinmoqda...")
            
            try:
                file_info = await bot.get_file(message.document.file_id)
                await bot.download_file(file_info.file_path, destination=target_path)
                self.active_files[chat_id] = str(target_path)
                
                # Qisqa tahlil tayyorlash
                raw_summary = self._get_excel_summary_text(str(target_path))
                
                # Gemma 4 ga tahlil qildirib xulosa olish
                prompt = (
                    "Quyidagi Excel jadval ma'lumotlarini o'rganib chiq. O'zbek tilida qisqa, aniq va chiroyli formatda "
                    "umumiy xulosa, asosiy ko'rsatkichlar va jadval nima haqidaligini tushuntirib ber:\n\n"
                    f"{raw_summary[:3500]}"
                )
                
                llm_response = await self.llm.chat(
                    messages=[
                        {"role": "system", "content": "Siz tajribali ma'lumotlar tahlilchisisiz (Data Analyst). Excel ma'lumotlarini chuqur tahlil qilib, o'zbekcha chiroyli hisobot berasiz."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.2,
                    timeout=90.0
                )
                
                reply_text = (
                    f"✅ **«{file_name}» fayli muvaffaqiyatli yuklandi!**\n\n"
                    f"🤖 **Gemma 4-26B tahlili:**\n\n"
                    f"{llm_response or raw_summary[:800]}\n\n"
                    f"💡 *Endi ushbu jadval bo'yicha har qanday savolingizni berishingiz mumkin (masalan: 'Eng ko'p daromad keltirgan xizmat qaysi?', 'Jami bemorlar soni nechta?').*"
                )
                await status_msg.edit_text(reply_text)
                return PluginResponse(text=reply_text, handled=True)
            except Exception as e:
                logger.error(f"Faylni yuklab olishda xatolik: {e}")
                err_text = f"❌ Faylni tahlil qilishda xatolik yuz berdi: {e}"
                await status_msg.edit_text(err_text)
                return PluginResponse(text=err_text, handled=True)

        # HOLAT 2: /excel yoki /excel_demo komandasi
        if text.startswith("/excel"):
            if not self.default_demo_file.exists():
                return PluginResponse(text="❌ Demo Excel fayli topilmadi.", handled=True)

            self.active_files[chat_id] = str(self.default_demo_file)
            status_msg = await message.reply("⏳ «Klinika hisoboti» demo Excel fayli yuklanmoqda va Gemma 4 orqali tahlil qilinmoqda...")
            
            raw_summary = self._get_excel_summary_text(str(self.default_demo_file))
            prompt = (
                "Quyidagi klinika hisoboti Excel faylini tahlil qilib, o'zbek tilida asosiy ko'rsatkichlarni bayon qil:\n"
                "- Eng daromadli xizmatlar\n"
                "- Shifokorlar va bemorlar soni\n"
                "- Oylik dinamika xulosasi\n\n"
                f"{raw_summary}"
            )
            
            llm_response = await self.llm.chat(
                messages=[
                    {"role": "system", "content": "Siz tibbiy ma'lumotlar tahlilchisisiz. Excel jadvalidagi sonlar va statistikani o'zbekcha ravon tushuntirib bering."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                timeout=90.0
            )

            fallback_text = llm_response or "Excel fayl ma'lumotlari yuklandi."
            reply_text = (
                f"📊 **«Klinika Hisoboti» (Demo Excel) faollashtirildi!**\n\n"
                f"🧠 **Gemma 4-26B tahlili:**\n\n"
                f"{fallback_text}\n\n"
                f"💬 *Ushbu fayl bo'yicha xohlagan savolingizni berishingiz mumkin.*"
            )
            await status_msg.edit_text(reply_text)
            return PluginResponse(text=reply_text, handled=True)

        # HOLAT 3: Faol Excel bo'yicha berilgan savol
        if chat_id in self.active_files:
            file_path = self.active_files[chat_id]
            status_msg = await message.reply("🔍 Gemma 4 jadvaldan ma'lumotlarni qidirmoqda...")
            raw_summary = self._get_excel_summary_text(file_path)
            
            user_question = text
            prompt = (
                f"Quyidagi Excel jadvali asosida foydalanuvchining savoliga aniq va asoslangan javob ber.\n"
                f"Jadval ma'lumotlari:\n{raw_summary}\n\n"
                f"Foydalanuvchi savoli: «{user_question}»\n"
                f"Javobni o'zbek tilida, aniq sonlar va jadvallarga tayanib yozing:"
            )

            llm_response = await self.llm.chat(
                messages=[
                    {"role": "system", "content": "Siz Excel jadvallari bo'yicha aniq hisob-kitob qiluvchi va savollarga javob beruvchi yordamchisiz."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                timeout=90.0
            )

            ans_text = llm_response or "Savolga javob tayyorlashda xatolik yuz berdi."
            await status_msg.edit_text(ans_text)
            return PluginResponse(text=ans_text, handled=True)

        return None
