from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.startup import ingest_latest_folder

app = FastAPI()

# ✅ CORS setup for React frontend
origins = ["http://localhost:3000"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ API routes
app.include_router(api_router)

# ✅ Startup event
@app.on_event("startup")
def startup_event():
    ingest_latest_folder()
