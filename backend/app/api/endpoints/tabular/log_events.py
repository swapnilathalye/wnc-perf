import logging
import sqlite3
import pandas as pd
from fastapi import APIRouter,Body

from app.utils.paths import DB_PATH
from app.api.endpoints.tables import get_current_active_folder
from app.ai.insights import build_insight_prompt, call_ai_model

# ---------------------------------------------------------
# Logger setup
# ---------------------------------------------------------
logger = logging.getLogger("log_events")
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
        base="LOGEVENTS"
        active folder = "20251225_upload1"
        → "20251225_upload1_LOGEVENTS"
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
# API: Log Events Error Summary
# ---------------------------------------------------------
@router.get("/log-events-error")
def fetch_log_events_error(limit: int = 20):
    """
    Returns top ERROR loggers aggregated across:
    - MiscLogEvents
    - JmxNotifications
    - MethodContexts
    - ServletRequests
    """

    logger.info("[LOGEVENTS] Fetching ERROR log summary")

    # Resolve dynamic table names
    misc_table = resolve_table_name("MISCLOGEVENTS")
    jmx_table = resolve_table_name("JMXNOTIFICATIONS")
    method_table = resolve_table_name("METHODCONTEXTS")
    servlet_table = resolve_table_name("SERVLETREQUESTS")

    if not all([misc_table, jmx_table, method_table, servlet_table]):
        return {"rows": [], "message": "Active folder tables not found"}

    # Quote table names for SQLite
    misc_q = f'"{misc_table}"'
    jmx_q = f'"{jmx_table}"'
    method_q = f'"{method_table}"'
    servlet_q = f'"{servlet_table}"'

    # ---------------------------------------------------------
    # SQLite-compatible rewritten query
    # ---------------------------------------------------------
    query = f"""
        WITH LOGEVENTS AS (
            SELECT 
                LE_LOGGERNAME,
                LE_LEVEL,
                COUNT(*) AS COUNT
            FROM {misc_q}
            WHERE LE_LEVEL = 'ERROR'
            GROUP BY LE_LOGGERNAME, LE_LEVEL

            UNION ALL

            SELECT 
                LE_LOGGERNAME,
                LE_LEVEL,
                COUNT(*) AS COUNT
            FROM {jmx_q}
            WHERE LE_LEVEL = 'ERROR'
            GROUP BY LE_LOGGERNAME, LE_LEVEL

            UNION ALL

            SELECT 
                'wt.method.MethodContext.contextMBean.finish' AS LE_LOGGERNAME,
                LE_LEVEL,
                COUNT(*) AS COUNT
            FROM {method_q}
            WHERE LE_LEVEL = 'ERROR'
            GROUP BY LE_LEVEL

            UNION ALL

            SELECT 
                'wt.servlet.ServletRequestMonitor.requestMBean.finish' AS LE_LOGGERNAME,
                LE_LEVEL,
                COUNT(*) AS COUNT
            FROM {servlet_q}
            WHERE LE_LEVEL = 'ERROR'
            GROUP BY LE_LEVEL
        )
        SELECT *
        FROM LOGEVENTS
        ORDER BY COUNT DESC
        LIMIT {limit}
    """

    logger.info(f"[LOGEVENTS] Executing query:\n{query}")

    conn = sqlite3.connect(DB_PATH)

    try:
        df = pd.read_sql_query(query, conn)
    except Exception as e:
        logger.error(f"[LOGEVENTS] Query failed: {e}")
        conn.close()
        return {"rows": [], "message": "Error executing log events query"}
    finally:
        conn.close()

    if df.empty:
        return {"rows": [], "message": "No ERROR log events found"}

    return {"rows": df.to_dict(orient="records")}


# ---------------------------------------------------------
# API: Log Events WARN Summary
# ---------------------------------------------------------
@router.get("/log-events-warn")
def fetch_log_events_warn(limit: int = 20):
    """
    Returns top WARN loggers aggregated across:
    - MiscLogEvents
    - JmxNotifications
    - MethodContexts
    - ServletRequests
    """

    logger.info("[LOGEVENTS-WARN] Fetching WARN log summary")

    # Resolve dynamic table names
    misc_table = resolve_table_name("MISCLOGEVENTS")
    jmx_table = resolve_table_name("JMXNOTIFICATIONS")
    method_table = resolve_table_name("METHODCONTEXTS")
    servlet_table = resolve_table_name("SERVLETREQUESTS")

    if not all([misc_table, jmx_table, method_table, servlet_table]):
        return {"rows": [], "message": "Active folder tables not found"}

    # Quote table names for SQLite
    misc_q = f'"{misc_table}"'
    jmx_q = f'"{jmx_table}"'
    method_q = f'"{method_table}"'
    servlet_q = f'"{servlet_table}"'

    # ---------------------------------------------------------
    # SQLite-compatible WARN query
    # ---------------------------------------------------------
    query = f"""
        WITH LOGEVENTS AS (
            SELECT 
                LE_LOGGERNAME,
                LE_LEVEL,
                COUNT(*) AS COUNT
            FROM {misc_q}
            WHERE LE_LEVEL = 'WARN'
            GROUP BY LE_LOGGERNAME, LE_LEVEL

            UNION ALL

            SELECT 
                LE_LOGGERNAME,
                LE_LEVEL,
                COUNT(*) AS COUNT
            FROM {jmx_q}
            WHERE LE_LEVEL = 'WARN'
            GROUP BY LE_LOGGERNAME, LE_LEVEL

            UNION ALL

            SELECT 
                'wt.method.MethodContext.contextMBean.finish' AS LE_LOGGERNAME,
                LE_LEVEL,
                COUNT(*) AS COUNT
            FROM {method_q}
            WHERE LE_LEVEL = 'WARN'
            GROUP BY LE_LEVEL

            UNION ALL

            SELECT 
                'wt.servlet.ServletRequestMonitor.requestMBean.finish' AS LE_LOGGERNAME,
                LE_LEVEL,
                COUNT(*) AS COUNT
            FROM {servlet_q}
            WHERE LE_LEVEL = 'WARN'
            GROUP BY LE_LEVEL
        )
        SELECT *
        FROM LOGEVENTS
        ORDER BY COUNT DESC
        LIMIT {limit}
    """

    logger.info(f"[LOGEVENTS-WARN] Executing query:\n{query}")

    conn = sqlite3.connect(DB_PATH)

    try:
        df = pd.read_sql_query(query, conn)
    except Exception as e:
        logger.error(f"[LOGEVENTS-WARN] Query failed: {e}")
        conn.close()
        return {"rows": [], "message": "Error executing WARN log events query"}
    finally:
        conn.close()

    if df.empty:
        return {"rows": [], "message": "No WARN log events found"}

    return {"rows": df.to_dict(orient="records")}


# ---------------------------------------------------------
# API: Log Events INFO Summary
# ---------------------------------------------------------
@router.get("/log-events-info")
def fetch_log_events_info(limit: int = 20):
    """
    Returns top INFO loggers aggregated across:
    - MiscLogEvents
    - JmxNotifications
    - MethodContexts
    - ServletRequests
    """

    logger.info("[LOGEVENTS-INFO] Fetching INFO log summary")

    # Resolve dynamic table names
    misc_table = resolve_table_name("MISCLOGEVENTS")
    jmx_table = resolve_table_name("JMXNOTIFICATIONS")
    method_table = resolve_table_name("METHODCONTEXTS")
    servlet_table = resolve_table_name("SERVLETREQUESTS")

    if not all([misc_table, jmx_table, method_table, servlet_table]):
        return {"rows": [], "message": "Active folder tables not found"}

    # Quote table names for SQLite
    misc_q = f'"{misc_table}"'
    jmx_q = f'"{jmx_table}"'
    method_q = f'"{method_table}"'
    servlet_q = f'"{servlet_table}"'

    # ---------------------------------------------------------
    # SQLite-compatible INFO query
    # ---------------------------------------------------------
    query = f"""
        WITH LOGEVENTS AS (
            SELECT 
                LE_LOGGERNAME,
                LE_LEVEL,
                COUNT(*) AS COUNT
            FROM {misc_q}
            WHERE LE_LEVEL = 'INFO'
            GROUP BY LE_LOGGERNAME, LE_LEVEL

            UNION ALL

            SELECT 
                LE_LOGGERNAME,
                LE_LEVEL,
                COUNT(*) AS COUNT
            FROM {jmx_q}
            WHERE LE_LEVEL = 'INFO'
            GROUP BY LE_LOGGERNAME, LE_LEVEL

            UNION ALL

            SELECT 
                'wt.method.MethodContext.contextMBean.finish' AS LE_LOGGERNAME,
                LE_LEVEL,
                COUNT(*) AS COUNT
            FROM {method_q}
            WHERE LE_LEVEL = 'INFO'
            GROUP BY LE_LEVEL

            UNION ALL

            SELECT 
                'wt.servlet.ServletRequestMonitor.requestMBean.finish' AS LE_LOGGERNAME,
                LE_LEVEL,
                COUNT(*) AS COUNT
            FROM {servlet_q}
            WHERE LE_LEVEL = 'INFO'
            GROUP BY LE_LEVEL
        )
        SELECT *
        FROM LOGEVENTS
        ORDER BY COUNT DESC
        LIMIT {limit}
    """

    logger.info(f"[LOGEVENTS-INFO] Executing query:\n{query}")

    conn = sqlite3.connect(DB_PATH)

    try:
        df = pd.read_sql_query(query, conn)
    except Exception as e:
        logger.error(f"[LOGEVENTS-INFO] Query failed: {e}")
        conn.close()
        return {"rows": [], "message": "Error executing INFO log events query"}
    finally:
        conn.close()

    if df.empty:
        return {"rows": [], "message": "No INFO log events found"}

    return {"rows": df.to_dict(orient="records")}


# ---------------------------------------------------------
# API: Log Events DEBUG Summary
# ---------------------------------------------------------
@router.get("/log-events-debug")
def fetch_log_events_debug(limit: int = 20):
    """
    Returns top DEBUG loggers aggregated across:
    - MiscLogEvents
    - JmxNotifications
    - MethodContexts
    - ServletRequests
    """

    logger.info("[LOGEVENTS-DEBUG] Fetching DEBUG log summary")

    # Resolve dynamic table names
    misc_table = resolve_table_name("MISCLOGEVENTS")
    jmx_table = resolve_table_name("JMXNOTIFICATIONS")
    method_table = resolve_table_name("METHODCONTEXTS")
    servlet_table = resolve_table_name("SERVLETREQUESTS")

    if not all([misc_table, jmx_table, method_table, servlet_table]):
        return {"rows": [], "message": "Active folder tables not found"}

    # Quote table names for SQLite
    misc_q = f'"{misc_table}"'
    jmx_q = f'"{jmx_table}"'
    method_q = f'"{method_table}"'
    servlet_q = f'"{servlet_table}"'

    # ---------------------------------------------------------
    # SQLite-compatible DEBUG query
    # ---------------------------------------------------------
    query = f"""
        WITH LOGEVENTS AS (
            SELECT 
                LE_LOGGERNAME,
                LE_LEVEL,
                COUNT(*) AS COUNT
            FROM {misc_q}
            WHERE LE_LEVEL = 'DEBUG'
            GROUP BY LE_LOGGERNAME, LE_LEVEL

            UNION ALL

            SELECT 
                LE_LOGGERNAME,
                LE_LEVEL,
                COUNT(*) AS COUNT
            FROM {jmx_q}
            WHERE LE_LEVEL = 'DEBUG'
            GROUP BY LE_LOGGERNAME, LE_LEVEL

            UNION ALL

            SELECT 
                'wt.method.MethodContext.contextMBean.finish' AS LE_LOGGERNAME,
                LE_LEVEL,
                COUNT(*) AS COUNT
            FROM {method_q}
            WHERE LE_LEVEL = 'DEBUG'
            GROUP BY LE_LEVEL

            UNION ALL

            SELECT 
                'wt.servlet.ServletRequestMonitor.requestMBean.finish' AS LE_LOGGERNAME,
                LE_LEVEL,
                COUNT(*) AS COUNT
            FROM {servlet_q}
            WHERE LE_LEVEL = 'DEBUG'
            GROUP BY LE_LEVEL
        )
        SELECT *
        FROM LOGEVENTS
        ORDER BY COUNT DESC
        LIMIT {limit}
    """

    logger.info(f"[LOGEVENTS-DEBUG] Executing query:\n{query}")

    conn = sqlite3.connect(DB_PATH)

    try:
        df = pd.read_sql_query(query, conn)
    except Exception as e:
        logger.error(f"[LOGEVENTS-DEBUG] Query failed: {e}")
        conn.close()
        return {"rows": [], "message": "Error executing DEBUG log events query"}
    finally:
        conn.close()

    if df.empty:
        return {"rows": [], "message": "No DEBUG log events found"}

    return {"rows": df.to_dict(orient="records")}


# ---------------------------------------------------------
# API: Log Events TRACE Summary
# ---------------------------------------------------------
@router.get("/log-events-trace")
def fetch_log_events_trace(limit: int = 20):
    """
    Returns top TRACE loggers aggregated across:
    - MiscLogEvents
    - JmxNotifications
    - MethodContexts
    - ServletRequests
    """

    logger.info("[LOGEVENTS-TRACE] Fetching TRACE log summary")

    # Resolve dynamic table names
    misc_table = resolve_table_name("MISCLOGEVENTS")
    jmx_table = resolve_table_name("JMXNOTIFICATIONS")
    method_table = resolve_table_name("METHODCONTEXTS")
    servlet_table = resolve_table_name("SERVLETREQUESTS")

    if not all([misc_table, jmx_table, method_table, servlet_table]):
        return {"rows": [], "message": "Active folder tables not found"}

    # Quote table names for SQLite
    misc_q = f'"{misc_table}"'
    jmx_q = f'"{jmx_table}"'
    method_q = f'"{method_table}"'
    servlet_q = f'"{servlet_table}"'

    # ---------------------------------------------------------
    # SQLite-compatible TRACE query
    # ---------------------------------------------------------
    query = f"""
        WITH LOGEVENTS AS (
            SELECT 
                LE_LOGGERNAME,
                LE_LEVEL,
                COUNT(*) AS COUNT
            FROM {misc_q}
            WHERE LE_LEVEL = 'TRACE'
            GROUP BY LE_LOGGERNAME, LE_LEVEL

            UNION ALL

            SELECT 
                LE_LOGGERNAME,
                LE_LEVEL,
                COUNT(*) AS COUNT
            FROM {jmx_q}
            WHERE LE_LEVEL = 'TRACE'
            GROUP BY LE_LOGGERNAME, LE_LEVEL

            UNION ALL

            SELECT 
                'wt.method.MethodContext.contextMBean.finish' AS LE_LOGGERNAME,
                LE_LEVEL,
                COUNT(*) AS COUNT
            FROM {method_q}
            WHERE LE_LEVEL = 'TRACE'
            GROUP BY LE_LEVEL

            UNION ALL

            SELECT 
                'wt.servlet.ServletRequestMonitor.requestMBean.finish' AS LE_LOGGERNAME,
                LE_LEVEL,
                COUNT(*) AS COUNT
            FROM {servlet_q}
            WHERE LE_LEVEL = 'TRACE'
            GROUP BY LE_LEVEL
        )
        SELECT *
        FROM LOGEVENTS
        ORDER BY COUNT DESC
        LIMIT {limit}
    """

    logger.info(f"[LOGEVENTS-TRACE] Executing query:\n{query}")

    conn = sqlite3.connect(DB_PATH)

    try:
        df = pd.read_sql_query(query, conn)
    except Exception as e:
        logger.error(f"[LOGEVENTS-TRACE] Query failed: {e}")
        conn.close()
        return {"rows": [], "message": "Error executing TRACE log events query"}
    finally:
        conn.close()

    if df.empty:
        return {"rows": [], "message": "No TRACE log events found"}

    return {"rows": df.to_dict(orient="records")}


# ---------------------------------------------------------
# API: Log Events ALL Levels Summary
# ---------------------------------------------------------
@router.get("/log-events-all")
def fetch_log_events_all(limit: int = 20):
    """
    Returns top ALL loggers aggregated across:
    - MiscLogEvents
    - JmxNotifications
    - MethodContexts
    - ServletRequests

    NOTE:
    LE_LEVEL='ALL' means: include ALL levels (no WHERE filter)
    """

    logger.info("[LOGEVENTS-ALL] Fetching ALL-level log summary")

    # Resolve dynamic table names
    misc_table = resolve_table_name("MISCLOGEVENTS")
    jmx_table = resolve_table_name("JMXNOTIFICATIONS")
    method_table = resolve_table_name("METHODCONTEXTS")
    servlet_table = resolve_table_name("SERVLETREQUESTS")

    if not all([misc_table, jmx_table, method_table, servlet_table]):
        return {"rows": [], "message": "Active folder tables not found"}

    # Quote table names for SQLite
    misc_q = f'"{misc_table}"'
    jmx_q = f'"{jmx_table}"'
    method_q = f'"{method_table}"'
    servlet_q = f'"{servlet_table}"'

    # ---------------------------------------------------------
    # SQLite-compatible ALL-levels query (NO WHERE LE_LEVEL filter)
    # ---------------------------------------------------------
    query = f"""
        WITH LOGEVENTS AS (
            SELECT 
                LE_LOGGERNAME,
                LE_LEVEL,
                COUNT(*) AS COUNT
            FROM {misc_q}
            GROUP BY LE_LOGGERNAME, LE_LEVEL

            UNION ALL

            SELECT 
                LE_LOGGERNAME,
                LE_LEVEL,
                COUNT(*) AS COUNT
            FROM {jmx_q}
            GROUP BY LE_LOGGERNAME, LE_LEVEL

            UNION ALL

            SELECT 
                'wt.method.MethodContext.contextMBean.finish' AS LE_LOGGERNAME,
                LE_LEVEL,
                COUNT(*) AS COUNT
            FROM {method_q}
            GROUP BY LE_LEVEL

            UNION ALL

            SELECT 
                'wt.servlet.ServletRequestMonitor.requestMBean.finish' AS LE_LOGGERNAME,
                LE_LEVEL,
                COUNT(*) AS COUNT
            FROM {servlet_q}
            GROUP BY LE_LEVEL
        )
        SELECT *
        FROM LOGEVENTS
        ORDER BY COUNT DESC
        LIMIT {limit}
    """

    logger.info(f"[LOGEVENTS-ALL] Executing query:\n{query}")

    conn = sqlite3.connect(DB_PATH)

    try:
        df = pd.read_sql_query(query, conn)
    except Exception as e:
        logger.error(f"[LOGEVENTS-ALL] Query failed: {e}")
        conn.close()
        return {"rows": [], "message": "Error executing ALL log events query"}
    finally:
        conn.close()

    if df.empty:
        return {"rows": [], "message": "No log events found"}

    return {"rows": df.to_dict(orient="records")}

# ---------------------------------------------------------
# API: Log Events FATAL Summary
# ---------------------------------------------------------
@router.get("/log-events-fatal")
def fetch_log_events_fatal(limit: int = 20):
    """
    Returns top FATAL loggers aggregated across:
    - MiscLogEvents
    - JmxNotifications
    - MethodContexts
    - ServletRequests
    """

    logger.info("[LOGEVENTS-FATAL] Fetching FATAL log summary")

    # Resolve dynamic table names
    misc_table = resolve_table_name("MISCLOGEVENTS")
    jmx_table = resolve_table_name("JMXNOTIFICATIONS")
    method_table = resolve_table_name("METHODCONTEXTS")
    servlet_table = resolve_table_name("SERVLETREQUESTS")

    if not all([misc_table, jmx_table, method_table, servlet_table]):
        return {"rows": [], "message": "Active folder tables not found"}

    # Quote table names for SQLite
    misc_q = f'"{misc_table}"'
    jmx_q = f'"{jmx_table}"'
    method_q = f'"{method_table}"'
    servlet_q = f'"{servlet_table}"'

    # ---------------------------------------------------------
    # SQLite-compatible FATAL query
    # ---------------------------------------------------------
    query = f"""
        WITH LOGEVENTS AS (
            SELECT 
                LE_LOGGERNAME,
                LE_LEVEL,
                COUNT(*) AS COUNT
            FROM {misc_q}
            WHERE LE_LEVEL = 'FATAL'
            GROUP BY LE_LOGGERNAME, LE_LEVEL

            UNION ALL

            SELECT 
                LE_LOGGERNAME,
                LE_LEVEL,
                COUNT(*) AS COUNT
            FROM {jmx_q}
            WHERE LE_LEVEL = 'FATAL'
            GROUP BY LE_LOGGERNAME, LE_LEVEL

            UNION ALL

            SELECT 
                'wt.method.MethodContext.contextMBean.finish' AS LE_LOGGERNAME,
                LE_LEVEL,
                COUNT(*) AS COUNT
            FROM {method_q}
            WHERE LE_LEVEL = 'FATAL'
            GROUP BY LE_LEVEL

            UNION ALL

            SELECT 
                'wt.servlet.ServletRequestMonitor.requestMBean.finish' AS LE_LOGGERNAME,
                LE_LEVEL,
                COUNT(*) AS COUNT
            FROM {servlet_q}
            WHERE LE_LEVEL = 'FATAL'
            GROUP BY LE_LEVEL
        )
        SELECT *
        FROM LOGEVENTS
        ORDER BY COUNT DESC
        LIMIT {limit}
    """

    logger.info(f"[LOGEVENTS-FATAL] Executing query:\n{query}")

    conn = sqlite3.connect(DB_PATH)

    try:
        df = pd.read_sql_query(query, conn)
    except Exception as e:
        logger.error(f"[LOGEVENTS-FATAL] Query failed: {e}")
        conn.close()
        return {"rows": [], "message": "Error executing FATAL log events query"}
    finally:
        conn.close()

    if df.empty:
        return {"rows": [], "message": "No FATAL log events found"}

    return {"rows": df.to_dict(orient="records")}


# ---------------------------------------------------------
# API: Log Events OFF Summary
# ---------------------------------------------------------
@router.get("/log-events-off")
def fetch_log_events_off(limit: int = 20):
    """
    Returns top OFF loggers aggregated across:
    - MiscLogEvents
    - JmxNotifications
    - MethodContexts
    - ServletRequests
    """

    logger.info("[LOGEVENTS-OFF] Fetching OFF log summary")

    # Resolve dynamic table names
    misc_table = resolve_table_name("MISCLOGEVENTS")
    jmx_table = resolve_table_name("JMXNOTIFICATIONS")
    method_table = resolve_table_name("METHODCONTEXTS")
    servlet_table = resolve_table_name("SERVLETREQUESTS")

    if not all([misc_table, jmx_table, method_table, servlet_table]):
        return {"rows": [], "message": "Active folder tables not found"}

    # Quote table names for SQLite
    misc_q = f'"{misc_table}"'
    jmx_q = f'"{jmx_table}"'
    method_q = f'"{method_table}"'
    servlet_q = f'"{servlet_table}"'

    # ---------------------------------------------------------
    # SQLite-compatible OFF query
    # ---------------------------------------------------------
    query = f"""
        WITH LOGEVENTS AS (
            SELECT 
                LE_LOGGERNAME,
                LE_LEVEL,
                COUNT(*) AS COUNT
            FROM {misc_q}
            WHERE LE_LEVEL = 'OFF'
            GROUP BY LE_LOGGERNAME, LE_LEVEL

            UNION ALL

            SELECT 
                LE_LOGGERNAME,
                LE_LEVEL,
                COUNT(*) AS COUNT
            FROM {jmx_q}
            WHERE LE_LEVEL = 'OFF'
            GROUP BY LE_LOGGERNAME, LE_LEVEL

            UNION ALL

            SELECT 
                'wt.method.MethodContext.contextMBean.finish' AS LE_LOGGERNAME,
                LE_LEVEL,
                COUNT(*) AS COUNT
            FROM {method_q}
            WHERE LE_LEVEL = 'OFF'
            GROUP BY LE_LEVEL

            UNION ALL

            SELECT 
                'wt.servlet.ServletRequestMonitor.requestMBean.finish' AS LE_LOGGERNAME,
                LE_LEVEL,
                COUNT(*) AS COUNT
            FROM {servlet_q}
            WHERE LE_LEVEL = 'OFF'
            GROUP BY LE_LEVEL
        )
        SELECT *
        FROM LOGEVENTS
        ORDER BY COUNT DESC
        LIMIT {limit}
    """

    logger.info(f"[LOGEVENTS-OFF] Executing query:\n{query}")

    conn = sqlite3.connect(DB_PATH)

    try:
        df = pd.read_sql_query(query, conn)
    except Exception as e:
        logger.error(f"[LOGEVENTS-OFF] Query failed: {e}")
        conn.close()
        return {"rows": [], "message": "Error executing OFF log events query"}
    finally:
        conn.close()

    if df.empty:
        return {"rows": [], "message": "No OFF log events found"}

    return {"rows": df.to_dict(orient="records")}


# ---------------------------------------------------------
# AI Insights for Log Events (all levels)
# ---------------------------------------------------------
@router.get("/log-events-ai-insights")
def log_events_ai_insights(level: str = "ALL", limit: int = 50):
    """
    AI generates insights for log events for a given level.
    """

    logger.info(f"[LOGEVENTS-AI-INSIGHTS] Level={level}")

    misc_table = resolve_table_name("MISCLOGEVENTS")
    jmx_table = resolve_table_name("JMXNOTIFICATIONS")
    method_table = resolve_table_name("METHODCONTEXTS")
    servlet_table = resolve_table_name("SERVLETREQUESTS")

    if not all([misc_table, jmx_table, method_table, servlet_table]):
        return {"rows": [], "ai_insights": "Active folder tables not found."}

    misc_q = f'"{misc_table}"'
    jmx_q = f'"{jmx_table}"'
    method_q = f'"{method_table}"'
    servlet_q = f'"{servlet_table}"'

    where = "" if level.upper() == "ALL" else f"WHERE LE_LEVEL = '{level.upper()}'"

    query = f"""
        WITH LOGEVENTS AS (
            SELECT LE_LOGGERNAME, LE_LEVEL, COUNT(*) AS COUNT
            FROM {misc_q}
            {where}
            GROUP BY LE_LOGGERNAME, LE_LEVEL

            UNION ALL

            SELECT LE_LOGGERNAME, LE_LEVEL, COUNT(*) AS COUNT
            FROM {jmx_q}
            {where}
            GROUP BY LE_LOGGERNAME, LE_LEVEL

            UNION ALL

            SELECT 'wt.method.MethodContext.contextMBean.finish' AS LE_LOGGERNAME,
                   LE_LEVEL,
                   COUNT(*) AS COUNT
            FROM {method_q}
            {where}
            GROUP BY LE_LEVEL

            UNION ALL

            SELECT 'wt.servlet.ServletRequestMonitor.requestMBean.finish' AS LE_LOGGERNAME,
                   LE_LEVEL,
                   COUNT(*) AS COUNT
            FROM {servlet_q}
            {where}
            GROUP BY LE_LEVEL
        )
        SELECT *
        FROM LOGEVENTS
        ORDER BY COUNT DESC
        LIMIT {limit}
    """

    logger.info(f"[LOGEVENTS-AI-INSIGHTS] Executing query:\n{query}")

    conn = sqlite3.connect(DB_PATH)
    try:
        df = pd.read_sql_query(query, conn)
    except Exception:
        conn.close()
        return {"rows": [], "ai_insights": "Error executing log events query."}
    finally:
        conn.close()

    if df.empty:
        return {"rows": [], "ai_insights": "No log events found."}

    rows = df.to_dict(orient="records")

    prompt = build_insight_prompt(rows, f"Log Events ({level})", "summary")
    ai_text = call_ai_model(prompt)

    return {
        "rows": rows,
        "ai_insights": ai_text
    }

# ---------------------------------------------------------
# AI Query for Log Events (all levels)
# ---------------------------------------------------------
@router.post("/log-events-ai-query")
def log_events_ai_query(
    level: str = Body(..., embed=True),
    question: str = Body(..., embed=True),
    limit: int = 50
):
    """
    AI answers questions about log events for a given level.
    level can be: ERROR, WARN, INFO, DEBUG, TRACE, FATAL, OFF, ALL
    """

    logger.info(f"[LOGEVENTS-AI-QUERY] Level={level}")

    # Resolve dynamic tables
    misc_table = resolve_table_name("MISCLOGEVENTS")
    jmx_table = resolve_table_name("JMXNOTIFICATIONS")
    method_table = resolve_table_name("METHODCONTEXTS")
    servlet_table = resolve_table_name("SERVLETREQUESTS")

    if not all([misc_table, jmx_table, method_table, servlet_table]):
        return {"answer": "Active folder tables not found."}

    misc_q = f'"{misc_table}"'
    jmx_q = f'"{jmx_table}"'
    method_q = f'"{method_table}"'
    servlet_q = f'"{servlet_table}"'

    # WHERE clause logic
    where = "" if level.upper() == "ALL" else f"WHERE LE_LEVEL = '{level.upper()}'"

    query = f"""
        WITH LOGEVENTS AS (
            SELECT LE_LOGGERNAME, LE_LEVEL, COUNT(*) AS COUNT
            FROM {misc_q}
            {where}
            GROUP BY LE_LOGGERNAME, LE_LEVEL

            UNION ALL

            SELECT LE_LOGGERNAME, LE_LEVEL, COUNT(*) AS COUNT
            FROM {jmx_q}
            {where}
            GROUP BY LE_LOGGERNAME, LE_LEVEL

            UNION ALL

            SELECT 'wt.method.MethodContext.contextMBean.finish' AS LE_LOGGERNAME,
                   LE_LEVEL,
                   COUNT(*) AS COUNT
            FROM {method_q}
            {where}
            GROUP BY LE_LEVEL

            UNION ALL

            SELECT 'wt.servlet.ServletRequestMonitor.requestMBean.finish' AS LE_LOGGERNAME,
                   LE_LEVEL,
                   COUNT(*) AS COUNT
            FROM {servlet_q}
            {where}
            GROUP BY LE_LEVEL
        )
        SELECT *
        FROM LOGEVENTS
        ORDER BY COUNT DESC
        LIMIT {limit}
    """

    logger.info(f"[LOGEVENTS-AI-QUERY] Executing query:\n{query}")

    conn = sqlite3.connect(DB_PATH)
    try:
        df = pd.read_sql_query(query, conn)
    except Exception as e:
        logger.error(f"[LOGEVENTS-AI-QUERY] Query failed: {e}")
        conn.close()
        return {"answer": "Error executing log events query."}
    finally:
        conn.close()

    if df.empty:
        return {"answer": "No log events found for this level."}

    rows = df.to_dict(orient="records")

    prompt = f"""
    You are an observability assistant.
    The user asked: "{question}"
    Log event data (top {limit} rows): {rows}
    Answer concisely based only on this data.
    """

    answer = call_ai_model(prompt)
    return {"answer": answer}
