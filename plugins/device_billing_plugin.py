import re
import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import pandas as pd
from aiogram.types import Message

from core.plugin_base import BasePlugin, PluginResponse

logger = logging.getLogger("DeviceBillingPlugin")

class DeviceBillingPlugin(BasePlugin):
    name = "DeviceBilling"
    description = "Apparatlarning to'xtab qolish sababini haftalik Excel to'lovlar bazasidan tekshiruvchi plugin"
    priority = 10  # Eng yuqori prioritet, chunki ID va apparat shikoyatlari o'ta muhim

    def __init__(self):
        self.billing_file = Path(__file__).resolve().parent.parent / "data" / "billing" / "haftalik_tolovlar.xlsx"
        self.user_states: Dict[int, str] = {}  # chat_id/user_id -> state
        self.df: Optional[pd.DataFrame] = None
        self._load_database()

    def _load_database(self) -> None:
        """Excel bazasini yuklash"""
        if self.billing_file.exists():
            try:
                self.df = pd.read_excel(self.billing_file)
                logger.info(f"Haftalik to'lovlar bazasi yuklandi: {len(self.df)} ta mijoz mavjud.")
            except Exception as e:
                logger.error(f"Billing Excelni yuklashda xatolik: {e}")
                self.df = None
        else:
            logger.warning(f"Billing fayli topilmadi: {self.billing_file}")
            self.df = None

    def _extract_id(self, text: str) -> Optional[int]:
        """Matndan 3-6 xonali ID raqamni ajratib olish"""
        # "1002", "id 1002", "id: 1002", "ID-1002", "raqamim 1002"
        match = re.search(r"(?:id\s*[:#-]?\s*|\b)(\d{4,6})\b", text, re.IGNORECASE)
        if match:
            return int(match.group(1))
        return None

    def _is_device_complaint(self, text: str) -> bool:
        """Xabar apparat yoki to'lov haqidagi murojaat ekanligini aniqlash"""
        keywords = [
            "ishlamayapti", "ishlamayapdi", "yonmayapti", "o'chib qoldi", "ochib qoldi", 
            "to'xtab qoldi", "toxtab qoldi", "qotib qoldi", "blok", "bloklandi", 
            "xizmat to'xtatildi", "apparat", "terminal", "pos", "paynet", "kassa",
            "nimaga ishlamayapti", "nega ishlamayapti", "ishlamayaptiku", "o'chiq", "yoqilmayapti",
            "pulim", "tugadimi", "balans", "hisobim", "qarzim", "qarz", "to'lov", "tolov",
            "to'langanmi", "sababi nima", "tekshir", "tekshirib ber"
        ]
        text_lower = text.lower()
        return any(kw in text_lower for kw in keywords)

    async def can_handle(self, message: Message, context: Dict[str, Any]) -> bool:
        # 1. Agar kanal yoki guruhga yangi Excel fayl yuborilgan bo'lsa
        if message.document and message.document.file_name:
            fname = message.document.file_name.lower()
            caption = (message.caption or "").lower()
            is_excel = fname.endswith(".xlsx") or fname.endswith(".xls") or fname.endswith(".csv")
            if is_excel:
                # Agar kanalda bo'lsa (har qanday excel) YOKI guruhda to'lov/billing nomli bo'lsa
                if str(message.chat.type).lower() in ["channel", "chattype.channel"] or any(k in fname or k in caption for k in ["billing", "tolov", "to'lov", "hisobot"]):
                    return True

        text = (message.text or message.caption or "").strip()
        if not text:
            return False

        # 2. Buyruqlar
        if text.startswith("/check") or text.startswith("/apparat"):
            return True

        user_id = message.from_user.id if message.from_user else message.chat.id

        # 3. Agar xabarda 3-6 xonali ID bo'lsa (masalan "1001", "1002", "1003", "id 1004")
        if self._extract_id(text):
            return True

        # 4. Agar foydalanuvchi ID kiritish holatida bo'lsa
        if self.user_states.get(user_id) == "WAITING_FOR_ID":
            return True

        # 5. Agar xabarda apparat yoki to'lov bo'yicha shikoyat/savol bo'lsa
        if self._is_device_complaint(text):
            return True

        return False

    async def handle(self, message: Message, context: Dict[str, Any]) -> Optional[PluginResponse]:
        user_id = message.from_user.id if message.from_user else message.chat.id
        text = (message.text or message.caption or "").strip()

        # HOLAT 1: Admin yangi haftalik to'lovlar Excel faylini yubordi
        if message.document and message.document.file_name:
            try:
                self.billing_file.parent.mkdir(parents=True, exist_ok=True)
                file_info = await message.bot.get_file(message.document.file_id)
                await message.bot.download_file(file_info.file_path, destination=self.billing_file)
                self._load_database()
                
                count = len(self.df) if self.df is not None else 0
                reply_text = (
                    f"✅ **Yangi haftalik to'lovlar bazasi yuklandi!**\n\n"
                    f"📁 Fayl: `{message.document.file_name}`\n"
                    f"👥 Ro'yxatdagi mijozlar soni: **{count} ta**\n"
                    f"🔄 Barcha apparat statuslari bir zumda yangilandi."
                )
                await message.reply(reply_text)
                return PluginResponse(text=reply_text, handled=True)
            except Exception as e:
                err_text = f"❌ Faylni yuklashda xatolik: {e}"
                await message.reply(err_text)
                return PluginResponse(text=err_text, handled=True)

        # Bazani tekshirish
        if self.df is None:
            self._load_database()
            if self.df is None:
                err_text = "⚠️ To'lovlar bazasi yuklanmagan. Iltimos, admin bilan bog'laning."
                await message.reply(err_text)
                return PluginResponse(text=err_text, handled=True)

        # Xabardan ID ni qidirish
        found_id = self._extract_id(text)

        # HOLAT 2: Foydalanuvchi shikoyat qildi, lekin ID ko'rsatmadi
        if not found_id and self._is_device_complaint(text):
            self.user_states[user_id] = "WAITING_FOR_ID"
            reply_text = (
                "⚠️ **Apparatingiz to'xtab qolish sababini tekshirish uchun:**\n\n"
                "Iltimos, apparat orqasidagi stikerda yoki shartnomangizda ko'rsatilgan "
                "**Mijoz ID** yoki **Apparat ID** raqamingizni yozib yuboring.\n\n"
                "💡 *Masalan: `1002` yoki `ID 1004`*"
            )
            await message.reply(reply_text)
            return PluginResponse(text=reply_text, handled=True)

        # HOLAT 3: ID topildi -> Excel bazadan 100% ANIQ qidirish (Deterministic Lookup)
        if found_id:
            # Holatni tozalash
            self.user_states.pop(user_id, None)

            # Pandas orqali qidirish
            record = self.df[self.df["Mijoz_ID"] == found_id]

            if record.empty:
                reply_text = (
                    f"🔍 **ID {found_id} bo'yicha ma'lumot topilmadi!**\n\n"
                    "Kechirasiz, ushbu ID raqami haftalik to'lovlar bazasida mavjud emas.\n"
                    "Iltimos, raqamni to'g'ri kiritganingizni tekshirib, qayta urinib ko'ring yoki "
                    "operatorimiz bilan bog'laning: +998 (71) 200-11-22."
                )
                await message.reply(reply_text)
                return PluginResponse(text=reply_text, handled=True)

            row = record.iloc[0]
            fio = row.get("F_I_SH", "Noma'lum")
            model = row.get("Apparat_Modeli", "POS Terminal")
            tolov_status = str(row.get("Tolov_Holati", "")).strip()
            apparat_status = str(row.get("Apparat_Holati", "")).strip()
            qarz = float(row.get("Qarz_Miqdori_som", 0))
            sana = str(row.get("Oxirgi_Tolov_Sanasi", "-"))

            # 3.1: Agar qarzdorlik sababli bloklangan bo'lsa
            if tolov_status.lower() in ["qarzdor", "tolanmagan"] or apparat_status.lower() in ["bloklangan", "to'xtatilgan"]:
                reply_text = (
                    f"⛔ **DIQQAT: Apparat to'xtatilgan (Bloklangan)**\n\n"
                    f"👤 **Mijoz:** {fio}\n"
                    f"🆔 **Mijoz ID:** `{found_id}`\n"
                    f"📟 **Model:** {model}\n"
                    f"🔴 **Holat:** {apparat_status} ({tolov_status})\n"
                    f"💰 **Qarzdorlik miqdori:** **{qarz:,.0f} so'm**\n"
                    f"📅 **Oxirgi to'lov sanasi:** {sana}\n\n"
                    f"⚠️ **Sabab:** Oylik xizmat to'lovi o'z vaqtida to'lanmaganligi sababli tizim apparatni avtomatik bloklagan.\n\n"
                    f"💳 **Yechim:** Qarz to'langach, apparat 10 daqiqa ichida avtomatik ravishda ishga tushadi. "
                    f"To'lov uchun: Payme / Click orqali ID `{found_id}` ni kiriting."
                )
            else:
                # 3.2: Agar to'lov to'langan va apparat faol bo'lsa
                reply_text = (
                    f"✅ **TO'LOV HOLATI: Hammasi joyida (Faol)**\n\n"
                    f"👤 **Mijoz:** {fio}\n"
                    f"🆔 **Mijoz ID:** `{found_id}`\n"
                    f"📟 **Model:** {model}\n"
                    f"🟢 **Holat:** {apparat_status} (Qarzdorlik yo'q)\n"
                    f"📅 **Oxirgi to'lov:** {sana}\n\n"
                    f"🛠️ **Diqqat:** Sizda to'lov bo'yicha hech qanday muammo yo'q. Apparat ishlamayotgan bo'lsa, sabab texnik xarakterga ega:\n"
                    f"1. Apparatni o'chirib, 30 soniyadan keyin qayta yoqing (reboot).\n"
                    f"2. SIM-karta internet aloqasi borligini tekshiring.\n"
                    f"3. Tarmoqqa qayta ulanishni kuting.\n\n"
                    f"Agar baribir ishlamasa, texnik xizmat ko'rsatish bo'limiga murojaat qiling: +998 (71) 200-11-22."
                )

            await message.reply(reply_text)
            return PluginResponse(text=reply_text, handled=True)

        return None
