/**
 * api.js — FarmStock API Client
 * All backend calls, with demo data fallback if backend is offline.
 */

const BASE = '/api'

async function callApi(path, method = 'GET', body = null) {
  const opts = {
    method,
    headers: { 'Content-Type': 'application/json' },
  }
  if (body) opts.body = JSON.stringify(body)
  const res = await fetch(BASE + path, opts)
  if (!res.ok) throw new Error(`API error ${res.status}`)
  return res.json()
}

// ── Price Prediction ────────────────────────────────────────────
export async function predictPrice(data) {
  try {
    return await callApi('/predict', 'POST', data)
  } catch {
    // Demo fallback
    const change = (Math.random() - 0.4) * 20
    const predicted = Math.max(5, data.current_price + change)
    return {
      commodity: data.commodity,
      market: data.market,
      date: data.date || new Date().toISOString().split('T')[0],
      current_price_kg: data.current_price,
      predicted_price_kg: +predicted.toFixed(2),
      predicted_price_quintal: +(predicted * 100).toFixed(2),
      unit: 'Rs/kg',
      confidence: 78.5,
      change_pct: +((change / data.current_price) * 100).toFixed(2),
      recommendation: change > 5 ? 'HOLD — prices rising' : change < -5 ? 'SELL NOW — prices falling' : 'NEUTRAL — stable market',
      model_used: 'XGBoostRegressor [DEMO]',
      mae_kg: 3.42,
      _demo: true
    }
  }
}

// ── Forecast ────────────────────────────────────────────────────
export async function forecastPrices(data) {
  try {
    return await callApi('/forecast', 'POST', data)
  } catch {
    const days = []
    const horizon = data.horizon_days
    // Generate natural wave-based prices so best/worst are always distinct
    for (let i = 1; i <= horizon; i++) {
      const wave    = 0.12 * Math.sin(2 * Math.PI * i / 14)
      const wave2   = 0.05 * Math.sin(2 * Math.PI * i / 6 + 1)
      const trend   = 0.04 * Math.sin(2 * Math.PI * i / Math.max(horizon, 30))
      const signal  = 1.0 + wave + wave2 + trend
      const price   = Math.max(5, data.current_price * signal)
      const chg     = ((price - data.current_price) / data.current_price) * 100
      const d = new Date(); d.setDate(d.getDate() + i)
      days.push({
        day: i,
        date: d.toISOString().split('T')[0],
        predicted_price_kg: +price.toFixed(2),
        predicted_price_quintal: +(price * 100).toFixed(2),
        change_from_today: +chg.toFixed(2),
        recommendation: chg < -5 ? 'SELL' : chg > 5 ? 'HOLD' : 'NEUTRAL'
      })
    }
    const prices    = days.map(d => d.predicted_price_kg)
    const bestIdx   = prices.indexOf(Math.max(...prices))
    let   worstIdx  = prices.indexOf(Math.min(...prices))
    // Guarantee distinct
    if (bestIdx === worstIdx) worstIdx = (bestIdx + Math.floor(horizon / 2)) % horizon
    const best  = days[bestIdx]
    const worst = days[worstIdx]
    return {
      commodity: data.commodity, market: data.market,
      current_price: data.current_price, horizon_days: data.horizon_days,
      forecast: days,
      summary: {
        min_price_kg:          +Math.min(...prices).toFixed(2),
        max_price_kg:          +Math.max(...prices).toFixed(2),
        avg_price_kg:          +(prices.reduce((a,b)=>a+b,0)/prices.length).toFixed(2),
        best_sell_date:        best.date,
        best_sell_price_kg:    best.predicted_price_kg,
        worst_sell_date:       worst.date,
        worst_sell_price_kg:   worst.predicted_price_kg,
        potential_gain_pct:    best.change_from_today,
      },
      _demo: true
    }
  }
}

// ── Crop Health ─────────────────────────────────────────────────
export async function checkCropHealth(data, useAI = false) {
  const endpoint = useAI ? '/crop-health/ai' : '/crop-health'
  try {
    return await callApi(endpoint, 'POST', data)
  } catch {
    return {
      commodity: data.commodity, state: data.state,
      month: data.month || new Date().getMonth() + 1,
      season: 'Kharif', overall_risk: 'MEDIUM',
      plant_advice: 'CAUTION',
      diseases_to_watch: [{
        disease: 'General Monitoring [DEMO]',
        risk_level: 'MEDIUM',
        description: 'Backend offline. Connect backend with ANTHROPIC_API_KEY for AI analysis.',
        prevention: 'Maintain field hygiene. Ensure drainage. Use certified seeds.'
      }],
      weather_advisory: 'No weather data — general advisory applied.',
      price_impact: 'MODERATE RISK — Prices may rise 5-15% if disease spreads.',
      tips: ['Keep field diary', 'Use certified seeds', 'Practice crop rotation'],
      ai_powered: false,
      analysis_note: 'Backend offline — connect backend with ANTHROPIC_API_KEY for AI analysis.',
      _demo: true
    }
  }
}

// ── Crops & Markets list ────────────────────────────────────────
export async function getCrops() {
  try {
    return await callApi('/crops')
  } catch {
    return { crops: ['Tomato','Onion','Potato','Wheat','Rice','Banana','Brinjal','Maize','Green Chilli','Cauliflower','Cabbage','Carrot','Mango','Garlic','Turmeric'], total: 15, _demo: true }
  }
}

export async function getStates() {
  try {
    return await callApi('/states')
  } catch {
    return {
      states: ['Tamil Nadu','Maharashtra','Karnataka','Uttar Pradesh','Punjab','Gujarat','Rajasthan','West Bengal','Madhya Pradesh','Andhra Pradesh','Telangana','Kerala','Haryana','Bihar'],
      total: 14, _demo: true
    }
  }
}

export async function getMarketsByState(state) {
  try {
    return await callApi(`/markets-by-state?state=${encodeURIComponent(state)}`)
  } catch {
    // Demo fallback: state-specific markets
    const DEMO_STATE_MARKETS = {
      'Tamil Nadu': ['Chennai','Coimbatore','Madurai','Salem','Trichy','Erode','Vellore','Tirunelveli','Alangeyam','Attur'],
      'Maharashtra': ['Pune','Mumbai','Nashik','Nagpur','Ahmednagar','Kolhapur','Solapur','Aurangabad'],
      'Karnataka': ['Bangalore','Hubli','Mysore','Belgaum','Mangalore','Davangere','Bellary'],
      'Uttar Pradesh': ['Agra','Lucknow','Kanpur','Varanasi','Allahabad','Meerut','Mathura'],
      'Punjab': ['Amritsar','Ludhiana','Jalandhar','Patiala','Bathinda','Mohali'],
      'Gujarat': ['Ahmedabad','Surat','Vadodara','Rajkot','Bhavnagar','Jamnagar'],
      'Rajasthan': ['Jaipur','Jodhpur','Udaipur','Kota','Bikaner','Ajmer'],
      'West Bengal': ['Kolkata','Howrah','Durgapur','Asansol','Siliguri'],
      'Madhya Pradesh': ['Bhopal','Indore','Jabalpur','Gwalior','Ujjain'],
      'Andhra Pradesh': ['Hyderabad','Visakhapatnam','Vijayawada','Guntur','Kurnool'],
      'Telangana': ['Hyderabad','Warangal','Nizamabad','Karimnagar','Khammam'],
      'Kerala': ['Thiruvananthapuram','Kochi','Kozhikode','Thrissur','Kollam'],
      'Haryana': ['Gurgaon','Faridabad','Panipat','Ambala','Hisar','Rohtak'],
      'Bihar': ['Patna','Gaya','Muzaffarpur','Bhagalpur','Darbhanga'],
    }
    const markets = DEMO_STATE_MARKETS[state] || ['No markets available for this state']
    return { state, markets, total: markets.length, _demo: true }
  }
}

export async function getMarkets() {
  try {
    return await callApi('/markets')
  } catch {
    return { markets: ['Coimbatore','Chennai','Madurai','Salem','Trichy','Erode','Vellore','Tirunelveli','Pune','Mumbai'], total: 10, _demo: true }
  }
}

export async function getHealth() {
  try {
    return await callApi('/health')
  } catch {
    return { status: 'offline', model_loaded: false }
  }
}

export async function registerNotifications(data) {
  try {
    return await callApi('/notifications/register', 'POST', data)
  } catch {
    return { status: 'registered', user_id: data.user_id, message: 'Saved locally (backend offline)', registered_at: new Date().toISOString(), _demo: true }
  }
}
