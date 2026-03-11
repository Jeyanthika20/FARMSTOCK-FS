"""Pydantic schemas v2 — prices in Rs/kg + Rs/quintal both shown."""
from pydantic import BaseModel, Field , ConfigDict
from typing import Optional, List


class PredictRequest(BaseModel):
    commodity:     str   = Field(..., example="Tomato")
    market:        str   = Field(..., example="Coimbatore")
    state:         str   = Field(..., example="Tamil Nadu")
    district:      Optional[str]  = Field(None, example="Coimbatore")
    variety:       Optional[str]  = Field("Other", example="Local")
    grade:         Optional[str]  = Field("FAQ",   example="FAQ")
    date:          Optional[str]  = Field(None,    example="2025-06-15")
    current_price: float          = Field(...,     example=45.0,
                                          description="Current price in Rs/kg  (e.g. 45.0)")
    min_price:     Optional[float] = Field(None,   example=40.0)
    max_price:     Optional[float] = Field(None,   example=50.0)
    lag_7:         Optional[float] = Field(None,   example=42.0, description="Price 7 days ago Rs/kg")
    lag_14:        Optional[float] = Field(None,   example=41.0)
    lag_30:        Optional[float] = Field(None,   example=38.0)

    class Config:
        json_schema_extra = {"example": {
            "commodity":"Tomato","market":"Coimbatore","state":"Tamil Nadu",
            "current_price":45.0,"min_price":40.0,"max_price":50.0,
            "lag_7":42.0,"lag_14":41.0,"lag_30":38.0
        }}


class PredictResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())  # ← add this line

    commodity: str
    market:                  str
    date:                    str
    current_price_kg:        float
    predicted_price_kg:      float
    predicted_price_quintal: float
    unit:                    str
    confidence:              float
    change_pct:              float
    recommendation:          str
    model_used:              str
    mae_kg:                  float


class ForecastRequest(BaseModel):
    commodity:     str   = Field(..., example="Tomato")
    market:        str   = Field(..., example="Coimbatore")
    state:         str   = Field(..., example="Tamil Nadu")
    current_price: float = Field(..., example=45.0, description="Current price Rs/kg")
    horizon_days:  int   = Field(30, ge=1, le=90, example=30)

    class Config:
        json_schema_extra = {"example": {
            "commodity":"Tomato","market":"Coimbatore","state":"Tamil Nadu",
            "current_price":45.0,"horizon_days":30
        }}


class ForecastDay(BaseModel):
    day:                     int
    date:                    str
    predicted_price_kg:      float
    predicted_price_quintal: float
    change_from_today:       float
    recommendation:          str


class ForecastResponse(BaseModel):
    commodity:     str
    market:        str
    current_price: float
    horizon_days:  int
    forecast:      List[ForecastDay]
    summary:       dict


class HealthResponse(BaseModel):
    status:       str
    model_loaded: bool
    model_name:   str
    version:      str
