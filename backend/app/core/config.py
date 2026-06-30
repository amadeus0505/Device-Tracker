from pathlib import Path
import os

DATA_DIR = Path(os.getenv("DEVICE_TRACKER_DATA_DIR", "./data")).expanduser().resolve()
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = str(DATA_DIR / "device_tracker.db")
SECRET_KEY = "dev-secret-key-change-me"
ALGORITHM = "HS256"
