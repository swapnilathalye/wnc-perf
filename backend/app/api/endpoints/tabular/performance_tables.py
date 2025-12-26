import logging
import sqlite3
from typing import Any

import pandas as pd
from fastapi import APIRouter, Body, Query

from app.utils.paths import DB_PATH
from app.api.endpoints.tables import get_current_active_folder
from app.ai.insights import call_ai_model  # Ollama integration

router = APIRouter(
    prefix="/tabular",
    tags=["Tabular AI"]
)

logger = logging.getLogger("performance_ai")
logger.setLevel(logging.INFO)
logger.propagate = False

if not logger.handlers:
    h = logging.StreamHandler()
    h.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] [perf-ai] %(message)s"))
    logger.addHandler(h)


def _resolve_full_table_name(short_table: str) -> str | None:
    active = get_current_active_folder()
    folder = active.get("folder")
    if not folder:
        logger.warning("No active folder set")
        return None
    return f"{folder}_{short_table}"


def _table_exists(conn: sqlite3.Connection, table_name: str) -> bool:
    cur = conn.cursor()
    cur.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,)
    )
    return cur.fetchone() is not None


def _get_columns(conn: sqlite3.Connection, table_name: str) -> list[str]:
    cur = conn.cursor()
    cur.execute(f'PRAGMA table_info("{table_name}")')
    return [r[1] for r in cur.fetchall()]


def _json_safe(value: Any):
    try:
        import numpy as np
        if isinstance(value, (np.integer,)):
            return int(value)
        if isinstance(value, (np.floating,)):
            v = float(value)
            return None if v != v else v
        if isinstance(value, (np.bool_,)):
            return bool(value)
    except Exception:
        pass

    if isinstance(value, float) and value != value:
        return None

    try:
        if isinstance(value, pd.Timestamp):
            return value.isoformat()
    except Exception:
        pass

    return value


def _make_rows_json_safe(rows: list[dict]) -> list[dict]:
    return [{k: _json_safe(v) for k, v in r.items()} for r in rows]


@router.post("/perf-ai-query")
def perf_ai_query(
    table: str = Query(None),
    table_name: str = Query(None),
    question: str = Body(..., embed=True),
    limit: int = Query(200, ge=10, le=2000),
    sample: str = Query("latest", description="latest|random"),
):
    # 1) Resolve short table name from either param
    short_table = table or table_name

    logger.info(
        "Perf AI Query | table=%s table_name=%s | limit=%d | sample=%s",
        table, table_name, limit, sample
    )

    if not short_table:
        logger.warning("Perf AI Query missing table/table_name")
        return {"answer": "Missing required parameter: table (or table_name)"}

    # 2) If client accidentally sends full prefixed name, strip it:
    #    20251225_upload1_CacheStatistics -> CacheStatistics
    parts = str(short_table).split("_")
    if len(parts) >= 3 and parts[0].isdigit() and parts[1].startswith("upload"):
        logger.info("Stripping active-folder prefix from table: %s", short_table)
        short_table = "_".join(parts[2:])

    logger.info("Resolved short_table=%s", short_table)

    # 3) Now resolve full table name using active folder (same logic)
    full_table = _resolve_full_table_name(short_table)
    if not full_table:
        return {"answer": "No active folder set. Upload data first."}

    logger.info("Resolved full_table=%s", full_table)

    conn = sqlite3.connect(DB_PATH)
    try:
        if not _table_exists(conn, full_table):
            logger.warning("Table not found in DB: %s", full_table)
            return {"answer": f"Table not found: {full_table}"}

        cols = _get_columns(conn, full_table)
        if not cols:
            return {"answer": f"No columns in table: {full_table}"}

        order_clause = ""
        if sample == "latest" and "LE_TIMESTAMP" in cols:
            order_clause = "ORDER BY LE_TIMESTAMP DESC"

        sql = f'''
            SELECT * FROM "{full_table}"
            {order_clause}
            LIMIT {limit}
        '''

        logger.info("SQL for AI sample: %s", sql.replace("\n", " "))
        df = pd.read_sql_query(sql, conn)

    except Exception as e:
        logger.error("Query failed: %s", e)
        return {"answer": "Failed to read table data.", "error": str(e)}

    finally:
        conn.close()

    if df.empty:
        return {"answer": "No data available in this table."}

    rows = _make_rows_json_safe(df.to_dict(orient="records"))

    prompt = f"""
You are a performance analysis assistant.

Table: {full_table}
Columns: {list(df.columns)}

User question:
{question}

Sample rows:
{rows[:120]}

Respond concisely. Highlight anomalies, trends, or risks.
"""

    logger.info("Calling Ollama model…")
    answer = call_ai_model(prompt)
    logger.info("AI response generated")

    return {
        "answer": answer,
        "table": short_table,         # ✅ return the resolved short name
        "full_table": full_table,
        "rows_sent": min(len(rows), 120),
        "columns": list(df.columns),
    }
