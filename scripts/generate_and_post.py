import sys
import random
import requests
import pandas as pd
from datetime import datetime, timedelta

sys.stdout.reconfigure(encoding='utf-8')

names = [
    ("Karimov", "Sanjarbek"), ("Aliyeva", "Malika"), ("Rustamov", "Davron"),
    ("Saidov", "Jasur"), ("Nazarova", "Shahnoza"), ("Tursunov", "Bahodir"),
    ("Ismoilov", "Aziz"), ("Yusupov", "Jamshid"), ("Qodirova", "Nilufar"),
    ("Mirzayev", "Sherzod"), ("Ergashev", "Otabek"), ("Holmatova", "Dildora"),
    ("Rahimov", "Farhod"), ("Usmonova", "Ziyoda"), ("Murodov", "Bekzod"),
    ("Soliyev", "Ilhom"), ("Jalilov", "Sarvar"), ("Toshmatova", "Gulnoza"),
    ("Abdullayev", "Umid"), ("Zokirov", "Bobur"), ("Sharipov", "Mansur"),
    ("Ganiyeva", "Madina"), ("Sobirov", "Akmal"), ("Nurmatov", "Sardor"),
    ("Xolmirzayev", "Jahongir"), ("Azimov", "Dilshod"), ("Ibrohimov", "Anvar"),
    ("Komilova", "Nargiza"), ("Botirov", "Elyor"), ("Normatov", "Ulug'bek"),
    ("Yoqubov", "Shavkat"), ("Rahmatullayev", "Nodir"), ("Qosimov", "Alisher"),
    ("Sultonov", "Doniyor"), ("Po'latov", "Rustam"), ("Oripov", "Farrux"),
    ("Xudoyberdiyev", "Jasurbek"), ("Matyoqubov", "Botir"), ("Kenjayev", "Asqar"),
    ("Davlatov", "San'at"), ("Tojiboyev", "Muzaffar"), ("Inomov", "Xurshid"),
    ("Haydarova", "Go'zal"), ("Valiyev", "Sherali"), ("Muxtorov", "Zohid"),
    ("Eshonov", "Abduvali"), ("Qurbonov", "Rustambek"), ("Shoimov", "Akbar"),
    ("Ne'matov", "Shuhrat"), ("Ortiqov", "Mirjalol")
]

regions = ["Toshkent sh.", "Samarqand", "Farg'ona", "Andijon", "Namangan", "Buxoro", "Qashqadaryo", "Xorazm"]
models = ["SmartPOS X-900", "PayNet Pro 5", "Terminal V-20", "PAX A930", "Sunmi V2"]
tariffs = ["Standart (60 000)", "Biznes (120 000)", "Premium (250 000)"]

random.seed(42)
records = []

for i, (last, first) in enumerate(names):
    mid = 2001 + i
    fio = f"{last} {first}"
    reg = random.choice(regions)
    mod = random.choice(models)
    tar = random.choice(tariffs)
    
    # 40% qarzdor, 60% to'langan
    is_debtor = (i % 5 == 1 or i % 5 == 3)
    
    if is_debtor:
        status_pay = "Qarzdor"
        status_dev = "Bloklangan"
        debt_amount = random.choice([50000, 75000, 95000, 120000, 150000, 210000, 320000])
        days_ago = random.randint(35, 75)
    else:
        status_pay = "Tolangan"
        status_dev = "Faol"
        debt_amount = 0
        days_ago = random.randint(1, 15)
        
    pay_date = (datetime(2026, 10, 6) - timedelta(days=days_ago)).strftime("%d.%m.%Y")
    
    records.append({
        "Mijoz_ID": mid,
        "F_I_SH": fio,
        "Hudud": reg,
        "Apparat_Modeli": mod,
        "Tarif_Rejasi": tar,
        "Tolov_Holati": status_pay,
        "Qarz_Miqdori_som": debt_amount,
        "Apparat_Holati": status_dev,
        "Oxirgi_Tolov_Sanasi": pay_date
    })

df = pd.DataFrame(records)

file_path_weekly = "d:/Telegram bot/data/billing/haftalik_tolovlar.xlsx"
file_path_new = "d:/Telegram bot/data/billing/haftalik_tolovlar_kengaytirilgan.xlsx"

df.to_excel(file_path_weekly, index=False)
df.to_excel(file_path_new, index=False)

debtors_cnt = len(df[df["Tolov_Holati"] == "Qarzdor"])
paid_cnt = len(df[df["Tolov_Holati"] == "Tolangan"])

print(f"Excel fayllar saqlandi: {len(df)} ta mijoz.")
print(f"Faol to'langan: {paid_cnt} ta, Bloklangan qarzdor: {debtors_cnt} ta.")

token = "8883859628:AAGtmZiljCOgfgjRalpm5rlt0KhalQr2I2w"
channel_id = -1004356431564
url = f"https://api.telegram.org/bot{token}/sendDocument"

caption = (
    "📊 2026-YIL OKTYABR OYI UCHUN YANGILANGAN KATTA BAZA (50 TA MIJOZ)\n\n"
    f"👥 Jami ro'yxat: {len(df)} ta mijoz\n"
    f"🟢 Faol apparatlar: {paid_cnt} ta\n"
    f"🔴 Bloklangan (Qarzdor): {debtors_cnt} ta\n"
    "🆔 Yangi ID lar diapazoni: 2001 dan 2050 gacha\n\n"
    "🔄 Guruhdagi barcha apparatlar holati avtomatik tarzda ushbu yangilangan bazaga ulandi!\n"
    "#billing #hisobot #baza"
)

with open(file_path_new, "rb") as f:
    resp = requests.post(
        url,
        data={"chat_id": channel_id, "caption": caption},
        files={"document": ("haftalik_tolovlar_kengaytirilgan.xlsx", f)}
    )

res_json = resp.json()
print("Kanalga yuklash natijasi:", res_json.get("ok"))
if res_json.get("ok"):
    print("Muvaffaqiyatli! Post ID:", res_json.get("result", {}).get("message_id"))
else:
    print("Xatolik:", res_json)
