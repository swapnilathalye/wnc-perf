from fastapi import APIRouter

# Core endpoints
from app.api.endpoints import upload, history, tables, download, settings, delete

# Charts: keep active-contexts endpoints in a single module to avoid duplicate routes
from app.api.endpoints.charts import active_contexts,active_users
from app.api.endpoints.tabular import performance_tables

api_router = APIRouter()

api_router.include_router(upload.router)
api_router.include_router(history.router)
api_router.include_router(tables.router)
api_router.include_router(download.router)
api_router.include_router(settings.router)
api_router.include_router(delete.router)
api_router.include_router(active_contexts.router)
api_router.include_router(active_users.router)
api_router.include_router(performance_tables.router)