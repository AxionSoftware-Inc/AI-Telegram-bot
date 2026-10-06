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
        "🏢 **Tijoriy Mahsulot — tensoric.space**\n\n"
        "Ushbu bot **tensoric.space** ga tegishli maxsus tijoriy mahsulot bo'lib, "
        "faqat **tijoriy maqsadlarda** va **maxsus o'qitilgan sun'iy intellekt (AI)** yordamida ishlatiladi.\n\n"
        "⛔️ **DIQQAT: Botni guruhlarga qo'shish mumkin emas!**\n"
        "Ushbu bot ommaviy yoki shaxsiy guruhlar uchun mo'ljallanmagan. "
        "U faqat **korxonalar uchun maxsus moslashtiribgina (enterprise custom integration)** ishlatilishi mumkin.\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "💼 **Tizimning Korporativ Vazifalari:**\n\n"
        "🔹 **Apparatlar va Billing Monitoringi:**\n"
        "• Telegram kanal orqali yuboriladigan to'lovlar jadvalini (`.xlsx`) avto-sinxronlash;\n"
        "• Mijozlar apparati holati, to'lov va qarzdorlikni ID bo'yicha 100% aniqlikda tekshirish.\n\n"
        "🔹 **Katta Ma'lumotlar va Excel Tahlili (AI Analytics):**\n"
        "• Korxonaning murakkab `.xlsx` hisobotlarini maxsus o'qitilgan AI modeli yordamida chuqur tahlil qilish.\n\n"
        "🔹 **Modulli Microkernel Arxitekturasi:**\n"
        "• Har bir korxona ehtiyojiga mos ravishda yangi funksiyalar va modullar plagin sifatida ulanadi.\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🧩 **O'rnatilgan faol modullar:**\n{plugins_list}\n\n"
        "🌐 **Batafsil ma'lumot va korxonaga moslashtirish:** [tensoric.space](https://tensoric.space)\n"
        "📌 Qo'llanma: `/help` | Modullar: `/plugins`"
    )
    await message.answer(text, disable_web_page_preview=True)


@dp.message(Command("plugins"))
async def cmd_plugins(message: Message):
    text = "🧩 **Tizimda o'rnatilgan faol pluginlar:**\n\n"
    for i, p in enumerate(plugin_manager.plugins, 1):
        text += f"{i}. **{p.name}** (Prioritet: {p.priority})\n   Ta'rif: {p.description}\n\n"
    await message.answer(text)


@dp.message(Command("help"))
async def cmd_help(message: Message):
    text = (
        "📖 **Foydalanish va Xavfsizlik Yo'riqnomasi:**\n\n"
        "⚠️ **Muhim qoida:**\n"
        "Ushbu bot **tensoric.space** tijoriy mahsuloti bo'lib, uni ruxsatsiz guruhlarga qo'shish qat'iyan man etiladi. "
        "Bot faqat korxonaga biriktirilgan maxsus kanal va tizimlar bilan integratsiyada ishlaydi.\n\n"
        "🔹 **Apparat va To'lov tekshiruvi:**\n"
        "• Mijozning ID raqami yuborilganda, to'lovlar bazasidan apparat statusi va qarz holati tekshiriladi.\n\n"
        "🔹 **Kanal orqali avto-sinxronlash:**\n"
        "• Korxona kanali orqali yangi hisobot (`.xlsx`) yuklanganda, bot ma'lumotlar bazasini yangilaydi.\n\n"
        "🔹 **Excel Tahlil (AI):**\n"
        "• Korxona hisoboti yuborilganda, maxsus AI orqali statistika va tahlillar olinadi.\n\n"
        "🌐 **Tizimni korxonangizga moslashtirish uchun:** [tensoric.space](https://tensoric.space)"
    )
    await message.answer(text, disable_web_page_preview=True)


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
            import pandas as pd
            try:
                cnt = len(pd.read_excel(billing_excel))
            except Exception:
                cnt = 50
            from aiogram.types import FSInputFile
            doc = FSInputFile(billing_excel, filename="haftalik_tolovlar_hisoboti.xlsx")
            caption = (
                "📊 **Haftalik to'lovlar va apparatlar holati hisoboti**\n\n"
                f"👥 Bazadagi mijozlar soni: **{cnt} ta**\n"
                "🔄 Guruhdagi barcha apparatlar statusi ushbu fayl asosida real-vaqtda tekshiriladi.\n\n"
                "#billing #monitoring #hisobot"
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
            import pandas as pd
            try:
                cnt = len(pd.read_excel(billing_excel))
            except Exception:
                cnt = 50
            from aiogram.types import FSInputFile
            try:
                doc = FSInputFile(billing_excel, filename="haftalik_tolovlar_hisoboti.xlsx")
                caption = (
                    "📊 **Haftalik to'lovlar va apparatlar holati hisoboti**\n\n"
                    f"👥 Bazadagi mijozlar soni: **{cnt} ta**\n"
                    "🔄 Guruhdagi barcha apparatlar statusi ushbu fayl asosida real-vaqtda tekshiriladi."
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
        bio = "tensoric.space tijoriy mahsuloti. Maxsus o'qitilgan AI orqali korxonalar billing va hisobot nazorati."
        desc = (
            "🏢 tensoric.space tijoriy mahsuloti!\n\n"
            "Ushbu bot faqat tijoriy maqsadlarda va maxsus o'qitilgan sun'iy intellekt (AI) yordamida ishlatiladi.\n\n"
            "⛔️ Botni guruhlarga qo'shish mumkin emas!\n"
            "U faqat korxonalar uchun maxsus moslashtiribgina ishlatiladi.\n\n"
            "✨ Imkoniyatlar:\n"
            "• Apparatlar billing nazorati va qarzdorlikni ID bo'yicha aniqlash\n"
            "• Telegram kanal orqali Excel hisobotlarini avtomatik sinxronlash\n"
            "• Maxsus o'qitilgan AI orqali Excel jadvallarini chuqur tahlil qilish\n\n"
            "Batafsil ma'lumot: https://tensoric.space"
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
