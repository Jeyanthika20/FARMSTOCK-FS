/**
 * CropHealth.jsx — Claude AI Crop Disease Advisory (Bilingual: EN + TA)
 *
 * Language switching is controlled by the global navbar toggle (⊕ தமிழ் / English).
 * The parent passes `lang` ('en' | 'ta') and `tr()` as props.
 * When lang==='ta', all _ta fields are shown; otherwise English.
 * If a _ta field is empty, gracefully falls back to the English field.
 */

import { useState } from 'react'
import { Loader2, Thermometer, Sprout, AlertTriangle, Sparkles, WifiOff } from 'lucide-react'
import RiskBadge from '../components/RiskBadge'
import { checkCropHealth } from '../utils/api'
import { CROPS_TA_MAP, STATES_TA_MAP } from '../utils/inputstranslations'

const STATES_EN = [
  'Tamil Nadu','Maharashtra','Karnataka','Uttar Pradesh','Punjab','Gujarat',
  'Rajasthan','West Bengal','Kerala','Andhra Pradesh','Telangana','Bihar',
  'Madhya Pradesh','Haryana','Odisha','Chattisgarh'
]
const CROPS_EN = [
  'Tomato','Onion','Potato','Wheat','Rice','Maize','Brinjal','Cabbage',
  'Cauliflower','Banana','Mango','Green Chilli','Garlic','Turmeric','Carrot'
]
const MONTHS_EN = [
  'January','February','March','April','May','June',
  'July','August','September','October','November','December'
]
const MONTHS_TA = [
  'ஜனவரி','பிப்ரவரி','மார்ச்','ஏப்ரல்','மே','ஜூன்',
  'ஜூலை','ஆகஸ்ட்','செப்டம்பர்','அக்டோபர்','நவம்பர்','டிசம்பர்'
]

const RISK_COLORS = {
  HIGH:     'border-orange-400 bg-orange-50',
  MEDIUM:   'border-yellow-400 bg-yellow-50',
  LOW:      'border-emerald-400 bg-emerald-50',
  CRITICAL: 'border-red-500 bg-red-50',
}

// Returns Tamil text if lang==='ta' AND ta is non-empty; otherwise English.
const pick = (lang, en, ta) => (lang === 'ta' && ta) ? ta : en

export default function CropHealth({ tr, lang = 'en' }) {
  const [form, setForm] = useState({
    commodity:    'Tomato',
    state:        'Tamil Nadu',
    month:        new Date().getMonth() + 1,
    current_temp: '',
    rainfall_mm:  '',
  })
  const [result,  setResult]  = useState(null)
  const [loading, setLoading] = useState(false)
  const [error,   setError]   = useState(null)

  const set = (k, v) => setForm(f => ({ ...f, [k]: v }))

  const submit = async () => {
    setLoading(true)
    setResult(null)
    setError(null)
    try {
      const res = await checkCropHealth({
        commodity:    form.commodity,
        state:        form.state,
        month:        +form.month,
        current_temp: form.current_temp ? +form.current_temp : undefined,
        rainfall_mm:  form.rainfall_mm  ? +form.rainfall_mm  : undefined,
      })
      if (!res.ai_powered) {
        setError(res.analysis_note || 'AI analysis unavailable. Please try again.')
        return
      }
      setResult(res)
    } catch (err) {
      setError('Could not reach the server. Please check your connection.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-5xl mx-auto px-4 py-8">

      {/* ── Page header ───────────────────────────────────────────────────── */}
      <div className="mb-8">
        <p className="font-mono text-xs text-farm-bright uppercase tracking-widest mb-1">
          {tr('health_tagline')}
        </p>
        <h1 className="font-syne font-bold text-3xl text-farm-deep lang-slide">
          {tr('health_title')}
        </h1>
        <p className="text-gray-500 mt-1 lang-slide">{tr('health_sub')}</p>
        <div className="inline-flex items-center gap-1.5 mt-3 px-3 py-1 bg-violet-50
                        border border-violet-200 rounded-full text-xs font-mono text-violet-700">
          <Sparkles size={11} />
          {pick(lang,
            'Powered by Claude AI (Anthropic)',
            'Claude AI (Anthropic) ஆல் இயக்கப்படுகிறது'
          )}
        </div>
      </div>

      {/* ── Input form ────────────────────────────────────────────────────── */}
      <div className="bg-white rounded-2xl border border-gray-100 p-6 mb-6 shadow-sm">
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">

          <div>
            <label className="block font-mono text-xs text-gray-500 mb-1 lang-slide">
              {tr('health_crop')}
            </label>
            <select value={form.commodity} onChange={e => set('commodity', e.target.value)}
              className="w-full border border-gray-200 rounded-xl px-3 py-2.5 font-mono
                         text-sm focus:outline-none focus:ring-2 focus:ring-farm-bright bg-white">
              {CROPS_EN.map(c => <option key={c} value={c}>{lang === 'ta' ? (CROPS_TA_MAP[c] || c) : c}</option>)}
            </select>
          </div>

          <div>
            <label className="block font-mono text-xs text-gray-500 mb-1 lang-slide">
              {tr('health_state')}
            </label>
            <select value={form.state} onChange={e => set('state', e.target.value)}
              className="w-full border border-gray-200 rounded-xl px-3 py-2.5 font-mono
                         text-sm focus:outline-none focus:ring-2 focus:ring-farm-bright bg-white">
              {STATES_EN.map(s => <option key={s} value={s}>{lang === 'ta' ? (STATES_TA_MAP[s] || s) : s}</option>)}
            </select>
          </div>

          <div>
            <label className="block font-mono text-xs text-gray-500 mb-1 lang-slide">
              {tr('health_month')}
            </label>
            <select value={form.month} onChange={e => set('month', +e.target.value)}
              className="w-full border border-gray-200 rounded-xl px-3 py-2.5 font-mono
                         text-sm focus:outline-none focus:ring-2 focus:ring-farm-bright bg-white">
              {MONTHS_EN.map((m, i) => <option key={m} value={i + 1}>{lang === 'ta' ? MONTHS_TA[i] : m}</option>)}
            </select>
          </div>

          <div>
            <label className="block font-mono text-xs text-gray-500 mb-1 lang-slide">
              {tr('health_temp')}
            </label>
            <input type="number" value={form.current_temp}
              onChange={e => set('current_temp', e.target.value)}
              className="w-full border border-gray-200 rounded-xl px-3 py-2.5 font-mono
                         text-sm focus:outline-none focus:ring-2 focus:ring-farm-bright"
              placeholder="32 (optional)" />
          </div>

          <div>
            <label className="block font-mono text-xs text-gray-500 mb-1 lang-slide">
              {tr('health_rain')}
            </label>
            <input type="number" value={form.rainfall_mm}
              onChange={e => set('rainfall_mm', e.target.value)}
              className="w-full border border-gray-200 rounded-xl px-3 py-2.5 font-mono
                         text-sm focus:outline-none focus:ring-2 focus:ring-farm-bright"
              placeholder="120 (optional)" />
          </div>

        </div>

        <button onClick={submit} disabled={loading}
          className="mt-5 bg-farm-deep text-white font-syne font-bold px-8 py-3 rounded-xl
                     hover:bg-farm-mid transition-colors disabled:opacity-60 flex items-center gap-2">
          {loading ? (
            <>
              <Loader2 size={18} className="animate-spin" />
              <span>{pick(lang, 'Claude is analyzing...', 'Claude பகுப்பாய்வு செய்கிறது...')}</span>
            </>
          ) : (
            <>
              <Sparkles size={18} />
              <span>{pick(lang, 'Analyze with AI', 'AI கொண்டு பகுப்பாய்')}</span>
            </>
          )}
        </button>
      </div>

      {/* ── Error ─────────────────────────────────────────────────────────── */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-2xl p-5 flex gap-3 mb-6">
          <WifiOff size={20} className="text-red-500 shrink-0 mt-0.5" />
          <div>
            <p className="font-syne font-semibold text-red-800 mb-0.5">
              {pick(lang, 'AI Analysis Unavailable', 'AI பகுப்பாய்வு கிடைக்கவில்லை')}
            </p>
            <p className="text-sm text-red-700 leading-relaxed">{error}</p>
            <p className="text-xs text-red-500 mt-2 font-mono">
              {pick(lang,
                'Check that ANTHROPIC_API_KEY is set in your backend environment.',
                'உங்கள் backend சூழலில் ANTHROPIC_API_KEY அமைக்கப்பட்டுள்ளதா என்பதை சரிபார்க்கவும்.'
              )}
            </p>
          </div>
        </div>
      )}

      {/* ── Results ───────────────────────────────────────────────────────── */}
      {result && (
        <div className="space-y-6">

          {/* AI badge + analysis note */}
          <div className="flex items-start gap-3 px-4 py-3 rounded-xl border text-sm font-mono
                          bg-violet-50 border-violet-200 text-violet-800">
            <Sparkles size={15} className="text-violet-600 shrink-0 mt-0.5" />
            <div>
              <span className="font-bold mr-2">
                {pick(lang, 'AI-Powered Analysis (Claude)', 'AI பகுப்பாய்வு (Claude)')}
              </span>
              {result.analysis_note && (
                <span className="text-xs opacity-70 block mt-0.5">
                  {pick(lang, result.analysis_note, result.analysis_note_ta)}
                </span>
              )}
            </div>
          </div>

          {/* Overview cards */}
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            <div className="bg-white rounded-2xl border border-gray-100 p-4 shadow-sm">
              <p className="font-mono text-xs text-gray-500 mb-2 lang-slide">{tr('health_risk')}</p>
              <RiskBadge level={result.overall_risk} tr={tr} />
            </div>
            <div className="bg-white rounded-2xl border border-gray-100 p-4 shadow-sm">
              <p className="font-mono text-xs text-gray-500 mb-2 lang-slide">{tr('health_season')}</p>
              <span className="font-syne font-bold text-farm-deep">{result.season}</span>
            </div>
            <div className="bg-white rounded-2xl border border-gray-100 p-4 shadow-sm">
              <p className="font-mono text-xs text-gray-500 mb-2 lang-slide">{tr('health_plant')}</p>
              <RiskBadge level={result.plant_advice} tr={tr} />
            </div>
          </div>

          {/* Weather advisory */}
          {result.weather_advisory && (
            <div className="bg-sky-50 border border-sky-200 rounded-2xl p-5 flex gap-3">
              <Thermometer size={20} className="text-sky-600 shrink-0 mt-0.5" />
              <div className="flex-1">
                <p className="font-syne font-semibold text-sky-800 mb-1 lang-slide">
                  {tr('health_weather')}
                </p>
                <p className="text-sm text-sky-700 leading-relaxed">
                  {pick(lang, result.weather_advisory, result.weather_advisory_ta)}
                </p>
              </div>
            </div>
          )}

          {/* Disease cards */}
          <div>
            <h3 className="font-syne font-bold text-farm-deep text-lg mb-3 lang-slide">
              {tr('health_diseases')}
            </h3>
            <div className="space-y-4">
              {result.diseases_to_watch.map((d, i) => (
                <div key={i}
                  className={`rounded-2xl border-l-4 p-5 ${RISK_COLORS[d.risk_level] || 'border-gray-300 bg-gray-50'}`}>

                  <div className="flex items-start justify-between gap-4 mb-3">
                    <div className="flex items-center gap-2">
                      <AlertTriangle size={18} className="shrink-0 opacity-70" />
                      <h4 className="font-syne font-bold text-gray-800">{d.disease}</h4>
                    </div>
                    <RiskBadge level={d.risk_level} tr={tr} />
                  </div>

                  <p className="text-sm text-gray-700 leading-relaxed">
                    {pick(lang, d.description, d.description_ta)}
                  </p>

                  <div className="bg-white/70 rounded-xl p-3 mt-3">
                    <p className="font-mono text-xs text-gray-500 uppercase tracking-wider mb-1 lang-slide">
                      {tr('health_prevention')}
                    </p>
                    <p className="text-sm text-gray-700 leading-relaxed">
                      {pick(lang, d.prevention, d.prevention_ta)}
                    </p>
                  </div>

                </div>
              ))}
            </div>
          </div>

          {/* Price impact */}
          {result.price_impact && (
            <div className="bg-yellow-50 border border-yellow-200 rounded-2xl p-5 flex gap-3">
              <Sprout size={20} className="text-yellow-700 shrink-0 mt-0.5" />
              <div className="flex-1">
                <p className="font-syne font-semibold text-yellow-800 mb-1 lang-slide">
                  {tr('health_price_impact')}
                </p>
                <p className="text-sm text-yellow-700 leading-relaxed">
                  {pick(lang, result.price_impact, result.price_impact_ta)}
                </p>
              </div>
            </div>
          )}

          {/* Tips */}
          {result.tips?.length > 0 && (
            <div className="bg-white rounded-2xl border border-gray-100 p-6 shadow-sm">
              <h3 className="font-syne font-bold text-farm-deep text-lg mb-4
                             flex items-center gap-2 lang-slide">
                <Sprout size={18} className="text-farm-bright" />
                {tr('health_tips')}
              </h3>
              <ul className="space-y-4">
                {result.tips.map((tip, i) => (
                  <li key={i} className="flex items-start gap-3">
                    <span className="w-6 h-6 bg-farm-pale rounded-full flex items-center justify-center
                                     shrink-0 text-farm-deep font-mono font-bold text-xs mt-0.5">
                      {i + 1}
                    </span>
                    <span className="text-sm text-gray-700 leading-relaxed">
                      {pick(lang, tip, result.tips_ta?.[i])}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          )}

        </div>
      )}
    </div>
  )
}
