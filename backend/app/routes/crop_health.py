"""
Crop Health & Disease Risk Advisory Route — AI-Powered Version
CHANGES FROM PREVIOUS VERSION:
  - Added POST /api/crop-health/ai endpoint that calls Claude
  - Original rule-based /api/crop-health kept as reliable fallback
  - New /ai endpoint: crop+state+month+temp+rain → Claude → structured JSON
  - Falls back to rule-based if ANTHROPIC_API_KEY not set
  - Returns ai_powered=True/False so frontend shows correct label
"""

import os, json
import httpx
from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

router = APIRouter()
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

# ─── SCHEMAS ────────────────────────────────────────────────────────────────

class CropHealthRequest(BaseModel):
    commodity:    str            = Field(..., example="Tomato")
    state:        str            = Field(..., example="Tamil Nadu")
    month:        Optional[int]  = Field(None, ge=1, le=12, example=7)
    current_temp: Optional[float] = Field(None, example=32.0)
    rainfall_mm:  Optional[float] = Field(None, example=180.0)

class DiseaseRisk(BaseModel):
    disease:     str
    risk_level:  str
    description: str
    prevention:  str

class CropHealthResponse(BaseModel):
    commodity:          str
    state:              str
    month:              int
    season:             str
    overall_risk:       str
    plant_advice:       str
    diseases_to_watch:  List[DiseaseRisk]
    weather_advisory:   str
    price_impact:       str
    tips:               List[str]
    ai_powered:         bool = False
    analysis_note:      str  = ""

# ─── RULE-BASED DATA ────────────────────────────────────────────────────────

DISEASE_CALENDAR = {
    "Tomato": {
        "Kharif": [
            DiseaseRisk(disease="Early Blight (Alternaria)", risk_level="HIGH",
                description="Brown concentric-ring spots on older leaves; spreads fast in humid monsoon.",
                prevention="Spray Mancozeb 2.5 g/L every 10 days. Remove infected leaves immediately."),
            DiseaseRisk(disease="Leaf Curl Virus (TLCV)", risk_level="HIGH",
                description="Leaves curl upward and turn yellow-green; spread by whiteflies.",
                prevention="Use yellow sticky traps. Spray Imidacloprid 0.3 ml/L. Use virus-resistant varieties."),
            DiseaseRisk(disease="Damping Off", risk_level="MEDIUM",
                description="Seedlings collapse at soil level shortly after germination.",
                prevention="Treat seeds with Thiram 3 g/kg before sowing. Avoid waterlogging in nursery."),
        ],
        "Rabi": [
            DiseaseRisk(disease="Late Blight (Phytophthora)", risk_level="MEDIUM",
                description="Water-soaked dark lesions on leaves and fruit in cool, moist weather.",
                prevention="Ensure good field drainage. Spray Metalaxyl + Mancozeb at first sign."),
            DiseaseRisk(disease="Powdery Mildew", risk_level="LOW",
                description="White powdery coating on upper leaf surface in dry cool conditions.",
                prevention="Spray Wettable Sulphur 2 g/L or Hexaconazole 1 ml/L."),
        ],
        "Zaid": [
            DiseaseRisk(disease="Fusarium Wilt", risk_level="HIGH",
                description="Plants wilt and die; vascular tissue turns brown when stem is cut.",
                prevention="Soil solarization before planting. Use Trichoderma-treated seedlings."),
            DiseaseRisk(disease="Fruit Borer (Helicoverpa)", risk_level="MEDIUM",
                description="Larvae bore into fruits causing rotting; visible entry holes.",
                prevention="Install pheromone traps. Spray Spinosad 0.3 ml/L at flower stage."),
        ],
    },
    "Onion": {
        "Kharif": [
            DiseaseRisk(disease="Purple Blotch (Alternaria porri)", risk_level="HIGH",
                description="Purple lesions with yellow halo on leaves; serious in humid conditions.",
                prevention="Spray Iprodione 1.5 ml/L or Mancozeb 2.5 g/L weekly during monsoon."),
            DiseaseRisk(disease="Downy Mildew", risk_level="MEDIUM",
                description="Pale green-yellow lesions; white/violet mold on leaf underside.",
                prevention="Improve drainage. Spray Metalaxyl 2 g/L at first symptom."),
            DiseaseRisk(disease="Basal Rot (Fusarium)", risk_level="MEDIUM",
                description="Bulb base rots; leaves yellow from tip downward.",
                prevention="Avoid waterlogging. Treat bulbs with Carbendazim before planting."),
        ],
        "Rabi": [
            DiseaseRisk(disease="Thrips (Thrips tabaci)", risk_level="MEDIUM",
                description="Tiny insects cause silver-white streaks on leaves.",
                prevention="Spray Spinosad 0.3 ml/L or Imidacloprid 0.3 ml/L every 10 days."),
            DiseaseRisk(disease="Stemphylium Leaf Blight", risk_level="LOW",
                description="Small water-soaked lesions turning yellow-brown on leaf tips.",
                prevention="Spray Mancozeb 2.5 g/L + Carbendazim 0.5 g/L."),
        ],
        "Zaid": [
            DiseaseRisk(disease="Iris Yellow Spot Virus", risk_level="LOW",
                description="Diamond-shaped pale lesions on leaves; spread by thrips.",
                prevention="Control thrips with Imidacloprid. Remove infected plants promptly."),
        ],
    },
    "Potato": {
        "Rabi": [
            DiseaseRisk(disease="Late Blight (Phytophthora infestans)", risk_level="HIGH",
                description="Dark water-soaked lesions turning brown-black. Can destroy entire crop in 2 weeks.",
                prevention="Spray Mancozeb 2.5 g/L every 7 days. Use certified disease-free seed potatoes."),
            DiseaseRisk(disease="Common Scab (Streptomyces)", risk_level="MEDIUM",
                description="Rough, corky scabs on tuber skin. Reduces marketability.",
                prevention="Maintain soil pH 5.0-5.5. Avoid fresh manure. Rotate with non-host crops."),
            DiseaseRisk(disease="Black Scurf (Rhizoctonia)", risk_level="MEDIUM",
                description="Black sclerotia on tuber surface; stem canker causing poor emergence.",
                prevention="Seed treatment with Carbendazim 2 g/kg or Trichoderma 5 g/kg."),
        ],
        "Kharif": [
            DiseaseRisk(disease="Aphid Infestation", risk_level="MEDIUM",
                description="Sap-sucking insects on tender shoots; also transmit viruses.",
                prevention="Spray Dimethoate 2 ml/L or Imidacloprid 0.3 ml/L at first sighting."),
        ],
        "Zaid": [
            DiseaseRisk(disease="Bacterial Soft Rot", risk_level="LOW",
                description="Foul-smelling watery rotting of tubers; worse in hot weather.",
                prevention="Avoid injury during harvest. Store in cool, dry, well-ventilated space."),
        ],
    },
    "Wheat": {
        "Rabi": [
            DiseaseRisk(disease="Yellow Rust / Stripe Rust (Puccinia striiformis)", risk_level="HIGH",
                description="Yellow-orange stripes along leaf veins. Spreads rapidly in cool moist weather. Can cause 70% yield loss.",
                prevention="Spray Propiconazole 1 ml/L at first sign. Use resistant varieties (HD-2967, PBW-343)."),
            DiseaseRisk(disease="Brown Rust / Leaf Rust", risk_level="MEDIUM",
                description="Round orange-brown pustules randomly scattered on leaves.",
                prevention="Spray Mancozeb 2.5 g/L or Propiconazole 1 ml/L."),
            DiseaseRisk(disease="Loose Smut (Ustilago tritici)", risk_level="MEDIUM",
                description="Entire ear replaced by black smut mass; spreads at flowering.",
                prevention="Use hot water treated seed (50 degrees C for 2 hours). Seed treatment with Carboxin + Thiram."),
        ],
        "Kharif": [
            DiseaseRisk(disease="Not a Kharif crop", risk_level="LOW",
                description="Wheat is a Rabi (winter) crop. Planting in Kharif is not recommended.",
                prevention="Wait for Rabi season (Oct-Nov sowing)."),
        ],
        "Zaid": [
            DiseaseRisk(disease="Heat Stress", risk_level="HIGH",
                description="Wheat is not suited for Zaid. High temperatures cause grain shriveling.",
                prevention="Do not plant wheat in April-May. Harvest any standing crop immediately."),
        ],
    },
    "Rice": {
        "Kharif": [
            DiseaseRisk(disease="Blast (Magnaporthe oryzae)", risk_level="HIGH",
                description="Diamond/eye-shaped gray lesions on leaves. Most damaging rice disease; causes 10-50% yield loss.",
                prevention="Seed treatment with Tricyclazole 0.1%. Spray at booting stage. Use resistant varieties."),
            DiseaseRisk(disease="Brown Planthopper (BPH)", risk_level="HIGH",
                description="Insects at base of plant suck sap causing circular patches of dead plants.",
                prevention="Avoid excess nitrogen. Drain field for 3-4 days. Spray Buprofezin 1.5 ml/L."),
            DiseaseRisk(disease="Sheath Blight (Rhizoctonia solani)", risk_level="MEDIUM",
                description="Oval lesions on sheath; worsens with high nitrogen and dense planting.",
                prevention="Spray Validamycin 2 ml/L or Hexaconazole 1 ml/L at tillering."),
            DiseaseRisk(disease="Bacterial Leaf Blight (Xanthomonas)", risk_level="MEDIUM",
                description="Leaf edges turn yellow then brown; spreads through irrigation water.",
                prevention="No chemical cure. Drain field. Use resistant varieties. Avoid excess nitrogen."),
        ],
        "Rabi": [
            DiseaseRisk(disease="Cold Injury", risk_level="MEDIUM",
                description="Rabi rice faces cold stress during booting/flowering in Dec-Jan.",
                prevention="Maintain 5 cm standing water during cold nights. Choose cold-tolerant varieties."),
        ],
        "Zaid": [
            DiseaseRisk(disease="Stem Borer (Scirpophaga)", risk_level="MEDIUM",
                description="Larvae bore into stems causing dead heart in vegetative stage.",
                prevention="Install light traps. Spray Chlorantraniliprole 0.3 ml/L at tillering."),
        ],
    },
}

PLANTING_ADVICE = {
    "Tomato":      {"Kharif": "CAUTION",   "Rabi": "GOOD TIME",  "Zaid": "AVOID"},
    "Onion":       {"Kharif": "CAUTION",   "Rabi": "GOOD TIME",  "Zaid": "CAUTION"},
    "Potato":      {"Kharif": "AVOID",     "Rabi": "GOOD TIME",  "Zaid": "AVOID"},
    "Wheat":       {"Kharif": "AVOID",     "Rabi": "GOOD TIME",  "Zaid": "AVOID"},
    "Rice":        {"Kharif": "GOOD TIME", "Rabi": "CAUTION",    "Zaid": "CAUTION"},
    "Maize":       {"Kharif": "GOOD TIME", "Rabi": "CAUTION",    "Zaid": "CAUTION"},
    "Brinjal":     {"Kharif": "CAUTION",   "Rabi": "GOOD TIME",  "Zaid": "GOOD TIME"},
    "Cabbage":     {"Kharif": "AVOID",     "Rabi": "GOOD TIME",  "Zaid": "AVOID"},
    "Cauliflower": {"Kharif": "AVOID",     "Rabi": "GOOD TIME",  "Zaid": "AVOID"},
}

PRICE_IMPACT_BY_RISK = {
    "CRITICAL": "CRITICAL OUTBREAK RISK - Expect prices to DOUBLE within 2-3 weeks as supply collapses. If you have stock, sell immediately.",
    "HIGH":     "HIGH DISEASE PRESSURE - Expect 20-40% price RISE in 2-3 weeks as affected farms reduce supply.",
    "MEDIUM":   "MODERATE RISK - Prices may rise 5-15% if disease spreads. Monitor closely.",
    "LOW":      "LOW DISEASE PRESSURE - Supply likely stable. Prices expected to remain normal.",
}

MONTH_NAMES = ["","January","February","March","April","May","June",
               "July","August","September","October","November","December"]

# ─── HELPERS ────────────────────────────────────────────────────────────────

def get_season(month):
    if month in [6,7,8,9,10]:    return "Kharif"
    elif month in [11,12,1,2,3]: return "Rabi"
    else:                         return "Zaid"

def get_overall_risk(diseases):
    highs = sum(1 for d in diseases if d.risk_level == "HIGH")
    if highs >= 3: return "CRITICAL"
    if highs >= 2: return "HIGH"
    if highs == 1: return "MEDIUM"
    return "LOW"

def build_weather_advisory(temp, rain, season):
    if temp is None and rain is None:
        return "No weather data provided - general seasonal risk advisory applied."
    parts = []
    if temp is not None:
        if temp > 40:
            parts.append(f"EXTREME HEAT ({temp}C): Risk of flower drop. Provide shade nets. Irrigate in evening.")
        elif temp > 36:
            parts.append(f"HIGH TEMP ({temp}C): Avoid afternoon irrigation. Monitor for heat stress wilting.")
        elif temp < 8:
            parts.append(f"COLD STRESS ({temp}C): Cover sensitive crops at night. Risk of frost damage.")
        elif 22 <= temp <= 32:
            parts.append(f"Temperature {temp}C is optimal for most crops.")
        else:
            parts.append(f"Temperature {temp}C - within acceptable range.")
    if rain is not None:
        if rain > 250:
            parts.append(f"HEAVY RAIN ({rain} mm): HIGH fungal disease risk. Spray preventive fungicide within 24 hours.")
        elif rain > 120:
            parts.append(f"HIGH RAIN ({rain} mm): Monitor for fungal diseases closely.")
        elif rain < 15 and season == "Kharif":
            parts.append(f"LOW RAINFALL ({rain} mm) during monsoon: Supplement with irrigation.")
        else:
            parts.append(f"Rainfall {rain} mm - within normal range for the season.")
    return " | ".join(parts)

def get_tips(season, overall_risk, commodity):
    tips = [
        f"Season: {season} - follow the recommended spray calendar for this season.",
        "Always use certified disease-free seeds from government-approved nurseries.",
        "Practice crop rotation - avoid planting the same crop consecutively.",
        "Keep a field diary: record spray dates, products used, and weather conditions.",
    ]
    if overall_risk in ["HIGH", "CRITICAL"]:
        tips.append("Start PREVENTIVE spraying NOW - do not wait for visible symptoms.")
        tips.append("Inform your local Krishi Vigyan Kendra (KVK) if you see widespread infection.")
    if season == "Kharif":
        tips.append("Monsoon tip: Clear all drainage channels before heavy rain season.")
    elif season == "Rabi":
        tips.append("Winter tip: Protect seedlings from frost with mulching or light irrigation at night.")
    elif season == "Zaid":
        tips.append("Summer tip: Use drip irrigation to conserve water. Apply straw mulch.")
    return tips

# ─── AI CALL ────────────────────────────────────────────────────────────────

def build_ai_prompt(commodity, state, month, season, temp, rain):
    weather_ctx = ""
    if temp is not None: weather_ctx += f"Current temperature: {temp}C. "
    if rain is not None: weather_ctx += f"Recent rainfall: {rain} mm. "
    if not weather_ctx:  weather_ctx = "No specific weather data - use seasonal averages for this region."

    return f"""You are an expert Indian agricultural scientist specializing in crop disease management for Indian farming conditions.

A farmer needs a crop health advisory:
- Crop: {commodity}
- State: {state}
- Month: {MONTH_NAMES[month]} (Month {month})
- Season: {season}
- Weather: {weather_ctx}

Provide a comprehensive crop health analysis specific to {state} conditions in {season}.

Respond ONLY with valid JSON (no markdown, no extra text):
{{
  "overall_risk": "LOW|MEDIUM|HIGH|CRITICAL",
  "plant_advice": "GOOD TIME|CAUTION|AVOID",
  "diseases_to_watch": [
    {{
      "disease": "disease name",
      "risk_level": "LOW|MEDIUM|HIGH|CRITICAL",
      "description": "symptoms and how it damages the crop",
      "prevention": "specific spray/action with Indian product names and doses"
    }}
  ],
  "weather_advisory": "advisory based on provided temperature and rainfall",
  "price_impact": "expected market price impact with realistic percentage changes",
  "tips": ["tip1", "tip2", "tip3", "tip4"],
  "analysis_note": "brief explanation of why the risk is what it is"
}}

Include 2-5 diseases genuinely relevant to {commodity} in {season} in {state}.
Prevention must include specific fungicides/pesticides with actual doses used in India."""

async def call_claude_for_crop_health(commodity, state, month, season, temp, rain):
    if not ANTHROPIC_API_KEY:
        return None
    prompt = build_ai_prompt(commodity, state, month, season, temp, rain)
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": ANTHROPIC_API_KEY,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": "claude-sonnet-4-20250514",
                    "max_tokens": 2000,
                    "messages": [{"role": "user", "content": prompt}],
                }
            )
        if resp.status_code != 200:
            return None
        data = resp.json()
        text = data["content"][0]["text"].strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        return json.loads(text.strip())
    except Exception:
        return None

# ─── ENDPOINTS ──────────────────────────────────────────────────────────────

@router.post("/crop-health", response_model=CropHealthResponse,
             summary="Rule-based crop health advisory (fast, no API key needed)")
def crop_health_check(body: CropHealthRequest):
    month     = body.month if body.month is not None else datetime.today().month
    season    = get_season(month)
    commodity = body.commodity.strip().title()
    crop_data = DISEASE_CALENDAR.get(commodity, {})
    diseases  = crop_data.get(season) or [
        DiseaseRisk(disease="General Crop Monitoring", risk_level="LOW",
            description=f"No specific disease calendar for {commodity} in {season}. General monitoring recommended.",
            prevention="Maintain good field hygiene. Ensure proper spacing. Use balanced NPK fertilization.")
    ]
    overall_risk = get_overall_risk(diseases)
    plant_advice = PLANTING_ADVICE.get(commodity, {}).get(season, "CAUTION")
    return CropHealthResponse(
        commodity=body.commodity, state=body.state, month=month, season=season,
        overall_risk=overall_risk, plant_advice=plant_advice,
        diseases_to_watch=diseases,
        weather_advisory=build_weather_advisory(body.current_temp, body.rainfall_mm, season),
        price_impact=PRICE_IMPACT_BY_RISK.get(overall_risk, PRICE_IMPACT_BY_RISK["LOW"]),
        tips=get_tips(season, overall_risk, commodity),
        ai_powered=False,
        analysis_note="Rule-based advisory using verified agricultural disease calendars.",
    )


@router.post("/crop-health/ai", response_model=CropHealthResponse,
             summary="AI-powered crop health (requires ANTHROPIC_API_KEY env var)")
async def crop_health_ai(body: CropHealthRequest):
    month     = body.month if body.month is not None else datetime.today().month
    season    = get_season(month)
    commodity = body.commodity.strip().title()

    ai_result = await call_claude_for_crop_health(commodity, body.state, month, season,
                                                   body.current_temp, body.rainfall_mm)
    if ai_result:
        try:
            diseases = [
                DiseaseRisk(disease=d["disease"], risk_level=d["risk_level"],
                            description=d["description"], prevention=d["prevention"])
                for d in ai_result.get("diseases_to_watch", [])
            ]
            if diseases:
                return CropHealthResponse(
                    commodity=body.commodity, state=body.state, month=month, season=season,
                    overall_risk=ai_result.get("overall_risk", "MEDIUM"),
                    plant_advice=ai_result.get("plant_advice", "CAUTION"),
                    diseases_to_watch=diseases,
                    weather_advisory=ai_result.get("weather_advisory", ""),
                    price_impact=ai_result.get("price_impact", ""),
                    tips=ai_result.get("tips", []),
                    ai_powered=True,
                    analysis_note=ai_result.get("analysis_note",
                        f"AI analysis for {commodity} in {body.state} ({season} season)."),
                )
        except (KeyError, ValueError):
            pass

    # Fallback
    crop_data    = DISEASE_CALENDAR.get(commodity, {})
    diseases     = crop_data.get(season) or [
        DiseaseRisk(disease="General Crop Monitoring", risk_level="LOW",
            description=f"No specific data for {commodity} in {season}.",
            prevention="Maintain good field hygiene and proper spacing.")
    ]
    overall_risk = get_overall_risk(diseases)
    note = ("Set ANTHROPIC_API_KEY environment variable to enable AI-powered analysis."
            if not ANTHROPIC_API_KEY else "AI analysis failed - showing rule-based advisory.")
    return CropHealthResponse(
        commodity=body.commodity, state=body.state, month=month, season=season,
        overall_risk=overall_risk,
        plant_advice=PLANTING_ADVICE.get(commodity, {}).get(season, "CAUTION"),
        diseases_to_watch=diseases,
        weather_advisory=build_weather_advisory(body.current_temp, body.rainfall_mm, season),
        price_impact=PRICE_IMPACT_BY_RISK.get(overall_risk, PRICE_IMPACT_BY_RISK["LOW"]),
        tips=get_tips(season, overall_risk, commodity),
        ai_powered=False, analysis_note=note,
    )


@router.get("/crop-health/crops", summary="List crops with full disease advisory data")
def health_supported_crops():
    return {
        "crops_with_full_data": sorted(DISEASE_CALENDAR.keys()),
        "total": len(DISEASE_CALENDAR),
        "note": "All other crops receive a general advisory.",
        "ai_note": "With ANTHROPIC_API_KEY set, ALL crops get full AI-powered analysis via /crop-health/ai.",
    }
