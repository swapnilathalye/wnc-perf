import json
import datetime
import shutil
from pathlib import Path
from app.utils.paths import CONFIG_PATH, UPLOAD_DIR, OUTPUT_DIR, LOG_DIR, DB_PATH
from app.utils.logging import logger


def load_config() -> dict:
    """
    Load configuration from config.json.
    Returns defaults if file is missing or invalid.
    Ensures backward compatibility and required keys.
    """
    defaults = {
        "days": 7,
        "autoDelete": False,
        "language": "en",
    }

    try:
        if not CONFIG_PATH.exists():
            logger.warning("⚠️ Config file not found, using defaults")
            return defaults.copy()

        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            config = json.load(f)
            logger.info("📄 Loaded config: %s", config)

        # Backward compatibility / self-healing
        for key, default_value in defaults.items():
            if key not in config:
                logger.info("🔧 Adding missing config key '%s' with default '%s'", key, default_value)
                config[key] = default_value

        return config

    except Exception as e:
        logger.error("❌ Failed to load config.json, using defaults: %s", e)
        return defaults.copy()



def save_config(config: dict) -> None:
    """
    Save configuration to config.json.
    """
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
        logger.info("💾 Saved config: %s", config)
    except Exception as e:
        logger.error("❌ Failed to save config: %s", e)


def auto_delete_data() -> None:
    """
    Delete old uploads, outputs, logs, and optionally DB based on config.
    """
    config = load_config()
    if not config.get("autoDelete"):
        logger.info("ℹ️ Auto‑delete disabled, preserving data")
        return

    days = config.get("days", 7)
    cutoff = datetime.datetime.now() - datetime.timedelta(days=days)

    # Delete old uploads
    for folder in UPLOAD_DIR.glob("*"):
        if folder.is_dir():
            mtime = datetime.datetime.fromtimestamp(folder.stat().st_mtime)
            if mtime < cutoff:
                shutil.rmtree(folder, ignore_errors=True)
                logger.info("🗑️ Deleted upload folder %s (older than %d days)", folder, days)

    # Delete old output CSVs
    for folder in OUTPUT_DIR.glob("*"):
        if folder.is_dir():
            mtime = datetime.datetime.fromtimestamp(folder.stat().st_mtime)
            if mtime < cutoff:
                shutil.rmtree(folder, ignore_errors=True)
                logger.info("🗑️ Deleted output folder %s (older than %d days)", folder, days)

    # Delete old logs
    for file in LOG_DIR.glob("*"):
        mtime = datetime.datetime.fromtimestamp(file.stat().st_mtime)
        if mtime < cutoff:
            file.unlink(missing_ok=True)
            logger.info("🗑️ Deleted log file %s (older than %d days)", file, days)

    # Optionally reset DB
    if config.get("database", False):
        if DB_PATH.exists():
            DB_PATH.unlink()
            logger.info("🗑️ Deleted database file older than %d days", days)
