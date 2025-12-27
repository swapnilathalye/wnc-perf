from fastapi import APIRouter
from app.services.config import load_config, save_config
from app.utils.logging import logger

router = APIRouter()


@router.get("/settings")
def get_settings():
    """
    Load current settings from config.json.
    """
    config = load_config()
    logger.info("📄 Loaded settings: %s", config)
    return config


@router.post("/settings")
def update_settings(settings: dict):
    """
    Update settings and save to config.json.
    """
    logger.info("⚙️ Updating settings: %s", settings)

    # Load existing config (if any)
    existing = load_config()

    # Merge settings (new values override old)
    merged = {
        "days": settings.get("days", existing.get("days", 7)),
        "autoDelete": settings.get("autoDelete", existing.get("autoDelete", False)),
        "language": settings.get("language", existing.get("language", "en")),
    }

    save_config(merged)
    return {"message": "Settings saved", "settings": merged}


@router.get("/settings/languages")
def get_supported_languages():
    """
    Returns supported UI languages.
    Can later be driven by config / DB / feature flags.
    """
    return {
        "default": "en",
        "languages": [
            { "code": "en", "label": "English" },
            { "code": "fr", "label": "French" },
            { "code": "de", "label": "German" },
            { "code": "es", "label": "Spanish" },
            { "code": "ja", "label": "Japanese" }
        ]
    }

