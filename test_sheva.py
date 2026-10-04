import sys
import json
import urllib.request
import time

sys.stdout.reconfigure(encoding='utf-8')

system_prompt = """Siz o'zbek tilidagi har xil shevalar (vodiy, Toshkent, voha, Xorazm va b.), so'zlashuv tili, qisqartmalar va sinonimlarni juda yaxshi tushunadigan aqlli tibbiy yordamchisiz.
Guruhdagi xabarning ASL MAZMUNINI tushunib, unga mos toifani aniqlang:

- LOCATION : Manzil, qayerdaligi, qanday borish, joylashuvi (masalan: 'qayoqda', 'qata joylashgan', 'qaysi tarafdasila', 'yo'lni tushuntirvorilar', 'qayerdan topamiz')
- WORKING_HOURS : Ish vaqti, qachon ochiq/yopiqligi (masalan: 'ochumi hozir', 'qachon boraylik', 'kechqurun bo'ladimi', 'dam olish kuniyam ishlisizmi')
- PRICES_SERVICES : Narxlar, xizmat puli, tahlil haqi (masalan: 'nechpul olyapsila', 'qanchaga tushadi', 'baxosi qancha', 'puli necha pul', 'qancha to'lanadi')
- DOCTORS_APPOINTMENT : Shifokorlar, qabulga yozilish (masalan: 'do'xtirla bormi', 'vrach qachon keladi', 'navbat ovolmoqchiydim', 'ko'rsatmoqchiydim')
- CONTACT_INFO : Telefon, aloqa (masalan: 'nomer tashavoring', 'kimga tel qilsak bo'ladi', 'admin bormi')
- EMERGENCY : Shoshilinch, tez yordam, og'ir holat (masalan: 'tez yordam kerak', 'shoshilinch bormoqchiymiz')
- NONE : Klinikaga umuman aloqasi yo'q xabarlar (salom-alik, boshqa mavzular, ob-havo, mashina, futbol va b.)

Javobingiz FAQAT bitta toifa kodi bo'lsin (masalan: LOCATION, PRICES_SERVICES, WORKING_HOURS, DOCTORS_APPOINTMENT, CONTACT_INFO, EMERGENCY yoki NONE). Hech qanday boshqa so'z qo'shmang!"""

sheva_tests = [
    "Qayoqda o'zi bu joy, yo'lini tushuntirvorilar?",
    "UZI nechpul bo'lyapti hozir, qanchaga tushadi?",
    "Ertalab soat 7 da borsam ochiladimi klinika?",
    "Yaxshi kardiolog do'xtir bormi sizlarda, ko'rinmoqchiydik?",
    "Admin nomerini tashavoring gaplashib olaylik",
    "Bratva bugun choyxona bormi oqshomga?",
    "Bemor judayam og'ir ahvolda shoshilinch tez yordam kerak!",
    "Shu analiz necha pul turadi?",
    "Iya bugun qor yog'votti-ku"
]

print("Sinov boshlandi...")
for q in sheva_tests:
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Xabar: «{q}»\nToifa:"}
    ]
    data = json.dumps({
        "model": "qwen3-8b-local",
        "messages": messages,
        "stream": False,
        "options": {"temperature": 0.0, "num_predict": 20}
    }).encode("utf-8")
    
    req = urllib.request.Request(
        "http://localhost:11434/api/chat",
        data=data,
        headers={"Content-Type": "application/json"}
    )
    t0 = time.time()
    try:
        with urllib.request.urlopen(req) as resp:
            res = json.loads(resp.read().decode("utf-8"))
            ans = res.get("message", {}).get("content", "").strip()
            print(f"{ans:20} | {round(time.time()-t0, 2)}s | {q}")
    except Exception as e:
        print(f"Xato: {e}")
