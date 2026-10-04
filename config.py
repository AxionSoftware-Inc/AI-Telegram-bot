import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "").strip()
MODEL_NAME = os.getenv("MODEL_NAME", "google/gemini-2.5-flash-lite").strip()
COOLDOWN_SECONDS = int(os.getenv("COOLDOWN_SECONDS", "10"))
CLINIC_DATA_PATH = BASE_DIR / "clinic_data.json"
