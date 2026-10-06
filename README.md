# 🤖 Universal AI Telegram Bot Engine (Plugin Architecture)

Ushbu loyiha — modulli va **Pluginli arxitektura (Microkernel Engine)** asosida qurilgan, mahalliy sun'iy intellekt modellari (**Gemma 4-26B**, **Qwen** va boshqalar) bilan ishlovchi ko'p tarmoqli Telegram bot tizimidir.

Bot kanallar, guruhlar va shaxsiy xabarlar orqali korporativ ma'lumotlarni (Excel, to'lovlar, shikoyatlar, FAQ) qabul qilib, ularni deterministik algoritmlar va sun'iy intellekt orqali **100% aniqlikda** tahlil qiladi.

---

## 🏛️ Arxitektura tuzilishi

```
d:\Telegram bot\
├── core\                      # 🧠 ASOSIY YADRO (O'zgarmas dvigatel)
│   ├── plugin_base.py         # Abstract BasePlugin va PluginResponse
│   ├── plugin_manager.py      # Pluginlarni dinamik kashf qiluvchi va boshqaruvchi menejer
│   └── llm_client.py          # Ollama (Gemma 4, Qwen) bilan umumiy aloqa klienti
├── plugins\                   # 🧩 PLUGINLAR (Istalgan yangi funksiyalar)
│   ├── device_billing_plugin.py # 📟 Apparatlar & haftalik to'lovlarni tekshiruvchi plugin
│   ├── excel_plugin.py        # 📊 Excel (.xlsx) fayllarni tahlil qilish (Gemma 4)
│   └── clinic_faq_plugin.py   # 🏥 Shevalar va tibbiy savollarga avto-javob (FAQ)
├── data\                      # 📁 MA'LUMOTLAR BAZASI
│   ├── billing\
│   │   └── haftalik_tolovlar.xlsx # Haftalik to'lovlar va qarzdorliklar bazasi
│   └── klinika_hisoboti.xlsx  # Ko'p varaqli demo klinika hisoboti
├── tests\                     # 🧪 Sinov skriptlari
├── bot.py                     # 🚀 Asosiy Telegram bot kirish nuqtasi
├── config.py                  # ⚙️ Konfiguratsiya yuklagich
├── .env.example               # 📄 Sozlamalar namunasi
├── requirements.txt           # 📦 Python kutubxonalari
└── run.bat                    # 🖱️ Windows uchun bir bosishda ishga tushirish
```

---

## 🧩 O'rnatilgan Pluginlar va Imkoniyatlar

### 1. `DeviceBilling` Plugini (Apparatlar & To'lovlar monitoringi)
* **Kanal orqali avto-sinxronizatsiya:** Adminlar kanalga har hafta yangi Excel fayl tashlaganida, bot uni darhol ushlab oladi va to'lovlar bazasini yangilaydi.
* **Guruhda muammolarni tekshirish:** Guruhda odamlar *"apparatim ishlamayapti"*, *"pulim tugadimi"* deb yozganida, bot mijoz ID sini so'raydi.
* **100% Xatosiz natija (Deterministic lookup):** ID kiritilganda (`1001`, `1002`, `1004` va h.k.) bot sonlar va statuslarni gallyutsinatsiyasiz, to'g'ridan-to'g'ri jadvaldan tekshirib chiqarib beradi:
  - *Qarzdor bo'lsa:* Qarz miqdori va to'lov yo'riqnomasini yuboradi.
  - *Faol bo'lsa:* To'lov joyidaligini va texnik restart (reboot) qilish tartibini tushuntiradi.

### 2. `ExcelAnalyzer` Plugini (Gemma 4-26B tahlilchisi)
* **Xohlagan Excel jadval bilan ishlash:** Botga istalgan `.xlsx` yoki `.csv` fayl yuborilganda, uni o'qiydi.
* **Tabiiy tildagi savollar:** Jadval bo'yicha berilgan savollarga (masalan: *"Eng ko'p daromad keltirgan xizmat qaysi?"*, *"Jami tushum qancha?"*) **Gemma 4-26B** modeli orqali o'zbek tilida tahliliy hisobot beradi.
* **Demo rejimi:** `/excel` komandasi orqali tayyor klinika hisobotini sinab ko'rish mumkin.

### 3. `ClinicFAQ` Plugini (Shevalar va so'zlashuv tili)
* Toshkent, Vodiy, Voha va boshqa shevalardagi so'zlarni tushunadi.
* Guruhdagi begona mavzularga (futbol, ob-havo) mutlaqo aralashmaydi (jim turadi).
* Manzil, ish vaqti, narxlar bo'yicha tayyor shablon javoblarni `reply` qiladi.

---

## 🚀 Qanday qilib yangi Plugin qo'shish mumkin?

Yangi format (PDF, Word, OCR yoki SQL) qo'shish uchun asosiy kodga tegish shart emas! Shunchaki `plugins/` papkasida yangi `.py` fayl oching:

```python
from core.plugin_base import BasePlugin, PluginResponse

class PDFAnalyzerPlugin(BasePlugin):
    name = "PDFAnalyzer"
    description = "PDF shartnomalarni tahlil qilish"
    priority = 30

    async def can_handle(self, message, context) -> bool:
        return message.document and message.document.file_name.endswith(".pdf")

    async def handle(self, message, context) -> PluginResponse:
        # Faylni o'qish va tahlil qilish mantiqi
        return PluginResponse(text="PDF muvaffaqiyatli tahlil qilindi!", handled=True)
```
Bot qayta ishga tushganda yangi pluginni **avtomatik aniqlab ulaydi**.

---

## ⚙️ O'rnatish va Ishga tushirish

### 1. Talablar:
- Python 3.10+
- [Ollama](https://ollama.ai/) (Gemma 4-26B yoki Qwen modellari bilan)

### 2. Kutubxonalarni o'rnatish:
```bash
pip install -r requirements.txt
```

### 3. Konfiguratsiya:
`.env.example` faylidan nusxa olib `.env` yarating:
```env
BOT_TOKEN=sizning_bot_tokeningiz
OLLAMA_URL=http://localhost:11434
MODEL_NAME=gemma4-26b:latest
COOLDOWN_SECONDS=5
```

### 4. Ishga tushirish:
Windows muhitida shunchaki `run.bat` faylini bosing yoki terminalda:
```bash
python bot.py
```

---

## 🔐 Xavfsizlik
- `.env` fayli va maxfiy tokenlar `.gitignore` orqali himoyalangan.
- Har qanday mijoz va loyiha uchun alohida sozlamalarni xavfsiz boshqarish mumkin.
