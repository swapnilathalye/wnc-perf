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
    save_config(settings)
    return {"message": "Settings saved", "settings": settings}
