from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
UPLOAD_DIR = BASE_DIR / "uploads"
OUTPUT_DIR = BASE_DIR / "output_csv"
LOG_DIR = BASE_DIR / "logs"
DB_DIR = BASE_DIR / "db"
DB_PATH = DB_DIR / "perfdata.db"
JAVA_DIR = BASE_DIR / "java"
CONFIG_PATH = BASE_DIR / "config.json"
ACTIVE_TABLES_PATH = BASE_DIR / "active_tables.json"
PROPERTY_DIR = BASE_DIR / "properties"
SERVER_LOGS_DIR = BASE_DIR / "server_logs"

for d in [UPLOAD_DIR, OUTPUT_DIR, LOG_DIR, DB_DIR,PROPERTY_DIR,SERVER_LOGS_DIR]:
    d.mkdir(parents=True, exist_ok=True)
