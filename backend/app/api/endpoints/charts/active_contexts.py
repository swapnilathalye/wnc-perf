import logging
from fastapi import APIRouter, Body
from app.utils.paths import DB_PATH
import sqlite3
import pandas as pd
from app.ai.insights import build_insight_prompt, call_ai_model

# Configure logger
logger = logging.getLogger("active_contexts")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

router = APIRouter()

# ---------------------------------------------------------
# ✅ Shared helper: WHERE clause builder
# ---------------------------------------------------------
def build_where(start_date, end_date):
    if start_date and end_date:
        return f"WHERE LE_TIMESTAMP BETWEEN strftime('%s','{start_date}')*1000 AND strftime('%s','{end_date}')*1000"
    elif start_date:
        return f"WHERE LE_TIMESTAMP >= strftime('%s','{start_date}')*1000"
    elif end_date:
        return f"WHERE LE_TIMESTAMP <= strftime('%s','{end_date}')*1000"
    return ""


# ---------------------------------------------------------
# ✅ Shared helper: Convert timestamps
# ---------------------------------------------------------
def add_timestamp_columns(df):
    df["iso"] = df["last_ts"].apply(
        lambda x: pd.to_datetime(int(x), unit="ms").isoformat()
        if pd.notnull(x) else None
    )
    return df


# ---------------------------------------------------------
# ✅ General Active Contexts
# ---------------------------------------------------------
@router.get("/active-contexts/{table_name}")
def fetch_active_context_chart(
    table_name: str,
    limit: int = 200,
    granularity: str = "raw",
    start_date: str = None,
    end_date: str = None,
):
    logger.info(f"[GENERAL] Fetching active-contexts for table={table_name}")

    conn = sqlite3.connect(DB_PATH)
    where_clause = build_where(start_date, end_date)

    if granularity == "daily":
        query = f"""
            SELECT 
                date(LE_TIMESTAMP / 1000, 'unixepoch') AS bucket,
                MAX(ACTIVECONTEXTSMAX) AS max_active,
                MAX(LE_TIMESTAMP) AS last_ts
            FROM "{table_name}"
            {where_clause}
            GROUP BY bucket
            ORDER BY bucket
            LIMIT {limit}
        """
    elif granularity == "hourly":
        query = f"""
            SELECT 
                strftime('%Y-%m-%d %H:00:00', LE_TIMESTAMP / 1000, 'unixepoch') AS bucket,
                MAX(ACTIVECONTEXTSMAX) AS max_active,
                MAX(LE_TIMESTAMP) AS last_ts
            FROM "{table_name}"
            {where_clause}
            GROUP BY bucket
            ORDER BY bucket
            LIMIT {limit}
        """
    else:
        query = f"""
            SELECT 
                LE_TIMESTAMP AS last_ts,
                ACTIVECONTEXTSMAX AS max_active
            FROM "{table_name}"
            {where_clause}
            ORDER BY LE_TIMESTAMP
            LIMIT {limit}
        """

    try:
        df = pd.read_sql_query(query, conn)
    except Exception as e:
        logger.error(f"[GENERAL] Query failed: {e}")
        conn.close()
        return {"rows": [], "message": "Error executing query"}
    finally:
        conn.close()

    if df.empty:
        return {"rows": [], "message": "No data exists for the given date range"}

    df = add_timestamp_columns(df)
    return {"rows": df.to_dict(orient="records")}


# ---------------------------------------------------------
# ✅ JVM-specific Active Contexts
# ---------------------------------------------------------
@router.get("/active-contexts-jvm")
def fetch_active_contexts_by_jvm(
    table_name: str,
    limit: int = 200,
    granularity: str = "raw",
    start_date: str = None,
    end_date: str = None,
):
    logger.info(f"[JVM] Fetching JVM data for table={table_name}")

    conn = sqlite3.connect(DB_PATH)
    where_clause = build_where(start_date, end_date)

    if granularity == "daily":
        query = f"""
            SELECT 
                date(LE_TIMESTAMP / 1000, 'unixepoch') AS bucket,
                JVM_ID,
                MAX(ACTIVECONTEXTSMAX) AS max_active,
                MAX(LE_TIMESTAMP) AS last_ts
            FROM "{table_name}"
            {where_clause}
            GROUP BY bucket, JVM_ID
            ORDER BY bucket
            LIMIT {limit}
        """
    elif granularity == "hourly":
        query = f"""
            SELECT 
                strftime('%Y-%m-%d %H:00:00', LE_TIMESTAMP / 1000, 'unixepoch') AS bucket,
                JVM_ID,
                MAX(ACTIVECONTEXTSMAX) AS max_active,
                MAX(LE_TIMESTAMP) AS last_ts
            FROM "{table_name}"
            {where_clause}
            GROUP BY bucket, JVM_ID
            ORDER BY bucket
            LIMIT {limit}
        """
    else:
        query = f"""
            SELECT 
                LE_TIMESTAMP AS last_ts,
                JVM_ID,
                ACTIVECONTEXTSMAX AS max_active
            FROM "{table_name}"
            {where_clause}
            ORDER BY LE_TIMESTAMP
            LIMIT {limit}
        """

    try:
        df = pd.read_sql_query(query, conn)
    except Exception as e:
        logger.error(f"[JVM] Query failed: {e}")
        conn.close()
        return {"rows": [], "message": "Error executing JVM query"}
    finally:
        conn.close()

    if df.empty:
        return {"rows": [], "message": "No JVM data exists"}

    df = add_timestamp_columns(df)
    return {"rows": df.to_dict(orient="records")}


# ---------------------------------------------------------
# ✅ AI Query Endpoint (same logic as JVM/raw)
# ---------------------------------------------------------
@router.post("/active-contexts-ai-query")
def active_contexts_ai_query(
    table_name: str,
    question: str = Body(..., embed=True),
    limit: int = 200,
    granularity: str = "raw",
    start_date: str = None,
    end_date: str = None,
):
    conn = sqlite3.connect(DB_PATH)
    where_clause = build_where(start_date, end_date)

    query = f"""
        SELECT 
            LE_TIMESTAMP AS last_ts,
            JVM_ID,
            ACTIVECONTEXTSMAX AS max_active
        FROM "{table_name}"
        {where_clause}
        ORDER BY LE_TIMESTAMP
        LIMIT {limit}
    """

    try:
        df = pd.read_sql_query(query, conn)
    except Exception as e:
        logger.error(f"[AI-QUERY] Query failed: {e}")
        conn.close()
        return {"answer": "Error executing query for AI question."}
    finally:
        conn.close()

    if df.empty:
        return {"answer": "No data available for the given filters."}

    df = add_timestamp_columns(df)
    rows = df.to_dict(orient="records")

    prompt = f"""
    You are an observability assistant.
    The user asked: "{question}"
    Data sample: {rows[:100]}
    Answer concisely based only on this data.
    """

    answer = call_ai_model(prompt)
    return {"answer": answer}


# ---------------------------------------------------------
# ✅ AI Insights Endpoint (same logic as JVM/raw)
# ---------------------------------------------------------
@router.get("/active-contexts-ai-insights")
def active_contexts_ai_insights(
    table_name: str,
    limit: int = 200,
    granularity: str = "raw",
    start_date: str = None,
    end_date: str = None,
):
    conn = sqlite3.connect(DB_PATH)
    where_clause = build_where(start_date, end_date)

    # Build query (unchanged)
    if granularity == "daily":
        query = f"""
            SELECT 
                date(LE_TIMESTAMP / 1000, 'unixepoch') AS bucket,
                JVM_ID,
                MAX(ACTIVECONTEXTSMAX) AS max_active,
                MAX(LE_TIMESTAMP) AS last_ts
            FROM "{table_name}"
            {where_clause}
            GROUP BY bucket, JVM_ID
            ORDER BY bucket
            LIMIT {limit}
        """
    elif granularity == "hourly":
        query = f"""
            SELECT 
                strftime('%Y-%m-%d %H:00:00', LE_TIMESTAMP / 1000, 'unixepoch') AS bucket,
                JVM_ID,
                MAX(ACTIVECONTEXTSMAX) AS max_active,
                MAX(LE_TIMESTAMP) AS last_ts
            FROM "{table_name}"
            {where_clause}
            GROUP BY bucket, JVM_ID
            ORDER BY bucket
            LIMIT {limit}
        """
    else:
        query = f"""
            SELECT 
                LE_TIMESTAMP AS last_ts,
                JVM_ID,
                ACTIVECONTEXTSMAX AS max_active
            FROM "{table_name}"
            {where_clause}
            ORDER BY LE_TIMESTAMP
            LIMIT {limit}
        """

    try:
        df = pd.read_sql_query(query, conn)
    except Exception:
        conn.close()
        return {
            "rows": [],
            "ai_insights": "Error executing query for AI insights.",
            "min_iso": None,
            "max_iso": None
        }
    finally:
        conn.close()

    if df.empty:
        return {
            "rows": [],
            "ai_insights": "No data available for insights.",
            "min_iso": None,
            "max_iso": None
        }

    # Add timestamp columns (your existing helper)
    df = add_timestamp_columns(df)
    rows = df.to_dict(orient="records")

    # ✅ Extract min/max ISO timestamps
    try:
        min_iso = df["iso"].min()
        max_iso = df["iso"].max()
    except Exception:
        min_iso = None
        max_iso = None

    # AI insights
    prompt = build_insight_prompt(rows, table_name, granularity)
    ai_text = call_ai_model(prompt)

    return {
        "rows": rows,
        "ai_insights": ai_text,
        "min_iso": min_iso,
        "max_iso": max_iso
    }

