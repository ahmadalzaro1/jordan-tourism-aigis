from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import get_settings
from app.db.database import engine, Base
from app.api.routes import data, geo, etl, summary, analytics, export, research, actions, sources, official


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

def require_demo_mode():
    if settings.data_mode != "demo":
        raise HTTPException(410, "Legacy demo analytics are unavailable in official mode. Use /api/official; governorate monthly demand was not published in these sources.")

app.include_router(official.router, prefix="/api/official", tags=["official observations"])
app.include_router(sources.router, prefix="/api/sources", tags=["sources"])
app.include_router(data.router, dependencies=[Depends(require_demo_mode)], prefix="/api/tourism", tags=["tourism"])
app.include_router(geo.router, prefix="/api/geo", tags=["geo"])
app.include_router(etl.router, dependencies=[Depends(require_demo_mode)], prefix="/api/etl", tags=["etl"])
app.include_router(summary.router, dependencies=[Depends(require_demo_mode)], prefix="/api/summary", tags=["summary"])
app.include_router(analytics.router, dependencies=[Depends(require_demo_mode)], prefix="/api/analytics", tags=["analytics"])
app.include_router(export.router, dependencies=[Depends(require_demo_mode)], prefix="/api/export", tags=["export"])
app.include_router(research.router, dependencies=[Depends(require_demo_mode)], prefix="/api/research", tags=["research"])
app.include_router(actions.router, dependencies=[Depends(require_demo_mode)], prefix="/api/actions", tags=["actions"])


@app.get("/")
def root():
    return {"name": settings.app_name, "version": "1.0.0", "status": "running"}


@app.get("/health")
def health():
    return {"status": "ok"}
