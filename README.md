# Telegram Klinika AI Yordamchi Boti

Ushbu dastur Telegram guruhdagi barcha xabarlarni o'qib boradi va mahalliy (offline) sun'iy intellekt modeli orqali tahlil qilib, faqat klinikaga tegishli xabarlarga avvaldan tayyorlangan to'g'ri javoblarni tanlab `reply` tariqasida yuboradi.

## Asosiy imkoniyatlar:
- **Guruhdagi barcha xabarlarni kuzatish:** Guruh a'zolarining savollarini ushlab oladi.
- **Aqlli saralash (Zero Spam):** Klinikaga tegishli bo'lmagan shaxsiy suhbatlar, ob-havo, minnatdorchilik, hazillarga mutlaqo aralashmaydi (jim turadi).
- **Gibrid tezkor tahlil:** Aniq kalit so'zlar bo'yicha 0.001 soniyada, murakkab savollarda esa mahalliy LLM orqali tahlil qiladi.
- **Tayyor sintetik ma'lumotlar bazasi (`clinic_data.json`):**
  - Manzil va lokatsiya (mo'ljal, metro, karta)
  - Ish vaqti va kunlari (hafta kunlari, dam olish kunlari)
  - Xizmatlar va narxlar (ko'rik, MRT, UZI, tahlillar)
  - Shifokorlar va qabulga yozilish (mutaxassislar, navbat olish)
  - Aloqa va ma'muriyat telefon raqamlari
  - 24/7 tez yordam va shoshilinch bo'lim
- **Mahalliy AI modellarni qo'llab-quvvatlash:**
  - `qwen3-8b-local` (O'zbek tilini tushunish bo'yicha eng yuqori aniqlik)
  - `qwen2.5-1.5b` (D diskdagi 1.5B GGUF modeli)
  - `qwen-test` (D diskdagi 1.7B Q8_0 GGUF modeli)

---

## O'rnatish va Ishga tushirish

1. **Telegram sozlamasi (BotFather):**
   - `@BotFather` ga kiring va `/mybots` buyrug'ini yuboring.
   - O'zingizning botingizni tanlang (`@aiuchuntest_bot`).
   - **Bot Settings** -> **Allow Groups?** -> **Turn groups on** (Botni guruhga qo'shishga ruxsat berish).
   - **Bot Settings** -> **Group Privacy** -> **Turn off** (Guruhdagi barcha xabarlarni o'qish imkoniyati).

2. **Ishga tushirish:**
   - Shunchaki `run.bat` faylini ikki marta bosing yoki terminalda:
     ```bash
     python bot.py
     ```

3. **Guruhga qo'shish va sinash:**
   - Botni kerakli guruhga qo'shing.
   - Guruhda xabar yozing (masalan: *"Klinika qayerda joylashgan?"* yoki *"MRT narxi qancha?"*).
   - Bot bir necha soniyada javob qaytaradi.
