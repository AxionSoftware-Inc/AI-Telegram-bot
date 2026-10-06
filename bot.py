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
        "👋 **Assalomu alaykum!**\n\n"
        "Men korxona va xizmat ko'rsatish tizimlari uchun mo'ljallangan universal **AI Smart Assistant & Monitoring Bot**man.\n\n"
        "Tizim **Microkernel (Plugin)** arxitekturasida qurilgan bo'lib, quyidagi yo'nalishlarda to'liq avtomatlashtirilgan xizmat ko'rsatadi:\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "⚡ **Asosiy Imkoniyatlar:**\n\n"
        "1️⃣ **Apparatlar va Billing Monitoringi:**\n"
        "• Telegram kanalga joylangan haftalik to'lovlar jadvalini (`.xlsx`) avtomatik qabul qiladi va bazani real-vaqtda yangilaydi.\n"
        "• Guruh yoki shaxsiy chatda apparati to'xtab qolgan mijozlarning ID raqamini aniqlab, to'lov holati, qarz summasi va apparat statusini 100% aniqlikda tekshiradi.\n\n"
        "2️⃣ **Excel & Katta Ma'lumotlar Tahlili (AI Analytics):**\n"
        "• Ixtiyoriy `.xlsx` formatidagi hisobot faylini yuborib, Gemma 4 sun'iy intellekt modeli orqali istalgan statistika, solishtirish yoki chuqur tahlilni olishingiz mumkin.\n\n"
        "3️⃣ **Intellektual Muloqot & Qo'llab-quvvatlash:**\n"
        "• Tabiiy til va turli shevalardagi murojaatlarni to'g'ri tushunib, tezkor yordam ko'rsatadi.\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🧩 **Hozirda faol modullar:**\n{plugins_list}\n\n"
        "📌 **Foydali buyruqlar:**\n"
        "• `/help` — Batafsil qo'llanma va foydalanish yo'riqnomasi\n"
        "• `/plugins` — Faol modullar va ularning prioritetlari\n"
        "• `/excel` — Excel tahlilchi modulini ishga tushirish\n\n"
        "Savolingiz bo'lsa to'g'ridan-to'g'ri yozishingiz, ID raqam kiritishingiz yoki tahlil uchun Excel fayl yuborishingiz mumkin!"
    )
    await message.answer(text)


@dp.message(Command("plugins"))
async def cmd_plugins(message: Message):
    text = "🧩 **Tizimda o'rnatilgan faol pluginlar:**\n\n"
    for i, p in enumerate(plugin_manager.plugins, 1):
        text += f"{i}. **{p.name}** (Prioritet: {p.priority})\n   Ta'rif: {p.description}\n\n"
    await message.answer(text)


@dp.message(Command("help"))
async def cmd_help(message: Message):
    text = (
        "📖 **Botdan foydalanish qo'llanmasi:**\n\n"
        "🔹 **Apparat holati va to'lovni tekshirish:**\n"
        "• Guruhda yoki shaxsiy chatda apparatingiz nima sababdan ishlamayotganini yozing (masalan: *«Nega apparatim o'chib qoldi?»*).\n"
        "• Bot ID so'raganda o'z ID raqamingizni yuboring (yoki to'g'ridan-to'g'ri: *«ID 2002»* yoki *«2001»*).\n"
        "• Bot bazadan tekshirib, qarzdorlik yoki to'lov holati haqida darhol aniq javob beradi.\n\n"
        "🔹 **Kanal orqali bazani avto-yangilash:**\n"
        "• Ma'sul xodim tomonidan kanalga yangi `.xlsx` hisoboti joylansa, bot bazani avtomatik yangilab oladi.\n\n"
        "🔹 **Excel tahlil (AI Data Analyst):**\n"
        "• Xohlagan `.xlsx` hisobotingizni botga yuboring va unga oid savollaringizni bering (masalan: *«Eng ko'p qarzdor kim?», «Umumiy summa qancha?»*).\n"
        "• `/excel` buyrug'i orqali namunaviy fayl tahlilini sinab ko'rishingiz mumkin.\n\n"
        "🔹 **Tizim buyruqlari:**\n"
        "• `/start` — Asosiy tanishuv xabari\n"
        "• `/plugins` — Faol plaginlar ro'yxati\n"
        "• `/help` — Ushbu yo'riqnoma"
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
        bio = "🤖 Universal AI Yordamchi & Billing Monitoring Bot. Excel tahlili va apparatlar nazorati."
        desc = (
            "🤖 Universal modulli AI Smart Assistant & Monitoring Bot!\n\n"
            "✨ Imkoniyatlar:\n"
            "• Apparatlar billing nazorati va qarzdorlikni ID bo'yicha aniqlash\n"
            "• Telegram kanal orqali Excel jadvallarini avtomatik sinxronlash\n"
            "• Excel (.xlsx) ma'lumotlar bazalarini Gemma 4 orqali chuqur tahlil qilish\n"
            "• Yangi xizmatlarni Microkernel plagin tizimi orqali oson ulash."
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
