from fastapi import APIRouter, Request, HTTPException
from app.models.schemas import ForecastRequest, ForecastResponse, ForecastDay
import numpy as np

router = APIRouter()

@router.post("/forecast", response_model=ForecastResponse)
def forecast_prices(body: ForecastRequest, request: Request):
    """
    Forecast crop prices for next N days (max 90).
    Input current_price in Rs/kg. Response has Rs/kg + Rs/quintal per day.
    Best and worst sell dates are always distinct (guaranteed by model_service).
    """
    svc = request.app.state.model_service
    if not svc._loaded:
        raise HTTPException(503, "Model not loaded.")

    raw  = svc.forecast(body.commodity, body.market, body.state,
                        body.current_price, body.horizon_days)
    days = [ForecastDay(**{k: v for k, v in d.items() if k in ForecastDay.__fields__}) for d in raw]
    prices_kg = [d.predicted_price_kg for d in days]

    best_idx  = next((i for i, d in enumerate(raw) if d.get('is_best_sell')),  int(np.argmax(prices_kg)))
    worst_idx = next((i for i, d in enumerate(raw) if d.get('is_worst_sell')), int(np.argmin(prices_kg)))

    # Guarantee they differ
    if best_idx == worst_idx:
        worst_idx = (best_idx + len(days) // 2) % len(days)

    best  = days[best_idx]
    worst = days[worst_idx]

    summary = {
        'min_price_kg':      round(min(prices_kg), 2),
        'max_price_kg':      round(max(prices_kg), 2),
        'avg_price_kg':      round(float(np.mean(prices_kg)), 2),
        'min_price_quintal': round(min(prices_kg) * 100, 2),
        'max_price_quintal': round(max(prices_kg) * 100, 2),
        'best_sell_date':    best.date,
        'best_sell_price_kg': best.predicted_price_kg,
        'best_sell_price_quintal': best.predicted_price_quintal,
        'worst_sell_date':   worst.date,
        'worst_sell_price_kg': worst.predicted_price_kg,
        'potential_gain_pct': round((best.predicted_price_kg - body.current_price) / body.current_price * 100, 2),
    }

    return ForecastResponse(
        commodity=body.commodity, market=body.market,
        current_price=body.current_price, horizon_days=body.horizon_days,
        forecast=days, summary=summary,
    )
