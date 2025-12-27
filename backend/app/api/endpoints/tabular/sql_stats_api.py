from fastapi import APIRouter, Query
from typing import Optional

from app.services.sql_stats import fetch_top_sql_stats

router = APIRouter(prefix="/sql-stats", tags=["SQL Stats"])


@router.get("/")
def get_sql_stats(
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    jvm_id: Optional[str] = None,
    jvm_start_time: Optional[str] = None,
    min_secs: Optional[float] = None,
    sort_by_elapsed_time: bool = False,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500)
):
    """
    Full SQL Stats API with filtering, sorting, and pagination.
    """
    return fetch_top_sql_stats(
        start_time=start_time,
        end_time=end_time,
        jvm_id=jvm_id,
        jvm_start_time=jvm_start_time,
        min_secs=min_secs,
        sort_by_elapsed_time=sort_by_elapsed_time,
        page=page,
        page_size=page_size
    )
