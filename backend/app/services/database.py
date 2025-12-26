import sqlite3
import pandas as pd
from pathlib import Path
from app.utils.paths import DB_PATH
from app.utils.logging import logger

def import_csv_to_sqlite(csv_path: Path, folder_name: str):
    """
    Import a CSV into SQLite, replacing any existing table for this file.
    Normalize timestamp columns to INTEGER (ms since epoch).
    """
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_csv(csv_path)

    table_name = f"{folder_name}_{csv_path.stem}".replace("-", "_")

    # Drop existing table if any
    conn.execute(f"DROP TABLE IF EXISTS '{table_name}'")

    # 🔹 Normalize all known timestamp columns
    timestamp_cols = [
        "JVM_STARTTIME",
        "LE_TIMESTAMP",
        "CLIENTTIMESTAMP",
        "STARTTIME",
        "[LE_MDC_SAMPLESTARTTIME](guide://action?prefill=Tell%20me%20more%20about%3A%20LE_MDC_SAMPLESTARTTIME)"
    ]
    for col in df.columns:
        if col.upper() in [c.upper() for c in timestamp_cols]:
            df[col] = df[col].apply(
                lambda x: int(float(x)) if pd.notnull(x) else None
            )

    # Import CSV into SQLite
    df.to_sql(table_name, conn, index=False)

    conn.commit()
    conn.close()

    logger.info("✅ Imported %s into SQLite table %s", csv_path.name, table_name)
    return table_name, len(df)


def list_tables():
    """
    List all tables currently in SQLite.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    conn.close()
    logger.info("📋 Listed %d tables from SQLite", len(tables))
    return tables


def get_table(table_name: str, limit: int = 100):
    """
    Fetch rows from a given table.
    Returns dict with rows (list of dicts).
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Check if table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
    exists = cursor.fetchone()
    if not exists:
        logger.warning("⚠️ Table %s not found in DB", table_name)
        conn.close()
        return {"rows": []}

    query = f"SELECT * FROM '{table_name}' LIMIT ?"
    cursor.execute(query, (limit,))
    cols = [desc[0] for desc in cursor.description]
    rows = [dict(zip(cols, r)) for r in cursor.fetchall()]
    conn.close()

    logger.info("✅ Returned %d rows from table %s", len(rows), table_name)
    return {"rows": rows}


def drop_table(table_name: str) -> bool:
    """
    Drop a specific table if it exists.
    Returns True if dropped, False otherwise.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
    exists = cursor.fetchone()
    if exists:
        conn.execute(f"DROP TABLE IF EXISTS '{table_name}'")
        conn.commit()
        conn.close()
        logger.info("🗑️ Dropped table %s", table_name)
        return True
    conn.close()
    logger.warning("⚠️ Tried to drop non-existent table %s", table_name)
    return False


def clear_database():
    """
    Delete all tables in the SQLite DB.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    for t in tables:
        conn.execute(f"DROP TABLE IF EXISTS '{t}'")
        logger.info("🗑️ Dropped table %s", t)
    conn.commit()
    conn.close()
    logger.info("✅ Cleared all tables from database")
