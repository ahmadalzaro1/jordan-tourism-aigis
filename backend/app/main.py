from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import get_settings
from app.db.database import engine, Base
from app.api.routes import data, geo, etl, summary, analytics, export, research


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables on startup
    Base.metadata.create_all(bind=engine)
    yield


settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="AI-Enabled Geo-Analytics for Jordan Tourism",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(data.router, prefix="/api/tourism", tags=["tourism"])
app.include_router(geo.router, prefix="/api/geo", tags=["geo"])
app.include_router(etl.router, prefix="/api/etl", tags=["etl"])
app.include_router(summary.router, prefix="/api/summary", tags=["summary"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])
app.include_router(export.router, prefix="/api/export", tags=["export"])\napp.include_router(research.router, prefix="/api/research", tags=["research"])


@app.get("/")
def root():
    return {"name": settings.app_name, "version": "1.0.0", "status": "running"}


@app.get("/health")
def health():
    return {"status": "ok"}
