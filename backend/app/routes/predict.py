from fastapi import APIRouter, Request, HTTPException
from app.models.schemas import PredictRequest, PredictResponse
from datetime import datetime

router = APIRouter()

@router.post("/predict", response_model=PredictResponse)
def predict_price(body: PredictRequest, request: Request):
    """
    Predict crop price for a given date.
    Input/output prices in Rs/kg.  Response also shows Rs/quintal.
    """
    svc = request.app.state.model_service
    if not svc._loaded:
        raise HTTPException(503, "Model not loaded. Run train_model.py first.")

    target_date = body.date or datetime.today().strftime('%Y-%m-%d')
    inputs = {
        'commodity': body.commodity, 'market': body.market, 'state': body.state,
        'district':  body.district or '', 'variety': body.variety or 'Other',
        'grade':     body.grade or 'FAQ', 'date': target_date,
        'current_price': body.current_price,
        'min_price': body.min_price, 'max_price': body.max_price,
        'lag_7': body.lag_7, 'lag_14': body.lag_14, 'lag_30': body.lag_30,
    }

    result = svc.predict(inputs)
    chg    = ((result['predicted_price_kg'] - body.current_price) / body.current_price) * 100
    rec    = ("HOLD — prices rising" if chg > 5 else
              "SELL NOW — prices falling" if chg < -5 else
              "NEUTRAL — stable market")

    return PredictResponse(
        commodity               = body.commodity,
        market                  = body.market,
        date                    = target_date,
        current_price_kg        = body.current_price,
        predicted_price_kg      = result['predicted_price_kg'],
        predicted_price_quintal = result['predicted_price_quintal'],
        unit                    = result['unit'],
        confidence              = result['confidence'],
        change_pct              = round(chg, 2),
        recommendation          = rec,
        model_used              = result['model_used'],
        mae_kg                  = result['mae_kg'],
    )
