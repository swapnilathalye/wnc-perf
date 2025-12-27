import logging
import sqlite3
from typing import Optional, List, Dict, Any

from app.utils.paths import DB_PATH
from app.api.endpoints.tables import get_current_active_folder

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)


def get_connection() -> sqlite3.Connection:
    logger.info("Opening SQLite connection to %s", DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_top_sql_stats_table_name() -> Optional[str]:
    logger.info("Resolving TopSQLStats table name from active folder")

    active = get_current_active_folder()
    folder = active.get("folder") if active else None

    if not folder:
        logger.warning("No active folder found in active_tables.json")
        return None

    table_name = f"{folder}_TopSQLStats"
    logger.info("Resolved TopSQLStats table: %s", table_name)
    return table_name


def fetch_top_sql_stats(
    start_time: Optional[str],
    end_time: Optional[str],
    jvm_id: Optional[str],
    jvm_start_time: Optional[str],
    min_secs: Optional[float],
    sort_by_elapsed_time: bool,
    page: int,
    page_size: int
) -> Dict[str, Any]:

    table = get_top_sql_stats_table_name()
    if not table:
        return {"results": [], "total": 0}
    
    table_quoted = f'"{table}"'

    where_clauses = []
    params: List[Any] = []

    if start_time:
        where_clauses.append("LE_Timestamp >= ?")
        params.append(start_time)

    if end_time:
        where_clauses.append("StartTime <= ?")
        params.append(end_time)

    if jvm_id:
        where_clauses.append("JVM_Id = ?")
        params.append(jvm_id)

    if jvm_start_time:
        where_clauses.append("JVM_StartTime = ?")
        params.append(jvm_start_time)

    if min_secs is not None:
        where_clauses.append("ElapsedSeconds >= ?")
        params.append(min_secs)

    where_sql = ""
    if where_clauses:
        where_sql = "WHERE " + " AND ".join(where_clauses)

    order_sql = (
        "ORDER BY MaxSeconds DESC, StartTime, LE_Timestamp"
        if sort_by_elapsed_time
        else "ORDER BY StartTime, LE_Timestamp"
    )

    offset = (page - 1) * page_size

    query = f"""
        SELECT *
        FROM {table_quoted}
        {where_sql}
        {order_sql}
        LIMIT ? OFFSET ?
    """

    params.extend([page_size, offset])

    logger.info("Executing SQL: %s", query)
    logger.info("Params: %s", params)

    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(query, params)
        rows = [dict(row) for row in cur.fetchall()]

        # Count total rows for pagination
        count_query = f"SELECT COUNT(*) FROM {table_quoted } {where_sql}"
        cur.execute(count_query, params[:-2])
        total = cur.fetchone()[0]

        return {"results": rows, "total": total}
    finally:
        conn.close()
