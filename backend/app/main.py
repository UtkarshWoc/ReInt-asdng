"""FastAPI Application Factory."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers import accuracy, forecasts, health, meta

app = FastAPI(
    title="UK Wind Generation Day-Ahead Decision Support API",
    description=(
        "REST API supporting UK power trading desks with leak-free wind forecast views "
        "at D-1 gate closure and empirical forecast accuracy analysis."
    ),
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers with /api prefix (standard Docker and local dev)
app.include_router(health.router, prefix="/api")
app.include_router(meta.router, prefix="/api")
app.include_router(forecasts.router, prefix="/api")
app.include_router(accuracy.router, prefix="/api")

# Also include Routers without /api prefix (for serverless environments where /api is stripped by proxy)
app.include_router(health.router)
app.include_router(meta.router)
app.include_router(forecasts.router)
app.include_router(accuracy.router)


@app.get("/")
def root():
    return {
        "project": "UK Wind Generation Day-Ahead Decision Support",
        "documentation": "/docs",
        "health": "/api/health",
        "meta": "/api/meta",
    }
