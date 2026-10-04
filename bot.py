import asyncio
import logging
import time
from typing import Dict

from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode, ChatType
from aiogram.filters import Command, CommandStart
from aiogram.types import Message
from aiogram.client.default import DefaultBotProperties

from config import BOT_TOKEN, MODEL_NAME, COOLDOWN_SECONDS
from classifier import ClinicClassifier

# Logging sozlamalari
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("ClinicBot")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN ko'rsatilmagan! .env faylini tekshiring.")

# Bot va Dispatcher yaratish
bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN)
)
dp = Dispatcher()
classifier = ClinicClassifier()

# Spam / Cooldown nazorati (chat_id: timestamp)
last_reply_times: Dict[int, float] = {}


@dp.message(CommandStart())
async def cmd_start(message: Message):
    """Start komandasi"""
    text = (
        f"🏥 **Assalomu alaykum!**\n\n"
        f"Men **«{classifier.clinic_name}»** avtomatlashtirilgan yordamchi botiman.\n\n"
        f"Guruhdagi xabarlarni o'qib, klinika bo'yicha berilgan savollarga (manzil, ish vaqti, narxlar, shifokorlar, aloqa) "
        f"tayyor javoblarni tanlab uzatib turaman.\n\n"
        f"💡 **Sinash uchun biror savol yozing:**\n"
        f"• *Klinika qayerda joylashgan?*\n"
        f"• *MRT va UZI narxi qancha?*\n"
        f"• *Yakshanba kuni ishlaysizlarmi?*\n"
        f"• *Shifokor qabuliga qanday yozilsa bo'ladi?*"
    )
    await message.answer(text)


@dp.message(Command("help"))
async def cmd_help(message: Message):
    """Help komandasi"""
    text = (
        "ℹ️ **Bot qanday ishlaydi?**\n\n"
        "1. Botni Telegram guruhga qo'shing.\n"
        "2. Guruh a'zolari klinika haqida (ish vaqti, narxlar, shifokorlar, manzil va h.k.) savol berganida, "
        "sun'iy intellekt modeli savolni avtomatik tahlil qilib, mos tayyor javobni yuboradi.\n"
        "3. Klinikaga aloqador bo'lmagan oddiy gaplarga bot e'tibor bermaydi (spam bo'lmaydi)."
    )
    await message.answer(text)


@dp.message(Command("model"))
async def cmd_model(message: Message):
    """Model holati"""
    text = (
        f"🤖 **Model holati:**\n"
        f"• Model: `{MODEL_NAME}`\n"
        f"• Lokatsiya: Mahalliy (Ollama / Local GPU)\n"
        f"• Klinikaga tegishli toifalar soni: {len(classifier.categories)}"
    )
    await message.answer(text)


@dp.message(F.text)
async def handle_message(message: Message):
    """Barcha matnli xabarlarni tahlil qilish"""
    # Botning o'z xabarlariga javob bermaslik
    if message.from_user and message.from_user.is_bot:
        return

    text = message.text.strip()
    chat_id = message.chat.id
    is_group = message.chat.type in [ChatType.GROUP, ChatType.SUPERGROUP]

    # Guruhda tez-tez spam qilmaslik uchun cooldown tekshiruvi
    now = time.time()
    if is_group and (now - last_reply_times.get(chat_id, 0)) < COOLDOWN_SECONDS:
        # Hozirgina javob berilgan bo'lsa, biroz kutish
        return

    # Model orqali xabarni klassifikatsiya qilish
    category, response_text = await classifier.classify_message(text)

    if response_text:
        last_reply_times[chat_id] = now
        logger.info(f"Chat {chat_id} | Toifa: {category} | Reply yuborildi.")
        try:
            await message.reply(response_text)
        except Exception as e:
            logger.error(f"Xabar yuborishda xatolik: {e}")
    else:
        # Agar shaxsiy yozishmada (PM) bo'lsa va klinika savoli bo'lmasa, yo'naltirish
        if not is_group and not text.startswith("/"):
            await message.answer(
                "Tushunmadim. Klinikamiz xizmatlari, narxlar, manzil yoki shifokorlar haqida so'rashingiz mumkin."
            )


async def main():
    logger.info("Bot ishga tushmoqda...")
    logger.info(f"Ishlatilayotgan model: {MODEL_NAME}")
    # Eskirgan update larni o'chirib yuborish
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
