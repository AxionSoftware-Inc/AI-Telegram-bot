import sys
import json
import urllib.request
import time

sys.stdout.reconfigure(encoding='utf-8')

system_prompt = """Siz klinikaga kelgan Telegram xabarlarini tahlil qilasiz.
Foydalanuvchi xabari mazmuniga qarab quyidagi toifalardan birini JSON formatida qaytaring:
Toifalar:
- LOCATION : Manzil, qayerdaligi, mo'ljal, metro, avtobus, qanday borish
- WORKING_HOURS : Ish vaqti, qachon ochiq/yopiq, ertalab yoki kechqurun borish, ish kunlari
- PRICES_SERVICES : Narxlar, tahlil (qon, siydik topshirish), UZI, MRT, xizmat bormi/yo'qmi, to'lov
- DOCTORS_APPOINTMENT : Shifokorlar (kardiolog, vrach, terapevt), ko'rikka yozilish, navbat, davolanish
- CONTACT_INFO : Telefon, administrator bilan bog'lanish, kimdir bilan gaplashish
- EMERGENCY : Tez yordam, og'ir bemor, kechasi qabul
- NONE : Klinikaga aloqasi yo'q gaplar (ob-havo, salom-alik, futbol)

Format: {"category": "TOIFA_NOMI"}"""

queries = [
    'ertaga ertalab boraylikmi sizlarga?',
    'borib kelishga qancha pul olib olay yonimga?',
    'sizlarda qon topshirsak boladimi?',
    'yurakni tekshirtirmoqchiman',
    'avtobus qaysi boradi sizlarga?',
    'biror odam bormi gaplashadigan?',
    'salom qalaysizlar qor yogvottimi?'
]

for q in queries:
    req = urllib.request.Request(
        'http://localhost:11434/api/chat',
        data=json.dumps({
            'model': 'qwen3-8b-local',
            'messages': [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': f'Xabar: «{q}»'}
            ],
            'stream': False,
            'format': 'json',
            'options': {'temperature': 0.0}
        }).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    t0 = time.time()
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode('utf-8'))
        raw = res['message']['content'].strip()
        print(f"{q:45} | {round(time.time()-t0, 2)}s | {raw}")
