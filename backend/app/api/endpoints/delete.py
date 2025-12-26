from fastapi import APIRouter
from app.services.files import clear_directory
from app.utils.paths import OUTPUT_DIR, LOG_DIR, UPLOAD_DIR, DB_PATH
from app.utils.logging import logger

router = APIRouter()


@router.post("/delete-data")
def delete_data(options: dict):
    """
    Delete selected data categories: database, output_csv, logs, uploads.
    """
    summary = {}

    if options.get("database"):
        try:
            if DB_PATH.exists():
                DB_PATH.unlink()
                logger.info("🗑️ Deleted database %s", DB_PATH)
                summary["database"] = "deleted"
            else:
                summary["database"] = "not found"
        except Exception as e:
            logger.error("❌ Failed to delete database: %s", e)
            summary["database"] = f"error: {e}"

    if options.get("output_csv"):
        try:
            clear_directory(OUTPUT_DIR)
            summary["output_csv"] = "deleted"
        except Exception as e:
            summary["output_csv"] = f"error: {e}"

    if options.get("logs"):
        try:
            clear_directory(LOG_DIR)
            summary["logs"] = "deleted"
        except Exception as e:
            summary["logs"] = f"error: {e}"

    if options.get("uploads"):
        try:
            clear_directory(UPLOAD_DIR)
            summary["uploads"] = "deleted"
        except Exception as e:
            summary["uploads"] = f"error: {e}"

    return {"summary": summary}
