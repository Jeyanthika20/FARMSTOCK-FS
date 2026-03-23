"""
FarmStock Backend v3 — FastAPI Entry Point
==========================================
NEW in v3:
  - WebSocket /ws/prices  → real-time price ticker
  - WebSocket /ws/alerts  → real-time crop health alerts
  - POST /api/notifications → push notification preferences
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn, asyncio, random
from datetime import datetime

from app.routes import predict, forecast, info, crop_health, notifications
from app.services.model_service import ModelService
from app.services.websocket_manager import ConnectionManager
from dotenv import load_dotenv
from pathlib import Path
load_dotenv(dotenv_path=Path(r"D:\FARMSTOCK\backend\.env"))

manager = ConnectionManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    print(" FarmStock API v3 starting...")
    app.state.model_service = ModelService()
    app.state.model_service.load()
    app.state.ws_manager = manager
    print(" Ready — Swagger UI: http://localhost:8000/docs")
    yield
    print(" Shutting down.")

app = FastAPI(
    title="FarmStock Crop Price Prediction API",
    description="ML-powered API for Indian agricultural commodity price prediction. v3 with WebSocket real-time support.",
    version="3.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(predict.router,       prefix="/api", tags=["Prediction"])
app.include_router(forecast.router,      prefix="/api", tags=["Forecast"])
app.include_router(crop_health.router,   prefix="/api", tags=["Crop Health"])
app.include_router(info.router,          prefix="/api", tags=["Info"])
app.include_router(notifications.router, prefix="/api", tags=["Notifications"])


@app.websocket("/ws/prices")
async def websocket_prices(websocket: WebSocket):
    await manager.connect(websocket, channel="prices")
    try:
        TRACKED = [
            ("Tomato", "Coimbatore", 45.0),
            ("Onion", "Chennai", 32.0),
            ("Potato", "Salem", 28.0),
            ("Rice", "Madurai", 55.0),
            ("Wheat", "Trichy", 38.0),
            ("Banana", "Erode", 25.0),
            ("Green Chilli", "Coimbatore", 60.0),
            ("Brinjal", "Salem", 22.0),
        ]
        prices = {c[0]: c[2] for c in TRACKED}
        while True:
            updates = []
            for crop, market, base in TRACKED:
                change = random.uniform(-2.5, 2.5)
                prices[crop] = max(5.0, prices[crop] + change)
                chg_pct = round((prices[crop] - base) / base * 100, 2)
                updates.append({
                    "crop": crop,
                    "market": market,
                    "price_kg": round(prices[crop], 2),
                    "price_quintal": round(prices[crop] * 100, 2),
                    "change_pct": chg_pct,
                    "trend": "up" if change > 0 else "down",
                    "timestamp": datetime.now().isoformat()
                })
            await websocket.send_json({"type": "price_update", "data": updates, "timestamp": datetime.now().isoformat()})
            await asyncio.sleep(3)
    except WebSocketDisconnect:
        manager.disconnect(websocket, channel="prices")


@app.websocket("/ws/alerts")
async def websocket_alerts(websocket: WebSocket):
    await manager.connect(websocket, channel="alerts")
    try:
        ALERTS = [
            {"severity": "HIGH", "title": "Heavy Rain Alert — Tomato Farmers", "title_ta": "கனமழை எச்சரிக்கை — தக்காளி விவசாயிகள்", "message": "High rainfall predicted. Apply Mancozeb 2.5g/L preventively to avoid Early Blight.", "message_ta": "அதிக மழை எதிர்பார்க்கப்படுகிறது. ஆர்லி ப்ளைட் தடுக்க மேன்கோஸெப் 2.5g/L தெளிக்கவும்.", "category": "disease"},
            {"severity": "MEDIUM", "title": "Price Surge — Onion", "title_ta": "விலை உயர்வு — வெங்காயம்", "message": "Onion prices rising 15% this week in Chennai market. Consider selling now.", "message_ta": "சென்னை சந்தையில் வெங்காய விலை 15% அதிகரிக்கிறது. இப்போது விற்கலாம்.", "category": "market"},
            {"severity": "LOW", "title": "Rabi Sowing Advisory — Wheat", "title_ta": "ரபி விதைப்பு ஆலோசனை — கோதுமை", "message": "Optimal wheat sowing: Oct 25 – Nov 15. Use HD-2967 or PBW-343.", "message_ta": "கோதுமை விதைப்பு: அக். 25 – நவ. 15. HD-2967 அல்லது PBW-343 பயன்படுத்தவும்.", "category": "planting"},
            {"severity": "CRITICAL", "title": "Late Blight Outbreak — Potato", "title_ta": "தாமத கருகல் நோய் — உருளைக்கிழங்கு", "message": "CRITICAL: Late blight in Nilgiris. Spray Metalaxyl + Mancozeb immediately.", "message_ta": "முக்கியம்: நீலகிரியில் தாமத கருகல். உடனே மெட்டாலாக்சில் + மேன்கோஸெப் தெளிக்கவும்.", "category": "disease"},
            {"severity": "MEDIUM", "title": "Mandi Closed — Pongal", "title_ta": "சந்தை மூடல் — பொங்கல்", "message": "Markets closed Jan 14–17 for Pongal. Plan sales accordingly.", "message_ta": "பொங்கலுக்காக ஜன. 14-17 சந்தைகள் மூடல். விற்பனையை முன்னதாக திட்டமிடுங்கள்.", "category": "market"},
        ]
        idx = 0
        while True:
            alert = ALERTS[idx % len(ALERTS)]
            await websocket.send_json({"type": "alert", "data": {**alert, "id": idx, "timestamp": datetime.now().isoformat()}})
            idx += 1
            await asyncio.sleep(random.uniform(12, 20))
    except WebSocketDisconnect:
        manager.disconnect(websocket, channel="alerts")


@app.get("/", tags=["Root"])
def root():
    return {"app": "FarmStock API", "version": "3.0.0", "docs": "/docs", "websockets": {"prices": "ws://localhost:8000/ws/prices", "alerts": "ws://localhost:8000/ws/alerts"}}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
