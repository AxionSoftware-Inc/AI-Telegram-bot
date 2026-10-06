import asyncio
import logging
from typing import Dict, Any

from pathlib import Path
from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, ChatMemberUpdated, FSInputFile
from aiogram.client.default import DefaultBotProperties

from config import BOT_TOKEN
from core.plugin_manager import PluginManager

# Logging sozlamalari
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("CoreBot")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN ko'rsatilmagan! .env faylini tekshiring.")

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN)
)
dp = Dispatcher()
plugin_manager = PluginManager()


@dp.message(CommandStart())
async def cmd_start(message: Message):
    plugins_list = "\n".join([f"• **{p.name}** — {p.description}" for p in plugin_manager.plugins])
    text = (
        f"🏥 **Assalomu alaykum!**\n\n"
        f"Men modulli va pluginli arxitekturada ishlovchi **AI Yordamchi Bot**man.\n\n"
        f"🧩 **Faol pluginlar:**\n{plugins_list}\n\n"
        f"💡 **Imkoniyatlar:**\n"
        f"1. Guruhda klinika savollariga avtomatik javob berish\n"
        f"2. `/excel` buyrug'i orqali klinika hisobotini Gemma 4 modeli orqali tahlil qilish\n"
        f"3. Ixtiyoriy `.xlsx` fayl yuborib, undan xohlagan statistikani so'rash!"
    )
    await message.answer(text)


@dp.message(Command("plugins"))
async def cmd_plugins(message: Message):
    text = "🧩 **O'rnatilgan pluginlar ro'yxati:**\n\n"
    for i, p in enumerate(plugin_manager.plugins, 1):
        text += f"{i}. **{p.name}** (Prioritet: {p.priority})\n   Ta'rif: {p.description}\n\n"
    await message.answer(text)


@dp.message(Command("help"))
async def cmd_help(message: Message):
    text = (
        "ℹ️ **Qo'llanma va komandalar:**\n\n"
        "• `/start` — Botni qayta ishga tushirish\n"
        "• `/plugins` — Faol pluginlar ro'yxati\n"
        "• `/excel` — Klinika Excel hisoboti demosini ochish va Gemma 4 tahlili\n"
        "• *Excel fayl yuklash:* `.xlsx` formatidagi faylni shunchaki botga yuboring va savol bering!\n"
        "• *Klinika savollari:* Guruhda manzil, narx, shifokor va ish vaqtlari bo'yicha savol bering."
    )
    await message.answer(text)


@dp.message()
async def global_message_handler(message: Message):
    """Barcha kiruvchi xabarlar (guruh va shaxsiy) pluginlar menejeriga yo'naltiriladi"""
    if message.from_user and message.from_user.is_bot:
        return

    text_preview = message.text or message.caption or (message.document.file_name if message.document else "Fayl/Media")
    logger.info(f"Yangi xabar [{message.chat.type} | ID: {message.chat.id}]: '{text_preview}'")

    context: Dict[str, Any] = {
        "chat_id": message.chat.id,
        "chat_type": message.chat.type
    }
    await plugin_manager.process_message(message, context)


@dp.channel_post()
async def global_channel_post_handler(message: Message):
    """Kanalga kelgan yangi post va Excel fayllarni qabul qilish va bazani avto-yangilash"""
    chat_id = message.chat.id
    title = message.chat.title or "Kanal"
    text_preview = message.text or message.caption or (message.document.file_name if message.document else "Post")
    logger.info(f"Kanal posti qabul qilindi [{title} | ID: {chat_id}]: '{text_preview}'")

    channel_file = Path("data/channel_id.txt")
    channel_file.parent.mkdir(parents=True, exist_ok=True)
    channel_file.write_text(str(chat_id))

    if message.document:
        context: Dict[str, Any] = {
            "chat_id": chat_id,
            "chat_type": "channel"
        }
        await plugin_manager.process_message(message, context)
    else:
        # Kanaldagi har qanday xabarga javoban avtomatik Excel faylni kanalga yuklash
        billing_excel = Path("data/billing/haftalik_tolovlar.xlsx")
        if billing_excel.exists():
            from aiogram.types import FSInputFile
            doc = FSInputFile(billing_excel, filename="haftalik_tolovlar_oktyabr.xlsx")
            caption = (
                "📊 **2026-yil Oktyabr oyi haftalik to'lovlar va qarzdorliklar hisoboti**\n\n"
                "👥 Jami mijozlar: **10 ta**\n"
                "🔄 Guruhdagi barcha apparatlar statusi ushbu fayl asosida avtomatik tekshiriladi.\n\n"
                "#billing #hisobot"
            )
            await message.answer_document(document=doc, caption=caption)
            logger.info(f"Excel fayl kanalga ({chat_id}) muvaffaqiyatli joylandi!")


@dp.my_chat_member()
async def on_my_chat_member(event: ChatMemberUpdated):
    """Bot kanal yoki guruhga qo'shilganda ishlaydi"""
    chat_id = event.chat.id
    title = event.chat.title or "Chat"
    logger.info(f"Bot yangi chatga qo'shildi: chat_id={chat_id}, title='{title}', type={event.chat.type}")
    
    if "channel" in str(event.chat.type).lower():
        channel_file = Path("data/channel_id.txt")
        channel_file.parent.mkdir(parents=True, exist_ok=True)
        channel_file.write_text(str(chat_id))
        
        billing_excel = Path("data/billing/haftalik_tolovlar.xlsx")
        if billing_excel.exists():
            from aiogram.types import FSInputFile
            try:
                doc = FSInputFile(billing_excel, filename="haftalik_tolovlar_oktyabr.xlsx")
                caption = (
                    "📊 **2026-yil Oktyabr oyi haftalik to'lovlar va qarzdorliklar hisoboti**\n\n"
                    "👥 Jami mijozlar: **10 ta**\n"
                    "🔄 Guruhdagi barcha apparatlar statusi ushbu fayl asosida avtomatik tekshiriladi."
                )
                await bot.send_document(chat_id=chat_id, document=doc, caption=caption)
                logger.info(f"Excel fayl kanalga ({chat_id}) yuborildi!")
            except Exception as e:
                logger.error(f"Kanalga fayl yuborishda xatolik: {e}")


async def main():
    logger.info("Yadro yuklanmoqda va pluginlar ro'yxatdan o'tkazilmoqda...")
    plugin_manager.load_plugins()
    await plugin_manager.startup()

    # Bio va Description sozlamalari
    try:
        bio = "🏥 AI Yordamchi & Ma'lumotlar tahlilchisi. Klinika FAQ va Excel (.xlsx) jadvallarini Gemma 4 da tahlil qiladi."
        desc = (
            "🏥 Pluginli arxitekturadagi ko'p funksiyali AI Bot!\n\n"
            "✨ Imkoniyatlar:\n"
            "• Klinika bo'yicha FAQ va shevalardagi savollarga avtomatik javoblar\n"
            "• Excel (.xlsx) jadvallarini yuklab, Gemma 4-26B orqali chuqur tahlil qilish\n"
            "• Istalgan yangi format va tool'larni plugin sifatida ulash imkoniyati."
        )
        await bot.set_my_short_description(short_description=bio[:120])
        await bot.set_my_description(description=desc)
    except Exception as e:
        logger.warning(f"Bio o'rnatishda ogohlantirish: {e}")

    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("Bot tayyor! Polling boshlandi...")
    await dp.start_polling(
        bot,
        allowed_updates=["message", "edited_message", "channel_post", "edited_channel_post", "my_chat_member", "chat_member"]
    )


if __name__ == "__main__":
    asyncio.run(main())
