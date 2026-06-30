from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = str(DATA_DIR / "device_tracker.db")
SECRET_KEY = "dev-secret-key-change-me"
ALGORITHM = "HS256"
