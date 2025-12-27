import logging
import sqlite3
import pandas as pd
from fastapi import APIRouter

from app.utils.paths import DB_PATH
from app.api.endpoints.tables import get_current_active_folder
from app.ai.insights import build_insight_prompt, call_ai_model

# ---------------------------------------------------------
# Logger setup
# ---------------------------------------------------------
logger = logging.getLogger("active_sessions_summary")
logger.setLevel(logging.INFO)

if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

router = APIRouter()


# ---------------------------------------------------------
# Resolve dynamic table names based on active folder
# ---------------------------------------------------------
def resolve_table_name(base: str) -> str | None:
    """
    Example:
        base="ServletSessionStats"
        active folder = "20251225_upload1"
        → "20251225_upload1_ServletSessionStats"
    """
    active = get_current_active_folder()
    folder = active.get("folder") if active else None

    if not folder:
        logger.warning("No active folder found in active_tables.json")
        return None

    table_name = f"{folder}_{base}"
    logger.info(f"Resolved table name: {table_name}")
    return table_name


# ---------------------------------------------------------
# GLOBAL SUMMARY ENDPOINT
# ---------------------------------------------------------
@router.get("/active-sessions-summary")
def active_sessions_summary():
    logger.info("[SUMMARY] Fetching global session summary")

    table = resolve_table_name("ServletSessionStats")
    if not table:
        return {"summary": {}, "message": "Active folder table not found"}

    table_q = f'"{table}"'

    query = f"SELECT * FROM {table_q}"

    conn = sqlite3.connect(DB_PATH)

    try:
        df = pd.read_sql_query(query, conn)
    except Exception as e:
        logger.error(f"[SUMMARY] Query failed: {e}")
        conn.close()
        return {"summary": {}, "message": "Error executing summary query"}
    finally:
        conn.close()

    if df.empty:
        return {"summary": {}, "message": "No session data found"}

    # Convert timestamps
    df["iso"] = df["LE_TIMESTAMP"].apply(
        lambda x: pd.to_datetime(int(x), unit="ms").isoformat()
    )

    summary = {
        "total_jvms": df["JVM_ID"].nunique(),
        "total_samples": len(df),
        "peak_active_sessions": df["ACTIVESESSIONSMAX"].max(),
        "avg_active_sessions": float(df["ACTIVESESSIONSMAX"].mean()),
        "total_sessions_created": int(df["SESSIONSCREATED"].sum()),
        "total_sessions_destroyed": int(df["SESSIONSDESTROYED"].sum()),
        "total_sessions_activated": int(df["SESSIONSACTIVATED"].sum()),
        "total_sessions_passivated": int(df["SESSIONSPASSIVATED"].sum()),
        "max_elapsed_seconds": float(df["ELAPSEDSECONDS"].max()),
        "min_timestamp_iso": df["iso"].min(),
        "max_timestamp_iso": df["iso"].max(),
        "jvm_with_peak_sessions": df.loc[
            df["ACTIVESESSIONSMAX"].idxmax(), "JVM_ID"
        ] if df["ACTIVESESSIONSMAX"].max() > 0 else None
    }

    return {"summary": summary}


# ---------------------------------------------------------
# AI SUMMARY ENDPOINT
# ---------------------------------------------------------
@router.get("/active-sessions-ai-summary")
def active_sessions_ai_summary(limit: int = 200):
    logger.info("[AI-SUMMARY] Generating AI insights for session data")

    table = resolve_table_name("ServletSessionStats")
    if not table:
        return {"rows": [], "ai_summary": "Active folder table not found"}

    table_q = f'"{table}"'

    query = f"""
        SELECT *
        FROM {table_q}
        ORDER BY LE_TIMESTAMP
        LIMIT {limit}
    """

    conn = sqlite3.connect(DB_PATH)

    try:
        df = pd.read_sql_query(query, conn)
    except Exception as e:
        logger.error(f"[AI-SUMMARY] Query failed: {e}")
        conn.close()
        return {"rows": [], "ai_summary": "Error executing AI summary query"}
    finally:
        conn.close()

    if df.empty:
        return {"rows": [], "ai_summary": "No session data available"}

    # Convert timestamps
    df["iso"] = df["LE_TIMESTAMP"].apply(
        lambda x: pd.to_datetime(int(x), unit="ms").isoformat()
    )

    rows = df.to_dict(orient="records")

    prompt = build_insight_prompt(
        rows,
        "ServletSessionStats",
        "active-sessions-summary"
    )

    ai_text = call_ai_model(prompt)

    return {
        "rows": rows,
        "ai_summary": ai_text
    }


# ---------------------------------------------------------
# GRAPH DATA ENDPOINT
# ---------------------------------------------------------
@router.get("/active-sessions-graph")
def active_sessions_graph(limit: int = 500):
    logger.info("[GRAPH] Building active sessions graph data")

    table = resolve_table_name("ServletSessionStats")
    if not table:
        return {"nodes": [], "edges": [], "message": "Active folder table not found"}

    table_q = f'"{table}"'

    query = f"""
        SELECT *
        FROM {table_q}
        ORDER BY LE_TIMESTAMP
        LIMIT {limit}
    """

    conn = sqlite3.connect(DB_PATH)

    try:
        df = pd.read_sql_query(query, conn)
    except Exception as e:
        logger.error(f"[GRAPH] Query failed: {e}")
        conn.close()
        return {"nodes": [], "edges": [], "message": "Error executing graph query"}
    finally:
        conn.close()

    if df.empty:
        return {"nodes": [], "edges": [], "message": "No session data found"}

    # Convert timestamps
    df["iso"] = df["LE_TIMESTAMP"].apply(
        lambda x: pd.to_datetime(int(x), unit="ms").isoformat()
    )

    # Build nodes (one per JVM)
    nodes = []
    for jvm, group in df.groupby("JVM_ID"):
        nodes.append({
            "id": jvm,
            "label": jvm,
            "peak_active": int(group["ACTIVESESSIONSMAX"].max()),
            "avg_active": float(group["ACTIVESESSIONSMAX"].mean()),
            "samples": len(group),
        })

    # Optional edges (simple chain for topology layout)
    edges = []
    jvm_list = list(df["JVM_ID"].unique())
    for i in range(len(jvm_list) - 1):
        edges.append({
            "source": jvm_list[i],
            "target": jvm_list[i + 1]
        })

    return {
        "nodes": nodes,
        "edges": edges
    }
