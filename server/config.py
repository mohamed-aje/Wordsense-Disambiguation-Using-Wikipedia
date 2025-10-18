from pathlib import Path
from dotenv import load_dotenv
import os

BASE_DIR = Path(__file__).resolve().parent

load_dotenv(BASE_DIR.parent / ".env")

AQUAINT_DIR = Path(os.getenv("AQUAINT_DIR", BASE_DIR / "data" / "aquaint"))
DEBUG = os.getenv("DEBUG", "false").strip().lower() in ("1", "true", "yes")

if DEBUG:
    print(f"[DEBUG] Using AQUAINT_DIR={AQUAINT_DIR}")
