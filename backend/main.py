"""
FarmStock Backend v2 — FastAPI Entry Point
==========================================
Endpoints:
  POST /api/predict              → predict crop price (Rs/kg in, Rs/kg + Rs/quintal out)
  POST /api/forecast             → forecast prices for next N days (1–90)
  POST /api/crop-health          → crop health & disease risk advisory  ← FROM files(1).zip
  GET  /api/crop-health/crops    → list crops with disease data          ← FROM files(1).zip
  GET  /api/crops                → list all 224 crops the model knows
  GET  /api/markets              → list all 1,289 markets the model knows
  GET  /api/health               → API + model health check
  GET  /api/model/info           → model metadata, metrics, feature list

Then open: http://localhost:8000/docs
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn

from app.routes import predict, forecast, info, crop_health
from app.services.model_service import ModelService


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load ML model on startup, clean up on shutdown."""
    print(" FarmStock API v2 starting...")
    app.state.model_service = ModelService()
    app.state.model_service.load()
    from app.utils.weather_fetcher import fetch_weather
    temp, rain, src = fetch_weather("Tamil Nadu", "Rabi")
    print(f"  Weather API : {src} — {temp}°C, {rain}mm")
    print(" Ready — Swagger UI: http://localhost:8000/docs")
    yield
    print(" Shutting down.")


app = FastAPI(
    title       = "FarmStock Crop Price Prediction API",
    description = (
        "ML-powered API for Indian agricultural commodity price prediction.\n\n"
        "**All prices in Rs/kg** (auto-converted from mandi Rs/quintal).\n\n"
        "Response always includes BOTH Rs/kg and Rs/quintal.\n\n"
        "**New in v2:** Crop health & disease advisory (POST /api/crop-health)"
    ),
    version     = "2.0.0",
    lifespan    = lifespan,
    docs_url    = "/docs",
    redoc_url   = "/redoc",
)

# Allow React frontend on any origin (restrict in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins     = ["*"],
    allow_credentials = True,
    allow_methods     = ["*"],
    allow_headers     = ["*"],
)

# ── Register all route groups ──────────────────────────────────
app.include_router(predict.router,      prefix="/api", tags=["Prediction"])
app.include_router(forecast.router,     prefix="/api", tags=["Forecast"])
app.include_router(crop_health.router,  prefix="/api", tags=["Crop Health"])
app.include_router(info.router,         prefix="/api", tags=["Info"])


@app.get("/", tags=["Root"])
def root():
    return {
        "app":     "FarmStock API",
        "version": "2.0.0",
        "unit":    "Rs/kg",
        "docs":    "/docs",
        "endpoints": {
            "predict":      "POST /api/predict",
            "forecast":     "POST /api/forecast",
            "crop_health":  "POST /api/crop-health",
            "crops":        "GET  /api/crops",
            "markets":      "GET  /api/markets",
            "health":       "GET  /api/health",
            "model_info":   "GET  /api/model/info",
        }
    }


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
