import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434").strip()
MODEL_NAME = os.getenv("MODEL_NAME", "qwen3-8b-local").strip()
COOLDOWN_SECONDS = int(os.getenv("COOLDOWN_SECONDS", "10"))
CLINIC_DATA_PATH = BASE_DIR / "clinic_data.json"
