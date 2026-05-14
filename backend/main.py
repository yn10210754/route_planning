# backend/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import settings
from routers import plan, poi

app = FastAPI(title="Route Planner API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.backend_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(plan.router, prefix="/api", tags=["plan"])
app.include_router(poi.router, prefix="/api", tags=["poi"])

@app.get("/health")
async def health():
    return {"status": "ok"}
