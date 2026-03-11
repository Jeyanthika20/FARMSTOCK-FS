"""
Crop Health & Disease Risk Advisory Route  — v2 (Real-Time Weather)

Endpoint: POST /api/crop-health
Changes in v2:
  - Auto-fetches real-time temperature & rainfall from Open-Meteo API
    using the farmer's state — no manual weather input needed.
  - Response now includes 'weather_source' field: 'live' / 'user_provided' / 'fallback'
  - Graceful fallback to seasonal averages if API is unreachable.
"""

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List
from datetime import datetime

from app.utils.weather_fetcher import fetch_weather   # ← new import

router = APIRouter()


# ═══════════════════════════════════════════════════════════════
# REQUEST / RESPONSE SCHEMAS
# ═══════════════════════════════════════════════════════════════

class CropHealthRequest(BaseModel):
    commodity:    str             = Field(..., example="Tomato")
    state:        str             = Field(..., example="Tamil Nadu")
    month:        Optional[int]   = Field(None, ge=1, le=12, example=7)
    current_temp: Optional[float] = Field(None, example=32.0,
                                          description="Optional. Auto-fetched from weather API if not provided.")
    rainfall_mm:  Optional[float] = Field(None, example=180.0,
                                          description="Optional. Auto-fetched from weather API if not provided.")

    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra={"example": {
            "commodity": "Tomato",
            "state":     "Tamil Nadu",
            "month":     7,
        }}
    )


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
    weather_source:     str          # ← NEW: 'live' | 'user_provided' | 'fallback_...'
    current_temp:       float        # ← NEW: actual temp used (fetched or user-given)
    rainfall_mm:        float        # ← NEW: actual rain used
    price_impact:       str
    tips:               List[str]

    model_config = ConfigDict(protected_namespaces=())


# ═══════════════════════════════════════════════════════════════
# DISEASE CALENDAR  (unchanged — your original data)
# ═══════════════════════════════════════════════════════════════

DISEASE_CALENDAR: dict = {
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
                description="Tiny insects cause silver-white streaks on leaves; severe in dry weather.",
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
                description="Dark water-soaked lesions on leaves turning brown-black. Can destroy crop in 2 weeks.",
                prevention="Spray Mancozeb 2.5 g/L every 7 days. Use certified disease-free seed potatoes."),
            DiseaseRisk(disease="Common Scab (Streptomyces)", risk_level="MEDIUM",
                description="Rough corky scabs on tuber skin. Reduces marketability.",
                prevention="Maintain soil pH 5.0–5.5. Avoid fresh manure. Rotate with non-host crops."),
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
                description="Yellow-orange stripes of pustules along leaf veins. Can cause 70% yield loss.",
                prevention="Spray Propiconazole 1 ml/L at first sign. Use resistant varieties HD-2967, PBW-343."),
            DiseaseRisk(disease="Brown Rust / Leaf Rust (Puccinia triticina)", risk_level="MEDIUM",
                description="Round orange-brown pustules randomly scattered on leaves.",
                prevention="Spray Mancozeb 2.5 g/L or Propiconazole 1 ml/L. Use rust-resistant varieties."),
            DiseaseRisk(disease="Loose Smut (Ustilago tritici)", risk_level="MEDIUM",
                description="Entire ear replaced by black smut mass; spreads at flowering.",
                prevention="Use hot water treated seed (50°C for 2 hours). Treat with Carboxin + Thiram."),
            DiseaseRisk(disease="Powdery Mildew", risk_level="LOW",
                description="White powdery growth on upper leaf surface in dense crops.",
                prevention="Maintain proper spacing. Spray Triadimefon 1 g/L if severe."),
        ],
        "Kharif": [
            DiseaseRisk(disease="Not a Kharif crop", risk_level="LOW",
                description="Wheat is a Rabi (winter) crop. Planting in Kharif is not recommended.",
                prevention="Wait for Rabi season (Oct–Nov sowing)."),
        ],
        "Zaid": [
            DiseaseRisk(disease="Heat Stress", risk_level="HIGH",
                description="Wheat is not suited for Zaid. High temperatures cause grain shriveling.",
                prevention="Do not plant wheat in April–May. Harvest any standing crop immediately."),
        ],
    },
    "Rice": {
        "Kharif": [
            DiseaseRisk(disease="Blast (Magnaporthe oryzae)", risk_level="HIGH",
                description="Diamond/eye-shaped gray lesions on leaves. Can cause 10–50% yield loss.",
                prevention="Seed treatment with Tricyclazole 0.1%. Spray at booting stage."),
            DiseaseRisk(disease="Brown Planthopper (BPH)", risk_level="HIGH",
                description="Insects at base suck sap; causes hopperburn. Can devastate field in 3–5 days.",
                prevention="Avoid excess nitrogen. Drain field 3–4 days. Spray Buprofezin 1.5 ml/L."),
            DiseaseRisk(disease="Sheath Blight (Rhizoctonia solani)", risk_level="MEDIUM",
                description="Oval lesions on sheath; white mycelium in humid conditions.",
                prevention="Spray Validamycin 2 ml/L or Hexaconazole 1 ml/L at tillering."),
            DiseaseRisk(disease="Bacterial Leaf Blight (Xanthomonas)", risk_level="MEDIUM",
                description="Leaf edges turn yellow then brown. Spreads through irrigation water.",
                prevention="No chemical cure. Drain field. Use resistant varieties. Avoid excess nitrogen."),
        ],
        "Rabi": [
            DiseaseRisk(disease="Cold Injury", risk_level="MEDIUM",
                description="Rabi rice faces cold stress during booting/flowering in Dec–Jan.",
                prevention="Maintain 5 cm standing water during cold nights. Choose cold-tolerant varieties."),
        ],
        "Zaid": [
            DiseaseRisk(disease="Stem Borer (Scirpophaga)", risk_level="MEDIUM",
                description="Larvae bore into stems causing dead heart in vegetative stage.",
                prevention="Install light traps. Spray Chlorantraniliprole 0.3 ml/L at tillering."),
        ],
    },
    "Maize": {
        "Kharif": [
            DiseaseRisk(
                disease     = "Fall Armyworm (Spodoptera frugiperda)",
                risk_level  = "HIGH",
                description = "Larvae bore into whorl and eat leaves; sawdust-like frass visible. "
                              "Introduced pest — spreading rapidly across India since 2018.",
                prevention  = "Spray Emamectin Benzoate 0.4 g/L or Spinetoram 0.5 ml/L. "
                              "Apply into whorl at first sign. Use pheromone traps for monitoring."
            ),
            DiseaseRisk(
                disease     = "Turcicum Leaf Blight (Exserohilum turcicum)",
                risk_level  = "MEDIUM",
                description = "Long cigar-shaped gray-green lesions on leaves; severe in humid monsoon.",
                prevention  = "Spray Mancozeb 2.5 g/L or Propiconazole 1 ml/L. Use resistant hybrids."
            ),
            DiseaseRisk(
                disease     = "Stem Borer (Chilo partellus)",
                risk_level  = "MEDIUM",
                description = "Dead heart in young plants; shot hole appearance on leaves.",
                prevention  = "Apply Carbofuran 3G granules in whorl at 10–15 days after germination."
            ),
        ],
        "Rabi": [
            DiseaseRisk(
                disease     = "Downy Mildew (Peronosclerospora)",
                risk_level  = "MEDIUM",
                description = "White downy growth on lower leaf surface; stunted plants with pale leaves.",
                prevention  = "Seed treatment with Metalaxyl 6 g/kg. Avoid waterlogging."
            ),
        ],
        "Zaid": [
            DiseaseRisk(
                disease     = "Heat + Moisture Stress",
                risk_level  = "HIGH",
                description = "Zaid maize faces pollination failure above 38°C and grain shriveling.",
                prevention  = "Irrigate at silking and grain-filling stage. Sow early (Feb) to avoid peak heat."
            ),
        ],
    },

    "Brinjal": {
        "Kharif": [
            DiseaseRisk(
                disease     = "Shoot and Fruit Borer (Leucinodes orbonalis)",
                risk_level  = "HIGH",
                description = "Most serious brinjal pest. Larvae bore into shoots causing wilting, "
                              "then into fruits making them unmarketable.",
                prevention  = "Install pheromone traps. Spray Spinosad 0.3 ml/L or "
                              "Chlorantraniliprole 0.3 ml/L at 10-day intervals."
            ),
            DiseaseRisk(
                disease     = "Phomopsis Blight",
                risk_level  = "MEDIUM",
                description = "Dark water-soaked lesions on leaves, stem, and fruits in humid conditions.",
                prevention  = "Spray Copper Oxychloride 3 g/L or Mancozeb 2.5 g/L every 10 days."
            ),
        ],
        "Rabi": [
            DiseaseRisk(
                disease     = "Bacterial Wilt (Ralstonia solanacearum)",
                risk_level  = "HIGH",
                description = "Sudden wilting of entire plant; vascular tissue turns brown.",
                prevention  = "Soil drench with Streptocycline 0.5 g/L. Use grafted seedlings on resistant rootstock."
            ),
            DiseaseRisk(
                disease     = "Little Leaf (Phytoplasma)",
                risk_level  = "MEDIUM",
                description = "Leaves become very small and pale; plant becomes bushy and sterile.",
                prevention  = "Control leafhopper vectors with Imidacloprid 0.3 ml/L. Remove and destroy infected plants."
            ),
        ],
        "Zaid": [
            DiseaseRisk(
                disease     = "Red Spider Mite",
                risk_level  = "MEDIUM",
                description = "Tiny mites under leaves cause yellowing and bronzing; worse in hot dry weather.",
                prevention  = "Spray Dicofol 2.5 ml/L or Abamectin 0.5 ml/L. Increase field humidity."
            ),
        ],
    },

    "Cabbage": {
        "Rabi": [
            DiseaseRisk(
                disease     = "Diamond Back Moth (Plutella xylostella)",
                risk_level  = "HIGH",
                description = "Most destructive cabbage pest worldwide. Larvae scrape leaf surface "
                              "leaving translucent windows; heavy attack skeletonizes leaves.",
                prevention  = "Spray Spinosad 0.3 ml/L or Emamectin Benzoate 0.4 g/L. "
                              "Rotate insecticides to prevent resistance."
            ),
            DiseaseRisk(
                disease     = "Black Rot (Xanthomonas campestris)",
                risk_level  = "HIGH",
                description = "V-shaped yellow lesions at leaf margins; veins turn black. "
                              "Entire head can rot internally.",
                prevention  = "Use disease-free seeds. Hot water seed treatment (50°C, 30 min). "
                              "Spray Copper Oxychloride 3 g/L at first sign."
            ),
            DiseaseRisk(
                disease     = "Club Root (Plasmodiophora brassicae)",
                risk_level  = "MEDIUM",
                description = "Roots develop club-shaped swellings; plants wilt and stunt.",
                prevention  = "Maintain soil pH above 7.2 with lime. Avoid infected transplants. "
                              "Long crop rotation (4+ years)."
            ),
        ],
        "Kharif": [
            DiseaseRisk(
                disease     = "Not recommended in Kharif",
                risk_level  = "HIGH",
                description = "Cabbage is a cool-season crop. Monsoon heat and humidity cause "
                              "rapid disease spread and poor head formation.",
                prevention  = "Wait for Rabi season (Oct–Nov transplanting) for best results."
            ),
        ],
        "Zaid": [
            DiseaseRisk(
                disease     = "Heat Stress + Bolting",
                risk_level  = "HIGH",
                description = "Cabbage bolts (goes to seed) in Zaid heat without forming heads.",
                prevention  = "Avoid Zaid planting. If unavoidable, use heat-tolerant varieties with shade nets."
            ),
        ],
    },

    "Cauliflower": {
        "Rabi": [
            DiseaseRisk(
                disease     = "Downy Mildew (Peronospora parasitica)",
                risk_level  = "HIGH",
                description = "Yellow patches on upper leaf surface with white mold underneath. "
                              "Curd turns brown and unmarketable in humid conditions.",
                prevention  = "Spray Metalaxyl + Mancozeb 2.5 g/L. Ensure good air circulation between plants."
            ),
            DiseaseRisk(
                disease     = "Black Rot (Xanthomonas)",
                risk_level  = "MEDIUM",
                description = "V-shaped lesions at leaf margins; progresses to curd browning.",
                prevention  = "Hot water seed treatment. Spray Copper Oxychloride 3 g/L preventively."
            ),
            DiseaseRisk(
                disease     = "Whiptail (Molybdenum deficiency)",
                risk_level  = "LOW",
                description = "Leaves become strap-like and twisted; common in acidic soils.",
                prevention  = "Apply Ammonium Molybdate 0.1 g/L as foliar spray. Correct soil pH to 6.5–7.0."
            ),
        ],
        "Kharif": [
            DiseaseRisk(
                disease     = "Not ideal in Kharif",
                risk_level  = "MEDIUM",
                description = "Early Kharif varieties exist but face high pest and disease pressure.",
                prevention  = "Use only Kharif-specific varieties (e.g. Early Kunwari). Spray preventively."
            ),
        ],
        "Zaid": [
            DiseaseRisk(
                disease     = "Curd Browning from Heat",
                risk_level  = "HIGH",
                description = "High temperatures cause curd to open, brown, and lose market value rapidly.",
                prevention  = "Tie leaves over curd to protect from direct sun. Harvest early in morning."
            ),
        ],
    },

    "Green Chilli": {
        "Kharif": [
            DiseaseRisk(
                disease     = "Chilli Thrips (Scirtothrips dorsalis)",
                risk_level  = "HIGH",
                description = "Tiny insects cause upward leaf curling, stunting, and silvery scars on fruits.",
                prevention  = "Spray Spinosad 0.3 ml/L or Fipronil 2 ml/L. Use blue sticky traps for monitoring."
            ),
            DiseaseRisk(
                disease     = "Anthracnose / Fruit Rot (Colletotrichum)",
                risk_level  = "HIGH",
                description = "Circular sunken spots on ripening fruits; entire fruit rots in humid monsoon. "
                              "Major post-harvest loss cause.",
                prevention  = "Spray Carbendazim 1 g/L + Mancozeb 2.5 g/L every 10 days during fruiting."
            ),
            DiseaseRisk(
                disease     = "Phytophthora Blight",
                risk_level  = "MEDIUM",
                description = "Water-soaked lesions on stem at soil level; plant collapses suddenly.",
                prevention  = "Avoid waterlogging. Drench soil with Metalaxyl 2 g/L around stem base."
            ),
        ],
        "Rabi": [
            DiseaseRisk(
                disease     = "Powdery Mildew",
                risk_level  = "MEDIUM",
                description = "White powdery coating on leaves and stems in cool dry weather.",
                prevention  = "Spray Wettable Sulphur 2 g/L or Hexaconazole 1 ml/L."
            ),
            DiseaseRisk(
                disease     = "Mosaic Virus (CMV)",
                risk_level  = "LOW",
                description = "Mottled yellow-green mosaic pattern on leaves; stunted growth.",
                prevention  = "Control aphid vectors with Imidacloprid 0.3 ml/L. Remove infected plants."
            ),
        ],
        "Zaid": [
            DiseaseRisk(
                disease     = "Mites + Sunscald",
                risk_level  = "MEDIUM",
                description = "Spider mites explode in dry summer heat; fruits also get sunscald bleaching.",
                prevention  = "Spray Abamectin 0.5 ml/L for mites. Provide partial shade and mulch soil."
            ),
        ],
    },

    "Banana": {
        "Kharif": [
            DiseaseRisk(
                disease     = "Sigatoka Leaf Spot (Mycosphaerella musicola)",
                risk_level  = "HIGH",
                description = "Yellow streaks turning brown-black on leaves; severe defoliation "
                              "reduces bunch weight by 30–50%.",
                prevention  = "Spray Propiconazole 1 ml/L or Mancozeb 2.5 g/L every 3 weeks. "
                              "Remove and destroy severely affected leaves."
            ),
            DiseaseRisk(
                disease     = "Banana Weevil Borer (Cosmopolites sordidus)",
                risk_level  = "MEDIUM",
                description = "Larvae tunnel through corm causing plant toppling and poor bunch development.",
                prevention  = "Use pheromone traps. Apply Chlorpyrifos 5G in soil around corm at planting."
            ),
        ],
        "Rabi": [
            DiseaseRisk(
                disease     = "Panama Wilt / Fusarium Wilt",
                risk_level  = "HIGH",
                description = "Leaves yellow from outer to inner; pseudostem splits at base. "
                              "Soil-borne — no chemical cure once infected. Can persist 30 years in soil.",
                prevention  = "Use resistant varieties (Grand Naine, Nendran). "
                              "Soil application of Trichoderma 50 g/plant. Never replant in infected soil."
            ),
            DiseaseRisk(
                disease     = "Banana Bunchy Top Virus (BBTV)",
                risk_level  = "MEDIUM",
                description = "Leaves become narrow, bunchy, and erect at top; plant never fruits.",
                prevention  = "Use virus-indexed tissue culture planting material. "
                              "Control aphid vectors immediately. Destroy infected plants with herbicide."
            ),
        ],
        "Zaid": [
            DiseaseRisk(
                disease     = "Heat + Water Stress",
                risk_level  = "MEDIUM",
                description = "Banana needs high water in summer. Drought stress causes premature ripening.",
                prevention  = "Drip irrigate 8–10 liters/plant/day in summer. Mulch heavily around plants."
            ),
        ],
    },

    "Mango": {
        "Kharif": [
            DiseaseRisk(
                disease     = "Mango Fruit Fly (Bactrocera dorsalis)",
                risk_level  = "HIGH",
                description = "Larvae develop inside ripening fruit causing internal rot. "
                              "Major cause of post-harvest loss in India.",
                prevention  = "Install methyl eugenol traps (1 per acre). "
                              "Bag individual fruits. Spray Malathion 2 ml/L + protein bait."
            ),
            DiseaseRisk(
                disease     = "Anthracnose (Colletotrichum gloeosporioides)",
                risk_level  = "HIGH",
                description = "Black spots on leaves, flowers, and fruits. Flower blight causes "
                              "heavy fruit drop. Post-harvest fruit rotting.",
                prevention  = "Spray Carbendazim 1 g/L at flowering, fruit set, and 15 days before harvest."
            ),
        ],
        "Rabi": [
            DiseaseRisk(
                disease     = "Powdery Mildew (Oidium mangiferae)",
                risk_level  = "HIGH",
                description = "White powdery coating on flowers and young fruits. "
                              "Causes flower and fruit drop. Critical during flowering (Jan–Feb).",
                prevention  = "Spray Wettable Sulphur 2 g/L or Hexaconazole 1 ml/L at bud break, "
                              "full bloom, and fruit set stages."
            ),
            DiseaseRisk(
                disease     = "Mango Hopper (Idioscopus spp.)",
                risk_level  = "MEDIUM",
                description = "Nymphs and adults suck sap from flowers and tender shoots; "
                              "honeydew leads to sooty mold.",
                prevention  = "Spray Imidacloprid 0.3 ml/L or Carbaryl 2 g/L at panicle emergence."
            ),
        ],
        "Zaid": [
            DiseaseRisk(
                disease     = "Stem End Rot (Lasiodiplodia)",
                risk_level  = "MEDIUM",
                description = "Black rot starting from stem end of harvested fruit; spreads rapidly.",
                prevention  = "Harvest with 5 cm stalk. Hot water treatment (52°C, 5 min) post-harvest. "
                              "Store in cool, ventilated conditions."
            ),
        ],
    },
}

PLANTING_ADVICE: dict = {
    "Tomato":      {"Kharif": "CAUTION",   "Rabi": "GOOD TIME",  "Zaid": "AVOID"},
    "Onion":       {"Kharif": "CAUTION",   "Rabi": "GOOD TIME",  "Zaid": "CAUTION"},
    "Potato":      {"Kharif": "AVOID",     "Rabi": "GOOD TIME",  "Zaid": "AVOID"},
    "Wheat":       {"Kharif": "AVOID",     "Rabi": "GOOD TIME",  "Zaid": "AVOID"},
    "Rice":        {"Kharif": "GOOD TIME", "Rabi": "CAUTION",    "Zaid": "CAUTION"},
    "Maize":       {"Kharif": "GOOD TIME", "Rabi": "CAUTION",    "Zaid": "CAUTION"},
    "Brinjal":     {"Kharif": "CAUTION",   "Rabi": "GOOD TIME",  "Zaid": "GOOD TIME"},
    "Cabbage":     {"Kharif": "AVOID",     "Rabi": "GOOD TIME",  "Zaid": "AVOID"},
    "Cauliflower": {"Kharif": "AVOID",     "Rabi": "GOOD TIME",  "Zaid": "AVOID"},
    "Green Chilli": {"Kharif": "GOOD TIME", "Rabi": "CAUTION",   "Zaid": "AVOID"},
    "Banana":       {"Kharif": "GOOD TIME", "Rabi": "GOOD TIME", "Zaid": "CAUTION"},
    "Mango":        {"Kharif": "CAUTION",   "Rabi": "GOOD TIME", "Zaid": "AVOID"},
}

PRICE_IMPACT_BY_RISK: dict = {
    "CRITICAL": "CRITICAL OUTBREAK RISK — Expect prices to DOUBLE within 2–3 weeks as supply collapses. Sell immediately.",
    "HIGH":     "HIGH DISEASE PRESSURE — Expect 20–40% price RISE in 2–3 weeks. Consider holding if storage is safe.",
    "MEDIUM":   "MODERATE RISK — Prices may rise 5–15% if disease spreads. Monitor and spray preventively.",
    "LOW":      "LOW DISEASE PRESSURE — Supply likely stable. Prices expected to remain normal.",
}


# ═══════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def get_season(month: int) -> str:
    if month in [6, 7, 8, 9, 10]:    return "Kharif"
    elif month in [11, 12, 1, 2, 3]: return "Rabi"
    else:                             return "Zaid"


def get_overall_risk(diseases: List[DiseaseRisk]) -> str:
    highs = sum(1 for d in diseases if d.risk_level == "HIGH")
    if highs >= 3: return "CRITICAL"
    if highs >= 2: return "HIGH"
    if highs == 1: return "MEDIUM"
    return "LOW"


def build_weather_advisory(temp: float, rain: float, season: str) -> str:
    parts = []
    if temp > 40:
        parts.append(f"EXTREME HEAT ({temp}°C): Risk of flower drop and fruit cracking. Use shade nets, irrigate in evening.")
    elif temp > 36:
        parts.append(f"HIGH TEMP ({temp}°C): Avoid afternoon irrigation. Monitor for heat stress wilting.")
    elif temp < 8:
        parts.append(f"COLD STRESS ({temp}°C): Cover sensitive crops at night. Risk of frost damage to flowers.")
    elif 22 <= temp <= 32:
        parts.append(f"Temperature {temp}°C is optimal for most crops.")
    else:
        parts.append(f"Temperature {temp}°C — within acceptable range.")

    if rain > 250:
        parts.append(f"HEAVY RAIN ({rain} mm): HIGH fungal risk. Spray preventive fungicide within 24 hours.")
    elif rain > 120:
        parts.append(f"HIGH RAIN ({rain} mm): Monitor for fungal diseases. Check drainage channels.")
    elif rain < 15 and season == "Kharif":
        parts.append(f"LOW RAINFALL ({rain} mm) during monsoon: Supplement with irrigation at critical stages.")
    else:
        parts.append(f"Rainfall {rain} mm — within normal range for the season.")

    return " | ".join(parts)


def get_tips(season: str, overall_risk: str, commodity: str) -> List[str]:
    tips = [
        f"Season: {season} — follow the recommended spray calendar for this season.",
        "Always use certified disease-free seeds from government-approved nurseries.",
        "Practice crop rotation — avoid planting the same crop consecutively.",
        "Keep a field diary: record spray dates, products used, and weather conditions.",
    ]
    if overall_risk in ["HIGH", "CRITICAL"]:
        tips.append("Start PREVENTIVE spraying NOW — do not wait for visible symptoms. By the time symptoms appear, 30–40% damage may already be done.")
        tips.append("Inform your local Krishi Vigyan Kendra (KVK) if you see widespread infection — it may be a notifiable outbreak.")
    if season == "Kharif":
        tips.append("Monsoon tip: Clear drainage channels before heavy rain. Waterlogging for 24 hours can cause root rot.")
    elif season == "Rabi":
        tips.append("Winter tip: Protect seedlings from frost with mulching. Frost below 2°C can kill flowers and reduce yield by 50%.")
    elif season == "Zaid":
        tips.append("Summer tip: Use drip irrigation. Apply straw mulch to keep soil cool and reduce water evaporation.")
    return tips


# ═══════════════════════════════════════════════════════════════
# ENDPOINTS
# ═══════════════════════════════════════════════════════════════

@router.post("/crop-health", response_model=CropHealthResponse,
             summary="Crop health check & real-time disease risk advisory")
def crop_health_check(body: CropHealthRequest):
    """
    Returns crop health advisory using real-time weather data.

    - Weather (temp + rainfall) is **automatically fetched** from Open-Meteo API
      using the farmer's state — user does NOT need to provide weather manually.
    - If user provides weather values, those are used instead (user_provided).
    - If API fails, seasonal averages are used as fallback.
    - `weather_source` in response tells you: 'live' / 'user_provided' / 'fallback_...'
    """
    month     = body.month if body.month is not None else datetime.today().month
    season    = get_season(month)
    commodity = body.commodity.strip().title()

    # ── Real-time weather resolution ──────────────────────────
    if body.current_temp is not None and body.rainfall_mm is not None:
        # User explicitly provided both — trust them
        temp   = body.current_temp
        rain   = body.rainfall_mm
        w_src  = "user_provided"
    else:
        # Auto-fetch from Open-Meteo using state coordinates
        fetched_temp, fetched_rain, w_src = fetch_weather(body.state, season)
        temp = body.current_temp if body.current_temp is not None else fetched_temp
        rain = body.rainfall_mm  if body.rainfall_mm  is not None else fetched_rain

    # ── Disease lookup ────────────────────────────────────────
    crop_data = DISEASE_CALENDAR.get(commodity, {})
    diseases  = crop_data.get(season) or [
        DiseaseRisk(
            disease     = "General Crop Monitoring",
            risk_level  = "LOW",
            description = f"No specific disease calendar for {commodity} in {season}. General monitoring recommended.",
            prevention  = "Maintain good field hygiene. Ensure proper spacing. Use balanced NPK fertilization.",
        )
    ]

    overall_risk = get_overall_risk(diseases)
    plant_advice = PLANTING_ADVICE.get(commodity, {}).get(season, "CAUTION")
    weather_adv  = build_weather_advisory(temp, rain, season)
    price_impact = PRICE_IMPACT_BY_RISK.get(overall_risk, PRICE_IMPACT_BY_RISK["LOW"])
    tips         = get_tips(season, overall_risk, commodity)

    return CropHealthResponse(
        commodity         = body.commodity,
        state             = body.state,
        month             = month,
        season            = season,
        overall_risk      = overall_risk,
        plant_advice      = plant_advice,
        diseases_to_watch = diseases,
        weather_advisory  = weather_adv,
        weather_source    = w_src,
        current_temp      = temp,
        rainfall_mm       = rain,
        price_impact      = price_impact,
        tips              = tips,
    )


@router.get("/crop-health/crops", summary="List crops with full disease advisory data")
def health_supported_crops():
    return {
        "crops_with_full_data": sorted(DISEASE_CALENDAR.keys()),
        "total":                len(DISEASE_CALENDAR),
        "note": "Crops not listed still receive a general advisory.",
    }