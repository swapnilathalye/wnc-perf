import logging
import math
import sqlite3
from typing import Any

import pandas as pd
from fastapi import APIRouter, Body, Query

from app.utils.paths import DB_PATH
from app.ai.insights import build_insight_prompt, call_ai_model
from app.api.endpoints.tables import get_current_active_folder

router = APIRouter()

# -------------------------------------------------------
# Logger setup
# -------------------------------------------------------
logger = logging.getLogger("active_users")
logger.setLevel(logging.INFO)
logger.propagate = False  # IMPORTANT: prevents duplicate log lines

if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] [active-users] %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

# -------------------------------------------------------
# Helpers
# -------------------------------------------------------

def build_where(start_date, end_date):
    logger.debug("Building WHERE clause | start=%s end=%s", start_date, end_date)

    if start_date and end_date:
        return (
            f"WHERE LE_TIMESTAMP BETWEEN "
            f"strftime('%s','{start_date}')*1000 AND strftime('%s','{end_date}')*1000"
        )
    elif start_date:
        return f"WHERE LE_TIMESTAMP >= strftime('%s','{start_date}')*1000"
    elif end_date:
        return f"WHERE LE_TIMESTAMP <= strftime('%s','{end_date}')*1000"
    return ""


def add_iso(df: pd.DataFrame) -> pd.DataFrame:
    logger.debug("Adding ISO timestamps to dataframe (%d rows)", len(df))
    df["iso"] = df["last_ts"].apply(
        lambda x: pd.to_datetime(int(x), unit="ms").isoformat() if pd.notnull(x) else None
    )
    return df


def get_active_users_table_name() -> str | None:
    """
    table_name = f"{folder}_SMHealthStats"
    """
    logger.info("Resolving active users table name from active folder")

    active = get_current_active_folder()
    folder = active.get("folder")

    if not folder:
        logger.warning("No active folder found in active_tables.json")
        return None

    table_name = f"{folder}_SMHealthStats"
    logger.info("Resolved active users table: %s", table_name)
    return table_name


def json_safe(value: Any):
    """
    Convert pandas/numpy types to JSON-serializable primitives.
    Fixes FastAPI 500 during response serialization.
    """
    try:
        import numpy as np  # type: ignore
        if isinstance(value, (np.integer,)):
            return int(value)
        if isinstance(value, (np.floating,)):
            v = float(value)
            return None if math.isnan(v) else v
        if isinstance(value, (np.bool_,)):
            return bool(value)
    except Exception:
        pass

    # NaN handling for regular floats
    if isinstance(value, float) and math.isnan(value):
        return None

    # pandas Timestamp
    try:
        if isinstance(value, pd.Timestamp):
            return value.isoformat()
    except Exception:
        pass

    return value


def make_rows_json_safe(rows: list[dict]) -> list[dict]:
    return [{k: json_safe(v) for k, v in r.items()} for r in rows]


# -------------------------------------------------------
# Endpoints
# -------------------------------------------------------

@router.get("/active-users-ai-insights")
def active_users_ai_insights(
    jvm: str = Query("all"),
    limit: int = 200,
    granularity: str = "raw",
    start_date: str = None,
    end_date: str = None,
):
    logger.info("Active Users AI Insights | jvm=%s granularity=%s limit=%d", jvm, granularity, limit)

    table_name = get_active_users_table_name()
    if not table_name:
        return {"rows": [], "ai_insights": "No active folder set."}

    conn = sqlite3.connect(DB_PATH)
    where_clause = build_where(start_date, end_date)

    if jvm != "all":
        logger.info("Filtering for JVM_ID=%s", jvm)
        where_clause = f"{where_clause} {'AND' if where_clause else 'WHERE'} JVM_ID = '{jvm}'"
    else:
        logger.info("Aggregating across ALL JVMs")

    if granularity == "daily":
        logger.info("Using DAILY aggregation")
        query = f"""
            SELECT
                date(LE_TIMESTAMP / 1000, 'unixepoch') AS bucket,
                JVM_ID,
                MAX(TOTALACTIVEUSERCOUNT) AS total_active_users,
                MAX(LE_TIMESTAMP) AS last_ts
            FROM "{table_name}"
            {where_clause}
            GROUP BY bucket, JVM_ID
            ORDER BY bucket
            LIMIT {limit}
        """
    elif granularity == "hourly":
        logger.info("Using HOURLY aggregation")
        query = f"""
            SELECT
                strftime('%Y-%m-%d %H:00:00', LE_TIMESTAMP / 1000, 'unixepoch') AS bucket,
                JVM_ID,
                MAX(TOTALACTIVEUSERCOUNT) AS total_active_users,
                MAX(LE_TIMESTAMP) AS last_ts
            FROM "{table_name}"
            {where_clause}
            GROUP BY bucket, JVM_ID
            ORDER BY bucket
            LIMIT {limit}
        """
    else:
        logger.info("Using RAW data")
        query = f"""
            SELECT
                LE_TIMESTAMP AS last_ts,
                JVM_ID,
                TOTALACTIVEUSERCOUNT AS total_active_users
            FROM "{table_name}"
            {where_clause}
            ORDER BY LE_TIMESTAMP
            LIMIT {limit}
        """

    try:
        df = pd.read_sql_query(query, conn)
    except Exception as e:
        logger.error("Query failed for table=%s | error=%s", table_name, e)
        return {"rows": [], "ai_insights": "Query execution failed.", "error": str(e), "table_name": table_name}
    finally:
        conn.close()

    if df.empty:
        logger.warning("No active users data found for given filters")
        return {"rows": [], "ai_insights": "No data available for the given filters."}

    logger.info("Fetched %d rows for active users", len(df))

    df = add_iso(df)
    rows = make_rows_json_safe(df.to_dict(orient="records"))

    logger.info("Calling AI insights model")
    prompt = build_insight_prompt(rows, table_name, granularity)
    ai_text = call_ai_model(prompt)
    logger.info("AI insights generated successfully")

    return {"rows": rows, "ai_insights": ai_text}


@router.post("/active-users-ai-query")
def active_users_ai_query(
    question: str = Body(..., embed=True),
    jvm: str = Query("all"),
    limit: int = 200,
    granularity: str = "raw",
    start_date: str = None,
    end_date: str = None,
):
    logger.info("Active Users AI Query | jvm=%s | question=%s", jvm, question)

    table_name = get_active_users_table_name()
    if not table_name:
        logger.warning("AI query aborted: no active folder")
        return {"answer": "No active folder set."}

    conn = sqlite3.connect(DB_PATH)
    where_clause = build_where(start_date, end_date)

    if jvm != "all":
        where_clause = f"{where_clause} {'AND' if where_clause else 'WHERE'} JVM_ID = '{jvm}'"

    query = f"""
        SELECT
            LE_TIMESTAMP AS last_ts,
            JVM_ID,
            TOTALACTIVEUSERCOUNT AS total_active_users
        FROM "{table_name}"
        {where_clause}
        ORDER BY LE_TIMESTAMP
        LIMIT {limit}
    """

    try:
        df = pd.read_sql_query(query, conn)
    except Exception as e:
        logger.error("AI query failed for table=%s | error=%s", table_name, e)
        return {"answer": "Error executing query for AI question.", "error": str(e), "table_name": table_name}
    finally:
        conn.close()

    if df.empty:
        logger.warning("AI query returned no data")
        return {"answer": "No data available for the given filters."}

    df = add_iso(df)
    rows = make_rows_json_safe(df.to_dict(orient="records"))

    logger.info("Calling AI model for question answering")

    prompt = f"""
You are an observability assistant.
The user asked: "{question}"
Use only the data below to answer.
Data (truncated): {rows[:120]}
Answer concisely.
"""
    answer = call_ai_model(prompt)
    logger.info("AI answer generated successfully")

    return {"answer": answer}


@router.get("/active-users-jvms")
def active_users_jvms(start_date: str = None, end_date: str = None):
    """
    Returns unique JVM_ID list from the active users table (folder_SMHealthStats).
    """
    table_name = get_active_users_table_name()
    if not table_name:
        logger.warning("No active folder set (active-users-jvms)")
        return {"jvms": []}

    conn = sqlite3.connect(DB_PATH)
    where_clause = build_where(start_date, end_date)

    query = f"""
        SELECT DISTINCT JVM_ID
        FROM "{table_name}"
        {where_clause}
        ORDER BY JVM_ID
    """

    logger.info("Querying JVM list from %s", table_name)

    try:
        df = pd.read_sql_query(query, conn)
    except Exception as e:
        logger.error("active-users-jvms query failed for table=%s | error=%s", table_name, e)
        return {"jvms": []}
    finally:
        conn.close()

    jvms = df["JVM_ID"].dropna().tolist() if not df.empty else []
    # make sure they are JSON-safe primitives
    jvms = [json_safe(x) for x in jvms]

    logger.info("Found %d JVM IDs", len(jvms))
    return {"jvms": jvms}

from datetime import datetime

@router.get("/active-users-date-range")
def active_users_date_range():
    """
    Returns oldest and latest date from <activeFolder>_SMHealthStats.
    """
    table_name = get_active_users_table_name()
    if not table_name:
        return {"start_date": None, "end_date": None, "message": "No active folder set"}

    conn = sqlite3.connect(DB_PATH)
    query = f"""
        SELECT MIN(LE_TIMESTAMP) AS min_ts, MAX(LE_TIMESTAMP) AS max_ts
        FROM "{table_name}"
    """
    try:
        df = pd.read_sql_query(query, conn)
    except Exception as e:
        logger.error("[ACTIVE-USERS-DATE-RANGE] Failed: %s", e)
        return {"start_date": None, "end_date": None, "error": str(e), "table_name": table_name}
    finally:
        conn.close()

    if df.empty or df.loc[0, "min_ts"] is None or df.loc[0, "max_ts"] is None:
        return {"start_date": None, "end_date": None, "message": "No data in table", "table_name": table_name}

    min_ts = int(df.loc[0, "min_ts"])
    max_ts = int(df.loc[0, "max_ts"])

    start_date = datetime.fromtimestamp(min_ts / 1000).strftime("%Y-%m-%d")
    end_date = datetime.fromtimestamp(max_ts / 1000).strftime("%Y-%m-%d")

    return {"start_date": start_date, "end_date": end_date, "table_name": table_name}

