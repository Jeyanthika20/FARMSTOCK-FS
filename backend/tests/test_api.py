"""
FarmStock API Tests — COMBINED from files(1).zip + files.zip
=============================================================
Run: cd farmstock/backend && pytest tests/ -v

Test coverage:
  - Health & Info endpoints
  - Price prediction (valid + edge cases + validation)
  - Multi-day forecast
  - Crop health advisory (does NOT need ML model)

Note: Tests marked with @pytest.mark.skipif skip gracefully if the ML model
has not been trained yet. Crop health tests ALWAYS run — they need no model.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

try:
    from main import app
    from fastapi.testclient import TestClient
    client = TestClient(app)
    APP_AVAILABLE = True
except Exception as e:
    print(f"Could not import app: {e}")
    APP_AVAILABLE = False


# ═══════════════════════════════════════════════════════════════
# HEALTH & INFO
# ═══════════════════════════════════════════════════════════════

@pytest.mark.skipif(not APP_AVAILABLE, reason="App not importable")
def test_root():
    r = client.get("/")
    assert r.status_code == 200
    data = r.json()
    assert "version" in data
    assert "endpoints" in data


@pytest.mark.skipif(not APP_AVAILABLE, reason="App not importable")
def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    data = r.json()
    assert "status" in data
    assert "model_loaded" in data
    assert "version" in data


@pytest.mark.skipif(not APP_AVAILABLE, reason="App not importable")
def test_crops_endpoint():
    r = client.get("/api/crops")
    assert r.status_code == 200
    data = r.json()
    assert "crops" in data
    assert "total" in data
    # model not loaded = empty list is also valid
    assert isinstance(data["crops"], list)


@pytest.mark.skipif(not APP_AVAILABLE, reason="App not importable")
def test_markets_endpoint():
    r = client.get("/api/markets")
    assert r.status_code == 200
    data = r.json()
    assert "markets" in data
    assert isinstance(data["markets"], list)


@pytest.mark.skipif(not APP_AVAILABLE, reason="App not importable")
def test_model_info_endpoint():
    r = client.get("/api/model/info")
    assert r.status_code == 200


# ═══════════════════════════════════════════════════════════════
# PRICE PREDICTION
# ═══════════════════════════════════════════════════════════════

@pytest.mark.skipif(not APP_AVAILABLE, reason="App not importable")
def test_predict_minimal_valid():
    """Minimal required fields should work."""
    r = client.post("/api/predict", json={
        "commodity":     "Tomato",
        "market":        "Coimbatore",
        "state":         "Tamil Nadu",
        "current_price": 45.0
    })
    # 200 = model loaded and working; 503 = model not trained yet (both acceptable)
    assert r.status_code in [200, 503]
    if r.status_code == 200:
        data = r.json()
        assert "predicted_price_kg"      in data
        assert "predicted_price_quintal" in data
        assert "confidence"              in data
        assert "recommendation"          in data
        assert "model_used"              in data
        assert data["predicted_price_kg"] > 0
        assert data["predicted_price_quintal"] == round(data["predicted_price_kg"] * 100, 2)


@pytest.mark.skipif(not APP_AVAILABLE, reason="App not importable")
def test_predict_with_full_inputs():
    """Full inputs including lags should return richer prediction."""
    r = client.post("/api/predict", json={
        "commodity":     "Onion",
        "market":        "Nasik",
        "state":         "Maharashtra",
        "district":      "Nashik",
        "variety":       "Local",
        "grade":         "FAQ",
        "date":          "2025-08-15",
        "current_price": 20.0,
        "min_price":     18.0,
        "max_price":     22.0,
        "lag_7":         18.0,
        "lag_14":        17.0,
        "lag_30":        15.0
    })
    assert r.status_code in [200, 503]


@pytest.mark.skipif(not APP_AVAILABLE, reason="App not importable")
def test_predict_missing_commodity():
    """commodity is required — should return 422."""
    r = client.post("/api/predict", json={
        "market":        "Coimbatore",
        "state":         "Tamil Nadu",
        "current_price": 45.0
    })
    assert r.status_code == 422


@pytest.mark.skipif(not APP_AVAILABLE, reason="App not importable")
def test_predict_missing_market():
    r = client.post("/api/predict", json={
        "commodity":     "Tomato",
        "state":         "Tamil Nadu",
        "current_price": 45.0
    })
    assert r.status_code == 422


@pytest.mark.skipif(not APP_AVAILABLE, reason="App not importable")
def test_predict_missing_state():
    r = client.post("/api/predict", json={
        "commodity":     "Tomato",
        "market":        "Coimbatore",
        "current_price": 45.0
    })
    assert r.status_code == 422


@pytest.mark.skipif(not APP_AVAILABLE, reason="App not importable")
def test_predict_missing_current_price():
    r = client.post("/api/predict", json={
        "commodity": "Tomato",
        "market":    "Coimbatore",
        "state":     "Tamil Nadu"
    })
    assert r.status_code == 422


@pytest.mark.skipif(not APP_AVAILABLE, reason="App not importable")
def test_predict_invalid_price_type():
    """Price must be a number, not a string."""
    r = client.post("/api/predict", json={
        "commodity":     "Tomato",
        "market":        "Coimbatore",
        "state":         "Tamil Nadu",
        "current_price": "not_a_number"
    })
    assert r.status_code == 422


@pytest.mark.skipif(not APP_AVAILABLE, reason="App not importable")
def test_predict_empty_body():
    r = client.post("/api/predict", json={})
    assert r.status_code == 422


# ═══════════════════════════════════════════════════════════════
# FORECAST
# ═══════════════════════════════════════════════════════════════

@pytest.mark.skipif(not APP_AVAILABLE, reason="App not importable")
def test_forecast_30_days():
    r = client.post("/api/forecast", json={
        "commodity":     "Tomato",
        "market":        "Coimbatore",
        "state":         "Tamil Nadu",
        "current_price": 45.0,
        "horizon_days":  30
    })
    assert r.status_code in [200, 503]
    if r.status_code == 200:
        data = r.json()
        assert "forecast" in data
        assert len(data["forecast"]) == 30
        assert "summary" in data
        # Check summary keys
        assert "best_sell_date"     in data["summary"]
        assert "best_sell_price_kg" in data["summary"]
        assert "potential_gain_pct" in data["summary"]
        # Check each day has dual-unit prices
        day = data["forecast"][0]
        assert "predicted_price_kg"      in day
        assert "predicted_price_quintal" in day
        assert "recommendation"          in day
        assert day["recommendation"] in ["HOLD", "SELL", "NEUTRAL"]


@pytest.mark.skipif(not APP_AVAILABLE, reason="App not importable")
def test_forecast_7_days():
    r = client.post("/api/forecast", json={
        "commodity":     "Wheat",
        "market":        "Agra",
        "state":         "Uttar Pradesh",
        "current_price": 20.0,
        "horizon_days":  7
    })
    assert r.status_code in [200, 503]
    if r.status_code == 200:
        assert len(r.json()["forecast"]) == 7


@pytest.mark.skipif(not APP_AVAILABLE, reason="App not importable")
def test_forecast_horizon_too_large():
    """horizon_days max is 90 — 200 should fail validation."""
    r = client.post("/api/forecast", json={
        "commodity":     "Tomato",
        "market":        "Coimbatore",
        "state":         "Tamil Nadu",
        "current_price": 45.0,
        "horizon_days":  200
    })
    assert r.status_code == 422


@pytest.mark.skipif(not APP_AVAILABLE, reason="App not importable")
def test_forecast_horizon_zero():
    """horizon_days min is 1 — 0 should fail validation."""
    r = client.post("/api/forecast", json={
        "commodity":     "Tomato",
        "market":        "Coimbatore",
        "state":         "Tamil Nadu",
        "current_price": 45.0,
        "horizon_days":  0
    })
    assert r.status_code == 422


@pytest.mark.skipif(not APP_AVAILABLE, reason="App not importable")
def test_forecast_missing_fields():
    r = client.post("/api/forecast", json={"commodity": "Tomato"})
    assert r.status_code == 422


# ═══════════════════════════════════════════════════════════════
# CROP HEALTH  (from files(1).zip — does NOT need ML model)
# ═══════════════════════════════════════════════════════════════

def test_crop_health_tomato_kharif():
    """Tomato in July (Kharif) should have HIGH disease risk."""
    r = client.post("/api/crop-health", json={
        "commodity":    "Tomato",
        "state":        "Tamil Nadu",
        "month":        7,
        "current_temp": 32.0,
        "rainfall_mm":  180.0
    })
    assert r.status_code == 200
    data = r.json()
    assert data["season"]       == "Kharif"
    assert data["overall_risk"] in ["HIGH", "CRITICAL", "MEDIUM"]
    assert data["plant_advice"] == "CAUTION"
    assert len(data["diseases_to_watch"]) > 0
    assert "weather_advisory" in data
    assert "price_impact"     in data
    assert len(data["tips"])  > 0
    # Check disease structure
    for d in data["diseases_to_watch"]:
        assert "disease"     in d
        assert "risk_level"  in d
        assert "description" in d
        assert "prevention"  in d
        assert d["risk_level"] in ["LOW", "MEDIUM", "HIGH"]


def test_crop_health_wheat_rabi():
    """Wheat in December (Rabi) = GOOD TIME to plant."""
    r = client.post("/api/crop-health", json={
        "commodity": "Wheat",
        "state":     "Punjab",
        "month":     12
    })
    assert r.status_code == 200
    data = r.json()
    assert data["season"]       == "Rabi"
    assert data["plant_advice"] == "GOOD TIME"
    assert data["overall_risk"] in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]


def test_crop_health_potato_rabi():
    """Potato in January (Rabi) — good season."""
    r = client.post("/api/crop-health", json={
        "commodity": "Potato",
        "state":     "West Bengal",
        "month":     1
    })
    assert r.status_code == 200
    data = r.json()
    assert data["season"]       == "Rabi"
    assert data["plant_advice"] == "GOOD TIME"


def test_crop_health_rice_kharif():
    """Rice in July (Kharif) — primary season."""
    r = client.post("/api/crop-health", json={
        "commodity": "Rice",
        "state":     "West Bengal",
        "month":     8
    })
    assert r.status_code == 200
    data = r.json()
    assert data["season"]       == "Kharif"
    assert data["plant_advice"] == "GOOD TIME"
    # Rice in Kharif should have Blast disease listed
    disease_names = [d["disease"] for d in data["diseases_to_watch"]]
    assert any("Blast" in name for name in disease_names)


def test_crop_health_wheat_kharif_avoid():
    """Wheat in July (Kharif) = AVOID."""
    r = client.post("/api/crop-health", json={
        "commodity": "Wheat",
        "state":     "Punjab",
        "month":     7
    })
    assert r.status_code == 200
    data = r.json()
    assert data["season"]       == "Kharif"
    assert data["plant_advice"] == "AVOID"


def test_crop_health_no_weather_data():
    """Works without temp/rainfall — optional fields."""
    r = client.post("/api/crop-health", json={
        "commodity": "Onion",
        "state":     "Maharashtra"
        # no month, no temp, no rain
    })
    assert r.status_code == 200
    data = r.json()
    assert "season"             in data
    assert "overall_risk"       in data
    assert "diseases_to_watch"  in data


def test_crop_health_defaults_to_current_month():
    """When month is omitted, should default to current month gracefully."""
    r = client.post("/api/crop-health", json={
        "commodity": "Tomato",
        "state":     "Tamil Nadu"
    })
    assert r.status_code == 200
    data = r.json()
    from datetime import datetime
    assert data["month"] == datetime.today().month


def test_crop_health_unknown_crop_graceful():
    """Unknown crop should return general advisory, NOT 500 error."""
    r = client.post("/api/crop-health", json={
        "commodity": "UnknownExoticCrop",
        "state":     "Maharashtra",
        "month":     5
    })
    assert r.status_code == 200
    data = r.json()
    assert data["overall_risk"]  == "LOW"
    assert len(data["diseases_to_watch"]) == 1
    assert data["diseases_to_watch"][0]["disease"] == "General Crop Monitoring"


def test_crop_health_weather_heat_warning():
    """Extreme temperature should trigger heat stress advisory."""
    r = client.post("/api/crop-health", json={
        "commodity":    "Tomato",
        "state":        "Rajasthan",
        "month":        5,
        "current_temp": 45.0,
        "rainfall_mm":  5.0
    })
    assert r.status_code == 200
    data = r.json()
    assert "HEAT" in data["weather_advisory"] or "EXTREME" in data["weather_advisory"]


def test_crop_health_weather_heavy_rain():
    """Heavy rainfall should trigger fungal disease warning."""
    r = client.post("/api/crop-health", json={
        "commodity":   "Rice",
        "state":       "Kerala",
        "month":       8,
        "rainfall_mm": 300.0
    })
    assert r.status_code == 200
    data = r.json()
    assert "RAIN" in data["weather_advisory"] or "fungal" in data["weather_advisory"].lower()


def test_crop_health_missing_commodity():
    """commodity is required — should return 422."""
    r = client.post("/api/crop-health", json={"state": "Tamil Nadu", "month": 7})
    assert r.status_code == 422


def test_crop_health_missing_state():
    """state is required — should return 422."""
    r = client.post("/api/crop-health", json={"commodity": "Tomato", "month": 7})
    assert r.status_code == 422


def test_crop_health_invalid_month():
    """Month must be 1–12."""
    r = client.post("/api/crop-health", json={
        "commodity": "Tomato",
        "state":     "Tamil Nadu",
        "month":     15
    })
    assert r.status_code == 422


def test_crop_health_supported_crops():
    """Supported crops endpoint returns the correct list."""
    r = client.get("/api/crop-health/crops")
    assert r.status_code == 200
    data = r.json()
    assert "crops_with_full_data" in data
    assert "total"                in data
    crops = data["crops_with_full_data"]
    assert "Tomato"  in crops
    assert "Wheat"   in crops
    assert "Rice"    in crops
    assert "Onion"   in crops
    assert "Potato"  in crops
    assert data["total"] == len(crops)
