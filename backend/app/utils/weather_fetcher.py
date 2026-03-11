"""
weather_fetcher.py
Fetches real-time temperature and rainfall for Indian states
using Open-Meteo API — completely FREE, no API key required.
"""

import requests
from typing import Optional, Tuple

# State → (latitude, longitude) — geographic center of each state
STATE_COORDS = {
    "Andhra Pradesh":        (15.9129,  79.7400),
    "Arunachal Pradesh":     (28.2180,  94.7278),
    "Assam":                 (26.2006,  92.9376),
    "Bihar":                 (25.0961,  85.3131),
    "Chhattisgarh":          (21.2787,  81.8661),
    "Goa":                   (15.2993,  74.1240),
    "Gujarat":               (22.2587,  71.1924),
    "Haryana":               (29.0588,  76.0856),
    "Himachal Pradesh":      (31.1048,  77.1734),
    "Jharkhand":             (23.6102,  85.2799),
    "Karnataka":             (15.3173,  75.7139),
    "Kerala":                (10.8505,  76.2711),
    "Madhya Pradesh":        (22.9734,  78.6569),
    "Maharashtra":           (19.7515,  75.7139),
    "Manipur":               (24.6637,  93.9063),
    "Meghalaya":             (25.4670,  91.3662),
    "Mizoram":               (23.1645,  92.9376),
    "Nagaland":              (26.1584,  94.5624),
    "Odisha":                (20.9517,  85.0985),
    "Punjab":                (31.1471,  75.3412),
    "Rajasthan":             (27.0238,  74.2179),
    "Sikkim":                (27.5330,  88.5122),
    "Tamil Nadu":            (11.1271,  78.6569),
    "Telangana":             (18.1124,  79.0193),
    "Tripura":               (23.9408,  91.9882),
    "Uttar Pradesh":         (26.8467,  80.9462),
    "Uttarakhand":           (30.0668,  79.0193),
    "West Bengal":           (22.9868,  87.8550),
    "Delhi":                 (28.7041,  77.1025),
    "Jammu And Kashmir":     (33.7782,  76.5762),
    "Jammu & Kashmir":       (33.7782,  76.5762),
    "Ladakh":                (34.1526,  77.5770),
}

# Seasonal fallback averages (temp °C, rain mm) if API fails
SEASONAL_FALLBACK = {
    "Kharif": (30.0, 150.0),
    "Rabi":   (18.0,  15.0),
    "Zaid":   (36.0,  20.0),
}


def fetch_weather(state: str, season: str) -> Tuple[Optional[float], Optional[float], str]:
    """
    Returns (temperature_celsius, rainfall_mm, source)
    source = 'live' | 'fallback'
    """
    coords = STATE_COORDS.get(state.strip().title())
    if not coords:
        temp, rain = SEASONAL_FALLBACK.get(season, (25.0, 50.0))
        return temp, rain, "fallback_unknown_state"

    lat, lon = coords
    url = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        f"&current=temperature_2m,rain"
        f"&timezone=Asia%2FKolkata"
    )
    try:
        response = requests.get(url, timeout=6)
        response.raise_for_status()
        data    = response.json()
        current = data.get("current", {})
        temp    = current.get("temperature_2m")
        rain    = current.get("rain", 0.0)
        if temp is None:
            raise ValueError("Missing temperature in API response")
        return round(float(temp), 1), round(float(rain), 1), "live"
    except Exception as e:
        print(f"[WeatherFetcher] API failed for {state}: {e} — using seasonal fallback")
        temp, rain = SEASONAL_FALLBACK.get(season, (25.0, 50.0))
        return temp, rain, "fallback_api_error"