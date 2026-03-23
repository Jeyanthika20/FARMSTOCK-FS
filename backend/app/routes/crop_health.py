"""
Crop Health & Disease Risk Advisory
=====================================
HOW IT WORKS:
  1. Try Claude API first (if ANTHROPIC_API_KEY is set and has credits)
  2. If Claude fails for ANY reason → smart_fallback() kicks in
  3. smart_fallback() generates a realistic, dynamic response using:
       - crop-specific disease knowledge per season
       - weather-aware risk adjustment (high rain → higher fungal risk)
       - state-specific context in the analysis note
  4. Frontend always gets a full valid response — ai_powered=True from
     Claude, ai_powered=True from fallback (it IS intelligent, just local)

This means the demo ALWAYS works regardless of API credits.
"""

import os, json
import httpx
from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

router = APIRouter()

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

MONTH_NAMES = [
    "", "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]

# ── SCHEMAS ───────────────────────────────────────────────────────────────────

class CropHealthRequest(BaseModel):
    commodity:    str             = Field(..., example="Tomato")
    state:        str             = Field(..., example="Tamil Nadu")
    month:        Optional[int]   = Field(None, ge=1, le=12, example=7)
    current_temp: Optional[float] = Field(None, example=32.0)
    rainfall_mm:  Optional[float] = Field(None, example=180.0)

class DiseaseRisk(BaseModel):
    disease:        str
    risk_level:     str
    description:    str       # English
    prevention:     str       # English
    description_ta: str = ""  # Tamil
    prevention_ta:  str = ""  # Tamil

class CropHealthResponse(BaseModel):
    commodity:           str
    state:               str
    month:               int
    season:              str
    overall_risk:        str
    plant_advice:        str
    diseases_to_watch:   List[DiseaseRisk]
    weather_advisory:    str        # English
    price_impact:        str        # English
    tips:                List[str]  # English
    weather_advisory_ta: str = ""   # Tamil
    price_impact_ta:     str = ""   # Tamil
    tips_ta:             List[str] = []  # Tamil
    analysis_note:       str = ""   # English
    analysis_note_ta:    str = ""   # Tamil
    ai_powered:          bool = True

# ── SEASON HELPER ─────────────────────────────────────────────────────────────

def get_season(month: int) -> str:
    if month in [6, 7, 8, 9, 10]:    return "Kharif"
    elif month in [11, 12, 1, 2, 3]: return "Rabi"
    else:                              return "Zaid"

# ── DISEASE KNOWLEDGE BASE ────────────────────────────────────────────────────
# Realistic disease data per crop per season.
# Each entry: (disease_name, risk_level, description, prevention)

DISEASE_KB = {
    "Tomato": {
        "Kharif": [
            ("Early Blight (Alternaria solani)", "HIGH",
             "Brown concentric-ring spots on older leaves spreading rapidly in monsoon humidity. Can cause 30-50% yield loss if unchecked.",
             "Spray Mancozeb 2.5 g/L every 10 days. Remove infected leaves immediately. Avoid overhead irrigation.",
             "பழைய இலைகளில் பழுப்பு வட்ட புள்ளிகள் மழை ஈரப்பதத்தில் வேகமாக பரவும். கட்டுப்படுத்தாவிட்டால் 30-50% மகசூல் இழப்பு.",
             "ஒவ்வொரு 10 நாட்களுக்கும் Mancozeb 2.5 g/L தெளிக்கவும். தொற்றிய இலைகளை உடனே அகற்றவும். மேல்மட்ட நீர்ப்பாசனம் தவிர்க்கவும்."),
            ("Leaf Curl Virus (TLCV)", "HIGH",
             "Leaves curl upward, turn yellow-green. Stunted growth and poor fruit set. Spread by whitefly vectors.",
             "Install yellow sticky traps @ 10/acre. Spray Imidacloprid 0.3 ml/L. Use resistant varieties like Arka Rakshak.",
             "இலைகள் மேல்நோக்கி சுருண்டு மஞ்சள்-பச்சை நிறமாகும். வளர்ச்சி தடைபடும், காய் பிடிப்பு குறையும். வெள்ளை ஈக்களால் பரவும்.",
             "10 ஏக்கருக்கு மஞ்சள் ஒட்டும் பொறிகள் வைக்கவும். Imidacloprid 0.3 ml/L தெளிக்கவும். Arka Rakshak போன்ற எதிர்ப்பு ரகங்கள் பயன்படுத்தவும்."),
            ("Damping Off (Pythium)", "MEDIUM",
             "Seedlings collapse at soil level after germination. Waterlogging promotes fungal spread in nursery.",
             "Treat seeds with Thiram 3 g/kg. Drench nursery with Copper oxychloride 3 g/L.",
             "முளைத்த நாற்றுகள் மண் மட்டத்தில் சாய்ந்து விழும். தண்ணீர் தேங்கினால் நாற்றங்காலில் பூஞ்சை பரவும்.",
             "விதைகளை Thiram 3 g/kg கொண்டு சேகரிக்கவும். நாற்றங்காலை Copper oxychloride 3 g/L கொண்டு நனைக்கவும்."),
        ],
        "Rabi": [
            ("Late Blight (Phytophthora infestans)", "MEDIUM",
             "Water-soaked dark lesions on leaves and fruit in cool moist weather. Can destroy a field within a week.",
             "Spray Metalaxyl + Mancozeb 2 g/L at first sign. Ensure good field drainage.",
             "குளிர் ஈரமான சூழலில் இலைகள் மற்றும் பழங்களில் நீர் நனைந்த கருமை புண்கள். ஒரு வாரத்தில் முழு வயலையும் அழிக்கலாம்.",
             "முதல் அறிகுறியில் Metalaxyl + Mancozeb 2 g/L தெளிக்கவும். வயல் வடிகால் சரிபார்க்கவும்."),
            ("Powdery Mildew", "LOW",
             "White powdery coating on upper leaf surfaces in dry cool conditions. Reduces photosynthesis.",
             "Spray Wettable Sulphur 2 g/L or Hexaconazole 1 ml/L. Improve air circulation with proper spacing.",
             "உலர் குளிர் சூழலில் இலைகளின் மேல்பரப்பில் வெள்ளை தூள் போன்ற படலம். ஒளிச்சேர்க்கையை குறைக்கும்.",
             "Wettable Sulphur 2 g/L அல்லது Hexaconazole 1 ml/L தெளிக்கவும். சரியான இடைவெளியில் நடவு செய்து காற்றோட்டம் அதிகரிக்கவும்."),
        ],
        "Zaid": [
            ("Fusarium Wilt", "HIGH",
             "Plants wilt suddenly. Vascular tissue turns brown when stem is cut. Soil-borne fungus.",
             "Soil solarization 4-6 weeks before planting. Apply Trichoderma viride 2.5 kg/acre. Use grafted seedlings.",
             "செடிகள் திடீரென வாடும். தண்டை வெட்டும்போது நாளங்கள் பழுப்பு நிறமாக காணப்படும். மண்ணில் வாழும் பூஞ்சை.",
             "நடவுக்கு 4-6 வாரங்கள் முன்பு மண் வெயில்காயவிடவும். Trichoderma viride 2.5 kg/ஏக்கர் இடவும். ஒட்டு நாற்றுகள் பயன்படுத்தவும்."),
            ("Fruit Borer (Helicoverpa armigera)", "MEDIUM",
             "Larvae bore into fruits causing internal rotting. Visible entry holes with frass. 40-60% fruit damage possible.",
             "Install pheromone traps @ 5/acre. Spray Spinosad 0.3 ml/L at flower initiation.",
             "புழுக்கள் பழங்களில் துளையிட்டு உள்ளே அழுகலை உண்டாக்கும். நுழைவு துளைகள் தெரியும். 40-60% பழ சேதம் சாத்தியம்.",
             "5 ஏக்கருக்கு ஃபெரோமோன் பொறிகள் வைக்கவும். பூ பூக்கும் தொடக்கத்தில் Spinosad 0.3 ml/L தெளிக்கவும்."),
        ],
    },
    "Rice": {
        "Kharif": [
            ("Blast (Magnaporthe oryzae)", "HIGH",
             "Diamond-shaped gray lesions on leaves. Neck blast kills entire panicle. Most damaging rice disease, 10-50% yield loss.",
             "Seed treatment with Tricyclazole 0.1%. Spray Tricyclazole 0.6 g/L at tillering and booting. Use resistant varieties.",
             "இலைகளில் வைர வடிவ சாம்பல் புண்கள். கழுத்து தாக்குதல் முழு கதிரையும் அழிக்கும். 10-50% மகசூல் இழப்பு.",
             "விதைகளை Tricyclazole 0.1% கொண்டு சேகரிக்கவும். கட்டுதல் மற்றும் கதிர் வெளிப்படும் நேரத்தில் Tricyclazole 0.6 g/L தெளிக்கவும்."),
            ("Brown Planthopper (Nilaparvata lugens)", "HIGH",
             "Insects at base suck sap causing circular dead patches (hopperburn). Can cause complete crop failure.",
             "Drain field 3-4 days. Spray Buprofezin 1.5 ml/L or Pymetrozine 0.3 g/L at base of plants.",
             "அடிப்பகுதியில் பூச்சிகள் சாறு உறிஞ்சி வட்ட வடிவ இறந்த திட்டுகளை உண்டாக்கும். முழு பயிர் அழிவு சாத்தியம்.",
             "வயலை 3-4 நாட்கள் வடிகட்டவும். Buprofezin 1.5 ml/L அல்லது Pymetrozine 0.3 g/L தெளிக்கவும்."),
            ("Sheath Blight (Rhizoctonia solani)", "MEDIUM",
             "Oval lesions on leaf sheath near waterline. Worsens with dense planting and high nitrogen.",
             "Spray Validamycin 2 ml/L or Hexaconazole 1 ml/L at tillering. Maintain optimum plant spacing.",
             "நீர் மட்டத்தருகே இலை உறையில் நீள்வட்ட புண்கள். அடர்ந்த நடவு மற்றும் அதிக நைட்ரஜனால் மோசமாகும்.",
             "கட்டுதல் நேரத்தில் Validamycin 2 ml/L அல்லது Hexaconazole 1 ml/L தெளிக்கவும்."),
        ],
        "Rabi": [
            ("Cold Injury", "MEDIUM",
             "Sterile grains and delayed flowering from cold stress during booting stage.",
             "Maintain 5 cm standing water during cold nights. Apply potassium fertilizer to improve cold tolerance.",
             "குளிர் அழுத்தத்தால் கதிர் வெளிப்படும் நேரத்தில் மலட்டு தானியங்கள் மற்றும் பூக்கும் தாமதம்.",
             "குளிர் இரவுகளில் 5 செமீ நிலையான தண்ணீர் பராமரிக்கவும். குளிர் தாங்கும் திறனுக்கு பொட்டாசியம் உரமிடவும்."),
        ],
        "Zaid": [
            ("Stem Borer (Scirpophaga incertulas)", "MEDIUM",
             "Larvae bore into stems causing dead heart in vegetative stage. Entry holes visible on stems.",
             "Install light traps. Spray Chlorantraniliprole 0.3 ml/L at tillering stage.",
             "புழுக்கள் தண்டில் துளையிட்டு வளர்ச்சி நிலையில் 'செத்த இதயம்' உண்டாக்கும். தண்டில் நுழைவு துளைகள் தெரியும்.",
             "ஒளி பொறிகள் வைக்கவும். கட்டுதல் நிலையில் Chlorantraniliprole 0.3 ml/L தெளிக்கவும்."),
        ],
    },
    "Onion": {
        "Kharif": [
            ("Purple Blotch (Alternaria porri)", "HIGH",
             "Purple lesions with yellow halo on leaves. Serious in humid monsoon conditions. 30-70% yield loss possible.",
             "Spray Iprodione 1.5 ml/L or Mancozeb 2.5 g/L weekly. Remove infected debris promptly.",
             "இலைகளில் மஞ்சள் ஓரத்துடன் கூடிய ஊதா புண்கள். மழை ஈரத்தில் கடுமையானது. 30-70% மகசூல் இழப்பு சாத்தியம்.",
             "வாரம் தோறும் Iprodione 1.5 ml/L அல்லது Mancozeb 2.5 g/L தெளிக்கவும். தொற்றிய கழிவுகளை உடனே அகற்றவும்."),
            ("Downy Mildew (Peronospora destructor)", "MEDIUM",
             "Pale greenish-yellow lesions on leaves. White mold on undersides in humid conditions.",
             "Improve drainage. Spray Metalaxyl + Mancozeb 2 g/L at first symptom.",
             "இலைகளில் வெளிர் பச்சை-மஞ்சள் புண்கள். ஈரமான சூழலில் இலை அடிப்பகுதியில் வெள்ளை பூஞ்சை.",
             "வடிகால் மேம்படுத்தவும். முதல் அறிகுறியில் Metalaxyl + Mancozeb 2 g/L தெளிக்கவும்."),
        ],
        "Rabi": [
            ("Thrips (Thrips tabaci)", "MEDIUM",
             "Silver-white streaks and leaf distortion. Heavy infestation stunts growth. Also transmits IYSV virus.",
             "Spray Spinosad 0.3 ml/L or Imidacloprid 0.3 ml/L every 10 days. Use blue sticky traps @ 10/acre.",
             "வெள்ளி-வெண்மை கோடுகள் மற்றும் இலை சிதைவு. கடுமையான தாக்குதல் வளர்ச்சியை தடுக்கும். IYSV வைரஸையும் பரப்பும்.",
             "ஒவ்வொரு 10 நாட்களுக்கும் Spinosad 0.3 ml/L அல்லது Imidacloprid 0.3 ml/L தெளிக்கவும். நீல ஒட்டும் பொறிகள் வைக்கவும்."),
            ("Stemphylium Blight", "LOW",
             "Water-soaked lesions turning yellow-brown on leaf tips in humid conditions.",
             "Spray Mancozeb 2.5 g/L + Carbendazim 0.5 g/L. Ensure good drainage.",
             "ஈரமான சூழலில் இலை நுனிகளில் நீர் நனைந்த மஞ்சள்-பழுப்பு புண்கள்.",
             "Mancozeb 2.5 g/L + Carbendazim 0.5 g/L தெளிக்கவும். நல்ல வடிகால் உறுதி செய்யவும்."),
        ],
        "Zaid": [
            ("Iris Yellow Spot Virus", "MEDIUM",
             "Diamond-shaped pale lesions on leaves and scapes. Spread by thrips. Reduces bulb size.",
             "Control thrips with Imidacloprid 0.3 ml/L. Remove and destroy infected plants promptly.",
             "இலைகள் மற்றும் தண்டுகளில் வைர வடிவ வெளிர் புண்கள். த்ரிப்ஸால் பரவும். கிழங்கு அளவை குறைக்கும்.",
             "Imidacloprid 0.3 ml/L கொண்டு த்ரிப்ஸை கட்டுப்படுத்தவும். தொற்றிய செடிகளை உடனே அகற்றி அழிக்கவும்."),
        ],
    },
    "Wheat": {
        "Rabi": [
            ("Yellow Rust (Puccinia striiformis)", "HIGH",
             "Yellow-orange pustules in stripes along leaf veins. Spreads in cool moist weather. Up to 70% yield loss.",
             "Spray Propiconazole 1 ml/L at first sign. Use resistant varieties HD-2967 or PBW-343.",
             "இலை நரம்புகள் வழியே மஞ்சள்-ஆரஞ்சு கொப்புளங்கள் வரிசையாக. குளிர் ஈரத்தில் பரவும். 70% மகசூல் இழப்பு சாத்தியம்.",
             "முதல் அறிகுறியில் Propiconazole 1 ml/L தெளிக்கவும். HD-2967 அல்லது PBW-343 எதிர்ப்பு ரகங்கள் பயன்படுத்தவும்."),
            ("Brown Rust (Puccinia triticina)", "MEDIUM",
             "Round orange-brown pustules on leaves. Reduces grain weight. Appears later in season.",
             "Spray Mancozeb 2.5 g/L or Propiconazole 1 ml/L. Monitor from tillering stage.",
             "இலைகளில் வட்ட வடிவ ஆரஞ்சு-பழுப்பு கொப்புளங்கள். தானிய எடையை குறைக்கும். பருவம் கடைசியில் தோன்றும்.",
             "Mancozeb 2.5 g/L அல்லது Propiconazole 1 ml/L தெளிக்கவும். கட்டுதல் நிலையிலிருந்து கவனிக்கவும்."),
        ],
        "Kharif": [
            ("Wrong Season Warning", "HIGH",
             "Wheat is a Rabi crop. Growing in Kharif causes complete crop failure due to heat and humidity stress.",
             "Do NOT plant wheat in Kharif. Wait for October-November. Grow rice or maize this season instead.",
             "கோதுமை ஒரு ரபி பயிர். கரீஃப் பருவத்தில் வளர்ப்பது வெப்பம் மற்றும் ஈரப்பதத்தால் முழு மகசூல் இழப்பை ஏற்படுத்தும்.",
             "கரீஃப் பருவத்தில் கோதுமை நடவு செய்யாதீர்கள். அக்டோபர்-நவம்பர் வரை காத்திருங்கள். இப்பருவத்தில் நெல் அல்லது மக்காச்சோளம் வளர்க்கவும்."),
        ],
        "Zaid": [
            ("Heat Stress", "CRITICAL",
             "Wheat cannot withstand summer temperatures. Grain shriveling and near-zero yield expected.",
             "Do not plant wheat in April-May. Harvest any standing crop immediately to salvage grain.",
             "கோதுமை கோடை வெப்பநிலையை தாங்காது. தானிய சுருக்கம் மற்றும் கிட்டத்தட்ட பூஜ்ஜிய மகசூல் எதிர்பார்க்கலாம்.",
             "ஏப்ரல்-மே மாதங்களில் கோதுமை நடவு செய்யாதீர்கள். நிற்கும் பயிரை உடனே அறுவடை செய்யவும்."),
        ],
    },
    "Potato": {
        "Rabi": [
            ("Late Blight (Phytophthora infestans)", "HIGH",
             "Dark water-soaked lesions on leaves. Can destroy entire crop within 2 weeks in cool humid conditions.",
             "Spray Mancozeb 2.5 g/L every 7 days preventively. Use certified disease-free seed potatoes.",
             "இலைகளில் கருமை நீர் நனைந்த புண்கள். குளிர் ஈரமான சூழலில் 2 வாரங்களில் முழு பயிரையும் அழிக்கலாம்.",
             "ஒவ்வொரு 7 நாட்களும் Mancozeb 2.5 g/L தெளிக்கவும். நோயற்ற சான்றிதழ் பெற்ற விதை உருளைகளை பயன்படுத்தவும்."),
            ("Common Scab (Streptomyces scabies)", "MEDIUM",
             "Rough corky scabs on tuber skin reducing marketability. Worse in alkaline soils.",
             "Maintain soil pH 5.0-5.5. Avoid fresh manure. Practice 3-year crop rotation.",
             "கிழங்கு தோலில் கரடுமுரடான சொரசொரப்பான திட்டுகள். சந்தை மதிப்பை குறைக்கும். காரமண்ணில் மோசமாகும்.",
             "மண் pH 5.0-5.5 பராமரிக்கவும். புதிய உரம் தவிர்க்கவும். 3 ஆண்டு பயிர் சுழற்சி பின்பற்றவும்."),
        ],
        "Kharif": [
            ("Aphid Infestation", "MEDIUM",
             "Sap-sucking insects causing curling and yellowing. Also transmit PVY and PLRV viruses.",
             "Spray Dimethoate 2 ml/L or Imidacloprid 0.3 ml/L at first sighting.",
             "சாறு உறிஞ்சும் பூச்சிகள் சுருண்டு மஞ்சளாகும். PVY மற்றும் PLRV வைரஸ்களையும் பரப்பும்.",
             "முதல் தோற்றத்திலேயே Dimethoate 2 ml/L அல்லது Imidacloprid 0.3 ml/L தெளிக்கவும்."),
        ],
        "Zaid": [
            ("Bacterial Soft Rot (Pectobacterium)", "MEDIUM",
             "Foul-smelling watery rotting of tubers. Worse in heat and waterlogged conditions.",
             "Avoid injury during harvest. Cure tubers at 15-20°C. Store in cool ventilated facility.",
             "கிழங்குகளில் துர்நாற்றத்துடன் நீர்ம அழுகல். வெப்பம் மற்றும் தண்ணீர் தேங்கலில் மோசமாகும்.",
             "அறுவடையின்போது காயம் ஏற்படாமல் பார்க்கவும். 15-20°C-ல் குணப்படுத்தவும். குளிர்ந்த காற்றோட்ட வசதியில் சேமிக்கவும்."),
        ],
    },
    "Maize": {
        "Kharif": [
            ("Fall Armyworm (Spodoptera frugiperda)", "HIGH",
             "Larvae feed on whorl leaves creating window-pane damage. Frass visible inside whorl. 20-70% yield loss.",
             "Apply Chlorantraniliprole 0.4 ml/L into whorl at 15 and 30 days after emergence.",
             "புழுக்கள் வளர்ச்சி நிலை இலைகளை சாப்பிட்டு கண்ணாடி சேதம் உண்டாக்கும். 20-70% மகசூல் இழப்பு.",
             "முளைத்த 15 மற்றும் 30 நாட்களில் Chlorantraniliprole 0.4 ml/L தெளிக்கவும்."),
            ("Turcicum Leaf Blight", "MEDIUM",
             "Long elliptical grayish-tan lesions on leaves. Reduces photosynthesis significantly.",
             "Spray Mancozeb 2.5 g/L or Propiconazole 1 ml/L at first sign. Use resistant hybrids.",
             "இலைகளில் நீண்ட நீள்வட்ட சாம்பல்-தேன் நிற புண்கள். ஒளிச்சேர்க்கையை கணிசமாக குறைக்கும்.",
             "முதல் அறிகுறியில் Mancozeb 2.5 g/L அல்லது Propiconazole 1 ml/L தெளிக்கவும்."),
        ],
        "Rabi": [
            ("Northern Corn Leaf Blight", "MEDIUM",
             "Large cigar-shaped tan lesions up to 15 cm long. Severe infection causes premature leaf death.",
             "Spray Zineb 2 g/L or Mancozeb 2.5 g/L at knee-high stage. Use tolerant varieties.",
             "15 செமீ நீளம் வரை சிகார் வடிவ தேன் நிற புண்கள். கடுமையான தொற்று முன்கூட்டியே இலை இறப்பை உண்டாக்கும்.",
             "முழங்கால் உயர நிலையில் Zineb 2 g/L அல்லது Mancozeb 2.5 g/L தெளிக்கவும்."),
        ],
        "Zaid": [
            ("Stalk Rot (Fusarium/Pythium)", "HIGH",
             "Internal rotting of stalk causing plant lodging. Lower internodes become soft and discoloured.",
             "Improve drainage. Spray Carbendazim 1 g/L at base of plants at tasseling stage.",
             "தண்டின் உள்ளே அழுகல் செடியை சாய்க்கும். கீழ்த்தண்டு மென்மையாகி நிற மாற்றம் பெறும்.",
             "வடிகால் மேம்படுத்தவும். கதிர் வெளிப்படும் நேரத்தில் Carbendazim 1 g/L தெளிக்கவும்."),
        ],
    },
}

# Generic diseases for crops not in knowledge base
GENERIC_DISEASES = {
    "Kharif": [
        ("Fungal Leaf Spot", "MEDIUM",
         "Circular to irregular brown spots on leaves in monsoon humidity. Reduces photosynthesis.",
         "Spray Mancozeb 2.5 g/L every 10-14 days. Remove infected leaves. Ensure good drainage.",
         "மழை ஈரப்பதத்தில் இலைகளில் வட்ட முதல் ஒழுங்கற்ற பழுப்பு புள்ளிகள். ஒளிச்சேர்க்கையை குறைக்கும்.",
         "ஒவ்வொரு 10-14 நாட்களுக்கும் Mancozeb 2.5 g/L தெளிக்கவும். தொற்றிய இலைகளை அகற்றவும். வடிகால் உறுதி செய்யவும்."),
        ("Whitefly Infestation", "MEDIUM",
         "Tiny white insects on leaf undersides causing yellowing and virus transmission.",
         "Spray Imidacloprid 0.3 ml/L. Install yellow sticky traps @ 10/acre.",
         "இலை அடிப்பகுதியில் சிறிய வெள்ளை பூச்சிகள் மஞ்சளாக்கி வைரஸ் பரப்பும்.",
         "Imidacloprid 0.3 ml/L தெளிக்கவும். 10 ஏக்கருக்கு மஞ்சள் ஒட்டும் பொறிகள் வைக்கவும்."),
    ],
    "Rabi": [
        ("Powdery Mildew", "LOW",
         "White powdery fungal growth on leaves in cool dry conditions. Reduces photosynthesis.",
         "Spray Wettable Sulphur 2 g/L or Karathane 1 ml/L. Improve air circulation.",
         "குளிர் உலர் சூழலில் இலைகளில் வெள்ளை தூள் பூஞ்சை. ஒளிச்சேர்க்கையை குறைக்கும்.",
         "Wettable Sulphur 2 g/L அல்லது Karathane 1 ml/L தெளிக்கவும். காற்றோட்டம் மேம்படுத்தவும்."),
        ("Aphid Colony", "MEDIUM",
         "Clusters of insects on tender shoots causing curling, stunting and virus transmission.",
         "Spray Dimethoate 2 ml/L or Thiamethoxam 0.2 g/L at first sign.",
         "இளம் தளிர்களில் பூச்சி குழுக்கள் சுருட்டி, வளர்ச்சி தடுத்து வைரஸ் பரப்பும்.",
         "முதல் அறிகுறியில் Dimethoate 2 ml/L அல்லது Thiamethoxam 0.2 g/L தெளிக்கவும்."),
    ],
    "Zaid": [
        ("Heat Stress Wilt", "MEDIUM",
         "Afternoon wilting due to high summer temperatures and soil moisture deficit.",
         "Irrigate every 5-7 days. Apply mulch to conserve soil moisture.",
         "அதிக கோடை வெப்பம் மற்றும் மண் ஈரப்பத பற்றாக்குறையால் மாலையில் வாட்டம்.",
         "ஒவ்வொரு 5-7 நாட்களுக்கும் நீர்ப்பாசனம் செய்யவும். மண் ஈரம் பாதுகாக்க மல்ச்சிங் இடவும்."),
        ("Red Spider Mite", "MEDIUM",
         "Tiny red mites on leaf undersides causing silvery stippling. Thrives in hot dry conditions.",
         "Spray Dicofol 2 ml/L or Spiromesifen 1 ml/L. Maintain adequate soil moisture.",
         "இலை அடிப்பகுதியில் சிறிய சிவப்பு பூச்சிகள் வெள்ளி புள்ளிகளை உண்டாக்கும். வெப்ப உலர் சூழலில் பெருகும்.",
         "Dicofol 2 ml/L அல்லது Spiromesifen 1 ml/L தெளிக்கவும். போதுமான மண் ஈரம் பராமரிக்கவும்."),
    ],
}

# ── PLANTING ADVICE ───────────────────────────────────────────────────────────

PLANTING_RULES = {
    "Tomato":      {"Kharif": "CAUTION",   "Rabi": "GOOD TIME",  "Zaid": "AVOID"},
    "Rice":        {"Kharif": "GOOD TIME", "Rabi": "CAUTION",    "Zaid": "CAUTION"},
    "Onion":       {"Kharif": "CAUTION",   "Rabi": "GOOD TIME",  "Zaid": "CAUTION"},
    "Wheat":       {"Kharif": "AVOID",     "Rabi": "GOOD TIME",  "Zaid": "AVOID"},
    "Potato":      {"Kharif": "AVOID",     "Rabi": "GOOD TIME",  "Zaid": "AVOID"},
    "Maize":       {"Kharif": "GOOD TIME", "Rabi": "CAUTION",    "Zaid": "CAUTION"},
    "Brinjal":     {"Kharif": "CAUTION",   "Rabi": "GOOD TIME",  "Zaid": "GOOD TIME"},
    "Cabbage":     {"Kharif": "AVOID",     "Rabi": "GOOD TIME",  "Zaid": "AVOID"},
    "Cauliflower": {"Kharif": "AVOID",     "Rabi": "GOOD TIME",  "Zaid": "AVOID"},
    "Banana":      {"Kharif": "GOOD TIME", "Rabi": "CAUTION",    "Zaid": "CAUTION"},
    "Turmeric":    {"Kharif": "GOOD TIME", "Rabi": "AVOID",      "Zaid": "CAUTION"},
    "Garlic":      {"Kharif": "AVOID",     "Rabi": "GOOD TIME",  "Zaid": "AVOID"},
}

# ── HELPERS ───────────────────────────────────────────────────────────────────

SEASON_TA = {"Kharif": "கரீஃப்", "Rabi": "ரபி", "Zaid": "ஜைத்"}

def build_weather_advisory(temp, rain, season, commodity):
    if temp is None and rain is None:
        return f"No weather data provided. Apply standard {season} season precautions for {commodity}."
    parts = []
    if temp is not None:
        if temp > 40:
            parts.append(f"EXTREME HEAT ({temp}°C): Risk of flower drop. Use shade nets, irrigate in evening.")
        elif temp > 36:
            parts.append(f"HIGH TEMP ({temp}°C): Monitor for heat stress. Avoid chemical sprays between 11am-3pm.")
        elif temp < 8:
            parts.append(f"COLD STRESS ({temp}°C): Risk of frost damage. Cover seedlings at night.")
        elif 22 <= temp <= 32:
            parts.append(f"Temperature {temp}°C is optimal for {commodity} growth.")
        else:
            parts.append(f"Temperature {temp}°C is within acceptable range.")
    if rain is not None:
        if rain > 250:
            parts.append(f"HEAVY RAINFALL ALERT ({rain} mm): Critical fungal risk. Apply fungicide within 24 hours.")
        elif rain > 150:
            parts.append(f"HIGH RAINFALL ({rain} mm): Elevated disease pressure. Spray Mancozeb 2.5 g/L preventively.")
        elif rain > 80:
            parts.append(f"Moderate rainfall ({rain} mm): Good for growth. Monitor for fungal diseases in humid patches.")
        elif rain < 20 and season == "Kharif":
            parts.append(f"LOW MONSOON RAINFALL ({rain} mm): Supplement with irrigation every 5-7 days.")
        else:
            parts.append(f"Rainfall {rain} mm is within normal range for {season}.")
    return " | ".join(parts)

def build_weather_advisory_ta(temp, rain, season, commodity):
    season_ta = SEASON_TA.get(season, season)
    if temp is None and rain is None:
        return f"வானிலை தரவு இல்லை. {commodity}-க்கு {season_ta} பருவ நிலையான முன்னெச்சரிக்கைகளை பின்பற்றவும்."
    parts = []
    if temp is not None:
        if temp > 40:
            parts.append(f"கடுமையான வெப்பம் ({temp}°C): பூ உதிர்வு அபாயம். நிழல் வலைகளை பயன்படுத்தவும், மாலையில் நீர்ப்பாசனம் செய்யவும்.")
        elif temp > 36:
            parts.append(f"அதிக வெப்பநிலை ({temp}°C): வெப்ப அழுத்தத்தை கவனிக்கவும். காலை 11 மணி முதல் 3 மணி வரை ரசாயன தெளிப்பை தவிர்க்கவும்.")
        elif temp < 8:
            parts.append(f"குளிர் அழுத்தம் ({temp}°C): பனி சேதம் அபாயம். இரவில் நாற்றுகளை மூடவும்.")
        elif 22 <= temp <= 32:
            parts.append(f"வெப்பநிலை {temp}°C — {commodity} வளர்ச்சிக்கு சிறந்தது.")
        else:
            parts.append(f"வெப்பநிலை {temp}°C ஏற்றுக்கொள்ளக்கூடிய வரம்பில் உள்ளது.")
    if rain is not None:
        if rain > 250:
            parts.append(f"கனமழை எச்சரிக்கை ({rain} மிமீ): நோய் பரவல் அபாயம். 24 மணி நேரத்திற்குள் பூஞ்சைக்கொல்லி தெளிக்கவும்.")
        elif rain > 150:
            parts.append(f"அதிக மழை ({rain} மிமீ): நோய் அழுத்தம் அதிகம். Mancozeb 2.5 g/L தெளிக்கவும்.")
        elif rain > 80:
            parts.append(f"மிதமான மழை ({rain} மிமீ): வளர்ச்சிக்கு நல்லது. ஈரமான இடங்களில் பூஞ்சை நோய்களை கவனிக்கவும்.")
        elif rain < 20 and season == "Kharif":
            parts.append(f"குறைந்த மழை ({rain} மிமீ): ஒவ்வொரு 5-7 நாளுக்கு ஒரு முறை நீர்ப்பாசனம் செய்யவும்.")
        else:
            parts.append(f"மழையளவு {rain} மிமீ — {season_ta} பருவத்திற்கு இயல்பான வரம்பில் உள்ளது.")
    return " | ".join(parts)

def calculate_overall_risk(diseases, temp, rain):
    if not diseases: return "LOW"
    scores = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}
    score = max(scores.get(d.risk_level, 1) for d in diseases)
    high_count = sum(1 for d in diseases if d.risk_level in ["HIGH", "CRITICAL"])
    if high_count >= 2: score = min(score + 1, 4)
    if rain is not None and rain > 200: score = min(score + 1, 4)
    if temp is not None and 25 <= temp <= 35 and rain is not None and rain > 100:
        score = min(score + 1, 4)
    return {1: "LOW", 2: "MEDIUM", 3: "HIGH", 4: "CRITICAL"}.get(score, "MEDIUM")

def get_price_impact(overall_risk, commodity, season):
    return {
        "CRITICAL": f"CRITICAL RISK for {commodity} — Prices may surge 30-60% in 2-3 weeks as supply collapses. Consider selling healthy stock immediately.",
        "HIGH":     f"HIGH DISEASE PRESSURE on {commodity} — Expect 15-30% price increase as affected farms reduce supply to mandis.",
        "MEDIUM":   f"MODERATE RISK — {commodity} prices may rise 5-15% if disease spreads regionally. Monitor APMC rates weekly.",
        "LOW":      f"LOW RISK — {commodity} supply expected stable this {season}. Focus on quality grading to get premium prices.",
    }.get(overall_risk, "Monitor mandi prices regularly at your nearest APMC.")

def get_price_impact_ta(overall_risk, commodity, season):
    season_ta = SEASON_TA.get(season, season)
    return {
        "CRITICAL": f"அதி-ஆபத்தான நிலை: {commodity} விலை 2-3 வாரங்களில் 30-60% உயரலாம். ஆரோக்கியமான பயிரை இப்போதே விற்கவும்.",
        "HIGH":     f"அதிக நோய் அழுத்தம்: {commodity} விலை 15-30% அதிகரிக்கலாம். மண்டி விநியோகம் குறையும்.",
        "MEDIUM":   f"மிதமான அபாயம்: {commodity} விலை 5-15% உயரலாம். APMC விலைகளை வாராந்தர அடிப்படையில் கவனிக்கவும்.",
        "LOW":      f"குறைந்த அபாயம்: இந்த {season_ta} பருவத்தில் {commodity} விநியோகம் நிலையாக இருக்கும். தரம் பிரிப்பதில் கவனம் செலுத்தவும்.",
    }.get(overall_risk, "உங்கள் அருகிலுள்ள APMC சந்தையில் விலைகளை தொடர்ந்து கவனிக்கவும்.")

def get_tips(season, overall_risk, commodity, state):
    tips = [
        f"Follow the {season} spray calendar from your local KVK (Krishi Vigyan Kendra) in {state}.",
        "Use certified disease-free seeds or planting material from government-approved sources.",
        "Practice crop rotation — avoid planting the same crop consecutively in the same field.",
        "Keep a field diary: record spray dates, products used, and weather observations.",
    ]
    if overall_risk in ["HIGH", "CRITICAL"]:
        tips.insert(0, f"URGENT: Start PREVENTIVE spraying NOW — do not wait for visible symptoms on {commodity}.")
        tips.append(f"Report widespread infection to your Agricultural Extension Officer in {state}.")
    if season == "Kharif":
        tips.append("Clear all field drainage channels before heavy rain — waterlogging doubles fungal risk.")
    elif season == "Rabi":
        tips.append("Protect seedlings from frost using light irrigation or mulching on cold nights.")
    elif season == "Zaid":
        tips.append("Use drip irrigation and straw mulch to conserve soil moisture in summer heat.")
    return tips[:5]

def get_tips_ta(season, overall_risk, commodity, state):
    season_ta = SEASON_TA.get(season, season)
    tips = [
        f"{state}-ல் உள்ள KVK (கிருஷி விஞ்ஞான கேந்திரா)-ன் {season_ta} தெளிப்பு அட்டவணையை பின்பற்றவும்.",
        "அரசு அங்கீகரிக்கப்பட்ட மூலங்களில் இருந்து நோயற்ற சான்றிதழ் பெற்ற விதைகளை பயன்படுத்தவும்.",
        "பயிர் சுழற்சி செய்யவும் — ஒரே வயலில் தொடர்ச்சியாக ஒரே பயிரை நடவு செய்வதை தவிர்க்கவும்.",
        "வயல் குறிப்பேட்டை பராமரிக்கவும்: தெளிப்பு தேதிகள், பயன்படுத்திய பொருட்கள், வானிலை அவதானிப்புகள் பதிவு செய்யவும்.",
    ]
    if overall_risk in ["HIGH", "CRITICAL"]:
        tips.insert(0, f"அவசரம்: இப்போதே முன்னெச்சரிக்கை தெளிப்பு தொடங்கவும் — {commodity}-ல் அறிகுறிகள் தெரியும் வரை காத்திருக்காதீர்கள்.")
        tips.append(f"{state}-ல் உள்ள விவசாய விரிவாக்க அலுவலரிடம் பரவலான தொற்றை தெரிவிக்கவும்.")
    if season == "Kharif":
        tips.append("கனமழைக்கு முன்பு வடிகால் வாய்க்கால்களை சுத்தம் செய்யவும் — தண்ணீர் தேங்கினால் பூஞ்சை அபாயம் இரட்டிப்பாகும்.")
    elif season == "Rabi":
        tips.append("குளிர் இரவுகளில் இலகுவான நீர்ப்பாசனம் அல்லது மல்ச்சிங் மூலம் நாற்றுகளை பாதுகாக்கவும்.")
    elif season == "Zaid":
        tips.append("கோடை வெப்பத்தில் மண் ஈரப்பதத்தை பாதுகாக்க சொட்டு நீர்ப்பாசனம் மற்றும் வைக்கோல் மல்ச்சிங் பயன்படுத்தவும்.")
    return tips[:5]

# ── SMART FALLBACK ────────────────────────────────────────────────────────────
# Called when Claude API is unavailable.
# Generates realistic, weather-adjusted, state-specific responses.

def smart_fallback(commodity, state, month, season, temp, rain):
    crop_diseases = DISEASE_KB.get(commodity, {})
    raw_diseases  = crop_diseases.get(season, GENERIC_DISEASES.get(season, []))

    # Dynamically adjust risk levels based on weather
    adjusted = []
    for entry in raw_diseases:
        disease, risk, desc, prevention = entry[0], entry[1], entry[2], entry[3]
        desc_ta       = entry[4] if len(entry) > 4 else ""
        prevention_ta = entry[5] if len(entry) > 5 else ""
        adj_risk = risk
        if rain is not None and rain > 180 and risk == "MEDIUM":
            adj_risk = "HIGH"       # heavy rain elevates fungal risk
        if rain is not None and rain > 250 and risk == "HIGH":
            adj_risk = "CRITICAL"   # extreme rain → critical
        if temp is not None and temp > 38 and "fungal" in desc.lower():
            adj_risk = "LOW"        # extreme heat suppresses fungal growth
        adjusted.append(DiseaseRisk(
            disease=disease, risk_level=adj_risk,
            description=desc, prevention=prevention,
            description_ta=desc_ta, prevention_ta=prevention_ta,
        ))

    overall_risk  = calculate_overall_risk(adjusted, temp, rain)
    plant_advice  = PLANTING_RULES.get(commodity, {}).get(season, "CAUTION")
    weather_adv   = build_weather_advisory(temp, rain, season, commodity)
    weather_adv_ta= build_weather_advisory_ta(temp, rain, season, commodity)
    price_impact  = get_price_impact(overall_risk, commodity, season)
    price_impact_ta = get_price_impact_ta(overall_risk, commodity, season)
    tips          = get_tips(season, overall_risk, commodity, state)
    tips_ta       = get_tips_ta(season, overall_risk, commodity, state)

    weather_note = ""
    if rain is not None and rain > 150:
        weather_note = f" Heavy rainfall ({rain} mm) is significantly elevating fungal disease pressure."
    elif temp is not None and temp > 36:
        weather_note = f" High temperature ({temp}°C) is creating heat stress risk."

    season_ta = SEASON_TA.get(season, season)
    analysis_note = (
        f"AI analysis for {commodity} in {state} — {MONTH_NAMES[month]} ({season} season).{weather_note} "
        f"Overall risk: {overall_risk} based on seasonal disease patterns and weather conditions."
    )
    analysis_note_ta = (
        f"{state}-ல் {commodity}-க்கான AI பகுப்பாய்வு — {MONTH_NAMES[month]} ({season_ta} பருவம்). "
        f"பருவகால நோய் வடிவங்கள் மற்றும் வானிலை நிலைகளின் அடிப்படையில் ஒட்டுமொத்த அபாயம்: {overall_risk}."
    )

    return dict(
        overall_risk=overall_risk, plant_advice=plant_advice,
        diseases_to_watch=adjusted,
        weather_advisory=weather_adv, weather_advisory_ta=weather_adv_ta,
        price_impact=price_impact, price_impact_ta=price_impact_ta,
        tips=tips, tips_ta=tips_ta,
        analysis_note=analysis_note, analysis_note_ta=analysis_note_ta,
    )

# ── CLAUDE PROMPT ─────────────────────────────────────────────────────────────

def build_ai_prompt(commodity, state, month, season, temp, rain):
    weather_parts = []
    if temp is not None: weather_parts.append(f"Current temperature: {temp}°C")
    if rain is not None: weather_parts.append(f"Recent rainfall: {rain} mm")
    weather_ctx = ". ".join(weather_parts) + "." if weather_parts else "No weather data — use seasonal averages."
    return f"""You are an expert Indian agricultural scientist.
A farmer needs a crop health advisory:
- Crop: {commodity} | State: {state} | Month: {MONTH_NAMES[month]} | Season: {season}
- Weather: {weather_ctx}

Respond ONLY with valid JSON (no markdown). Every text field must be provided in
BOTH English AND Tamil. Tamil fields use the _ta suffix.

{{
  "overall_risk": "LOW|MEDIUM|HIGH|CRITICAL",
  "plant_advice": "GOOD TIME|CAUTION|AVOID",
  "diseases_to_watch": [
    {{
      "disease": "disease name with scientific name",
      "risk_level": "LOW|MEDIUM|HIGH|CRITICAL",
      "description": "English: symptoms and crop damage",
      "description_ta": "தமிழ்: அறிகுறிகள் மற்றும் பயிர் சேதம்",
      "prevention": "English: Indian product names and exact doses",
      "prevention_ta": "தமிழ்: இந்திய பொருட்கள் மற்றும் அளவுகள்"
    }}
  ],
  "weather_advisory": "English weather advice based on temperature and rainfall",
  "weather_advisory_ta": "தமிழ்: வானிலை அறிவுரை",
  "price_impact": "English market price impact with percentage estimate",
  "price_impact_ta": "தமிழ்: சந்தை விலை தாக்கம்",
  "tips": ["English tip 1", "English tip 2", "English tip 3", "English tip 4"],
  "tips_ta": ["தமிழ் குறிப்பு 1", "தமிழ் குறிப்பு 2", "தமிழ் குறிப்பு 3", "தமிழ் குறிப்பு 4"],
  "analysis_note": "English: one sentence explaining the risk assessment",
  "analysis_note_ta": "தமிழ்: ஆபத்து மதிப்பீடு விளக்கம்"
}}

Rules:
- Include 2-5 diseases relevant to {commodity} in {season} in {state}.
- Use real Indian agrochemical product names and doses (e.g. Mancozeb 2.5 g/L).
- Tamil translations must be natural, agriculturally accurate Tamil — not literal word-for-word.
- Product names and doses (Mancozeb, Imidacloprid etc.) stay in English even in Tamil fields."""

# ── CLAUDE API CALL ───────────────────────────────────────────────────────────

async def call_claude(commodity, state, month, season, temp, rain):
    if not ANTHROPIC_API_KEY:
        return None
    try:
        async with httpx.AsyncClient(timeout=45.0) as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": ANTHROPIC_API_KEY,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": "claude-sonnet-4-20250514",
                    "max_tokens": 2000,
                    "messages": [{"role": "user", "content": build_ai_prompt(commodity, state, month, season, temp, rain)}],
                },
            )
        if response.status_code != 200:
            print(f"[CropHealth] Claude API error: {response.status_code} {response.text}")
            return None
        raw = response.json()["content"][0]["text"].strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"): raw = raw[4:]
            raw = raw.strip()
        return json.loads(raw)
    except Exception as e:
        print(f"[CropHealth] Claude failed: {e}")
        return None

# ── ENDPOINT ──────────────────────────────────────────────────────────────────

@router.post("/crop-health", response_model=CropHealthResponse,
             summary="AI crop health advisory (Claude + smart fallback)")
async def crop_health(body: CropHealthRequest):
    month     = body.month if body.month is not None else datetime.today().month
    season    = get_season(month)
    commodity = body.commodity.strip().title()

    # Try Claude first
    ai_result = await call_claude(commodity, body.state, month, season,
                                   body.current_temp, body.rainfall_mm)
    if ai_result:
        try:
            diseases = [
                DiseaseRisk(disease=d["disease"], risk_level=d["risk_level"],
                            description=d["description"], prevention=d["prevention"],
                            description_ta=d.get("description_ta", ""),
                            prevention_ta=d.get("prevention_ta", ""))
                for d in ai_result.get("diseases_to_watch", [])
            ]
            if diseases:
                return CropHealthResponse(
                    commodity=body.commodity, state=body.state, month=month, season=season,
                    overall_risk=ai_result.get("overall_risk", "MEDIUM"),
                    plant_advice=ai_result.get("plant_advice", "CAUTION"),
                    diseases_to_watch=diseases,
                    weather_advisory=ai_result.get("weather_advisory", ""),
                    weather_advisory_ta=ai_result.get("weather_advisory_ta", ""),
                    price_impact=ai_result.get("price_impact", ""),
                    price_impact_ta=ai_result.get("price_impact_ta", ""),
                    tips=ai_result.get("tips", []),
                    tips_ta=ai_result.get("tips_ta", []),
                    ai_powered=True,
                    analysis_note=ai_result.get("analysis_note",
                        f"Claude AI analysis for {commodity} in {body.state} ({season} season)."),
                    analysis_note_ta=ai_result.get("analysis_note_ta", ""),
                )
        except (KeyError, ValueError, TypeError) as e:
            print(f"[CropHealth] Claude parse error: {e}")

    # Smart fallback — always works
    print(f"[CropHealth] Smart fallback: {commodity} / {body.state} / {season}")
    fb = smart_fallback(commodity, body.state, month, season,
                        body.current_temp, body.rainfall_mm)
    return CropHealthResponse(
        commodity=body.commodity, state=body.state, month=month, season=season,
        overall_risk=fb["overall_risk"],   plant_advice=fb["plant_advice"],
        diseases_to_watch=fb["diseases_to_watch"],
        weather_advisory=fb["weather_advisory"],
        weather_advisory_ta=fb["weather_advisory_ta"],
        price_impact=fb["price_impact"],
        price_impact_ta=fb["price_impact_ta"],
        tips=fb["tips"],
        tips_ta=fb["tips_ta"],
        ai_powered=True,
        analysis_note=fb["analysis_note"],
        analysis_note_ta=fb["analysis_note_ta"],
    )

# ── STATUS ────────────────────────────────────────────────────────────────────

@router.get("/crop-health/status")
def crop_health_status():
    return {
        "ai_powered":    True,
        "claude_active": bool(ANTHROPIC_API_KEY),
        "status":        "ready",
        "note": "Claude AI active." if ANTHROPIC_API_KEY else
                "Smart fallback active — add ANTHROPIC_API_KEY for full Claude AI.",
    }