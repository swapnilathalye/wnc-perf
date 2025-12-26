from fastapi import APIRouter
import json
from app.services.database import list_tables, get_table
from app.utils.paths import ACTIVE_TABLES_PATH
from app.utils.logging import logger

router = APIRouter()


@router.get("/tables")
def list_all_tables():
    """
    List all tables currently in SQLite.
    """
    tables = list_tables()
    logger.info("📋 Listed %d tables", len(tables))
    return {"tables": tables}


@router.get("/table/{table_name}")
def fetch_table(table_name: str, limit: int = 100):
    """
    Fetch rows from a given table.
    """
    result = get_table(table_name, limit)
    return result


@router.get("/active-tables")
def get_active_tables():
    """
    Return currently active tables from active_tables.json.
    """
    if ACTIVE_TABLES_PATH.exists():
        try:
            with open(ACTIVE_TABLES_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            return {
                "folder": data.get("folder"),
                "tables": data.get("tables", [])
            }
        except Exception as e:
            logger.error("❌ Failed to read active_tables.json: %s", e)
            return {"folder": None, "tables": [], "error": str(e)}
    else:
        return {"folder": None, "tables": []}



@router.post("/set-active-tables")
def set_active_tables_from_history(payload: dict):
    """
    Update active_tables.json when user clicks 'View Dashboard' from Upload History.
    Payload should include {"folder_name": "..."}.
    """
    folder_name = payload.get("folder_name")
    if not folder_name:
        return {"message": "❌ folder_name is required"}

    # Build table names based on convention
    tables = []
    tables_info = []

    for t in list_tables():
        if t.startswith(folder_name):
            tables.append(t)
            tables_info.append({"tableName": t})

    # ✅ Write new JSON structure
    data = {
        "folder": folder_name,
        "tables": tables
    }

    with open(ACTIVE_TABLES_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    logger.info("💾 Active tables updated from history: %s", tables)

    return {
        "message": f"Active tables set from {folder_name}",
        "folder": folder_name,
        "tables": tables,
        "tables_info": tables_info
    }

@router.get("/current-active-folder")
def get_current_active_folder():
    """
    Returns the currently active folder from active_tables.json.
    JSON structure expected:
    {
        "folder": "20251218_upload1",
        "tables": ["20251218_upload1_MethodContextStats", ...]
    }
    """
    if not ACTIVE_TABLES_PATH.exists():
        logger.warning("⚠️ active_tables.json not found")
        return {"folder": None, "message": "No active folder set"}

    try:
        with open(ACTIVE_TABLES_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)

        folder = data.get("folder")
        tables = data.get("tables", [])

        logger.info(f"📁 Current active folder: {folder}")

        return {
            "folder": folder,
            "tables": tables
        }

    except Exception as e:
        logger.error(f"❌ Failed to read active_tables.json: {e}")
        return {"folder": None, "tables": [], "error": str(e)}