"""
Carbon Intelligence System — Main FastAPI Application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes_data import router as data_router
from api.routes_emissions import router as emissions_router
from api.routes_chat import router as chat_router
from api.routes_reports import router as reports_router
from database import get_connection

app = FastAPI(
    title="Carbon Intelligence System",
    description=(
        "AI-driven carbon footprint estimation, tracking, and reduction platform. "
        "Estimates emissions from electricity, travel, commuting, cloud, equipment, and waste "
        "using EPA, DEFRA, IPCC, and IEA emission factors."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS — allow Streamlit dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(data_router)
app.include_router(emissions_router)
app.include_router(chat_router)
app.include_router(reports_router)


@app.get("/", tags=["Health"])
async def root():
    """Health check endpoint."""
    conn = get_connection()
    activity_count = conn.execute("SELECT COUNT(*) FROM raw_activity").fetchone()[0]
    emission_count = conn.execute("SELECT COUNT(*) FROM emissions").fetchone()[0]

    return {
        "status": "healthy",
        "service": "Carbon Intelligence System",
        "version": "1.0.0",
        "data": {
            "activity_records": activity_count,
            "emission_records": emission_count,
        },
    }


@app.get("/api/health", tags=["Health"])
async def health_check():
    """Detailed health check."""
    return {
        "status": "ok",
        "database": "connected",
        "endpoints": [
            "/api/data/upload",
            "/api/data/batch",
            "/api/emissions/summary",
            "/api/emissions/by-category",
            "/api/emissions/by-department",
            "/api/emissions/monthly",
            "/api/emissions/insights",
            "/api/emissions/forecast",
            "/api/chat",
            "/api/reports/generate",
            "/api/reports/latest",
        ],
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
