/**
 * CropHealth.jsx — AI-Powered Crop Disease Risk Advisory Page
 * CHANGES:
 *   - Added AI Analysis toggle (Rule-Based vs AI-Powered via Claude)
 *   - Shows "AI Analysis" badge when ai_powered=true from backend
 *   - Shows analysis_note to explain how the result was generated
 *   - Streaming loading animation for AI mode
 *   - All existing UI preserved and enhanced
 */
import { useState } from 'react'
import { Loader2, Shield, Thermometer, Sprout, AlertTriangle, Sparkles, BookOpen } from 'lucide-react'
import RiskBadge from '../components/RiskBadge'
import { checkCropHealth } from '../utils/api'

const STATES = ['Tamil Nadu','Maharashtra','Karnataka','Uttar Pradesh','Punjab','Gujarat',
                'Rajasthan','West Bengal','Kerala','Andhra Pradesh','Telangana','Bihar',
                'Madhya Pradesh','Haryana','Odisha','Chattisgarh']
const CROPS  = ['Tomato','Onion','Potato','Wheat','Rice','Maize','Brinjal','Cabbage',
                'Cauliflower','Banana','Mango','Green Chilli','Garlic','Turmeric','Carrot']
const MONTHS = ['January','February','March','April','May','June',
                'July','August','September','October','November','December']

const RISK_COLORS = {
  HIGH:     'border-orange-400 bg-orange-50',
  MEDIUM:   'border-yellow-400 bg-yellow-50',
  LOW:      'border-emerald-400 bg-emerald-50',
  CRITICAL: 'border-red-500 bg-red-50',
}

export default function CropHealth({ tr }) {
  const [form, setForm] = useState({
    commodity: 'Tomato', state: 'Tamil Nadu',
    month: new Date().getMonth() + 1,
    current_temp: '', rainfall_mm: ''
  })
  const [useAI, setUseAI]   = useState(false)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)

  const set = (k, v) => setForm(f => ({ ...f, [k]: v }))

  const submit = async () => {
    setLoading(true)
    setResult(null)
    try {
      const res = await checkCropHealth({
        commodity:    form.commodity,
        state:        form.state,
        month:        +form.month,
        current_temp: form.current_temp ? +form.current_temp : undefined,
        rainfall_mm:  form.rainfall_mm  ? +form.rainfall_mm  : undefined,
      }, useAI)
      setResult(res)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-5xl mx-auto px-4 py-8">
      <div className="mb-8">
        <p className="font-mono text-xs text-farm-bright uppercase tracking-widest mb-1">Disease Advisory</p>
        <h1 className="font-syne font-bold text-3xl text-farm-deep lang-slide">{tr('health_title')}</h1>
        <p className="text-gray-500 mt-1 lang-slide">{tr('health_sub')}</p>
      </div>

      {/* Form */}
      <div className="bg-white rounded-2xl border border-gray-100 p-6 mb-6 shadow-sm">

        {/* AI / Rule toggle */}
        <div className="flex items-center gap-3 mb-5 p-3 bg-farm-pale/40 rounded-xl border border-farm-pale">
          <button
            onClick={() => setUseAI(false)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg font-mono text-xs font-medium transition-colors ${
              !useAI ? 'bg-farm-deep text-white shadow' : 'text-gray-500 hover:bg-white'
            }`}
          >
            <BookOpen size={13} />
            Rule-Based
          </button>
          <button
            onClick={() => setUseAI(true)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg font-mono text-xs font-medium transition-colors ${
              useAI ? 'bg-farm-deep text-white shadow' : 'text-gray-500 hover:bg-white'
            }`}
          >
            <Sparkles size={13} />
            AI Analysis (Claude)
          </button>
          <span className="font-mono text-xs text-gray-400 ml-auto">
            {useAI
              ? 'Requires ANTHROPIC_API_KEY on backend'
              : 'Works offline — verified disease calendars'}
          </span>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          <div>
            <label className="block font-mono text-xs text-gray-500 mb-1 lang-slide">{tr('health_crop')}</label>
            <select value={form.commodity} onChange={e => set('commodity', e.target.value)}
              className="w-full border border-gray-200 rounded-xl px-3 py-2.5 font-mono text-sm focus:outline-none focus:ring-2 focus:ring-farm-bright bg-white">
              {CROPS.map(c => <option key={c}>{c}</option>)}
            </select>
          </div>
          <div>
            <label className="block font-mono text-xs text-gray-500 mb-1 lang-slide">{tr('health_state')}</label>
            <select value={form.state} onChange={e => set('state', e.target.value)}
              className="w-full border border-gray-200 rounded-xl px-3 py-2.5 font-mono text-sm focus:outline-none focus:ring-2 focus:ring-farm-bright bg-white">
              {STATES.map(s => <option key={s}>{s}</option>)}
            </select>
          </div>
          <div>
            <label className="block font-mono text-xs text-gray-500 mb-1 lang-slide">{tr('health_month')}</label>
            <select value={form.month} onChange={e => set('month', +e.target.value)}
              className="w-full border border-gray-200 rounded-xl px-3 py-2.5 font-mono text-sm focus:outline-none focus:ring-2 focus:ring-farm-bright bg-white">
              {MONTHS.map((m, i) => <option key={m} value={i+1}>{m}</option>)}
            </select>
          </div>
          <div>
            <label className="block font-mono text-xs text-gray-500 mb-1 lang-slide">{tr('health_temp')}</label>
            <input type="number" value={form.current_temp} onChange={e => set('current_temp', e.target.value)}
              className="w-full border border-gray-200 rounded-xl px-3 py-2.5 font-mono text-sm focus:outline-none focus:ring-2 focus:ring-farm-bright"
              placeholder="32" />
          </div>
          <div>
            <label className="block font-mono text-xs text-gray-500 mb-1 lang-slide">{tr('health_rain')}</label>
            <input type="number" value={form.rainfall_mm} onChange={e => set('rainfall_mm', e.target.value)}
              className="w-full border border-gray-200 rounded-xl px-3 py-2.5 font-mono text-sm focus:outline-none focus:ring-2 focus:ring-farm-bright"
              placeholder="120" />
          </div>
        </div>

        <button onClick={submit} disabled={loading}
          className="mt-4 bg-farm-deep text-white font-syne font-bold px-8 py-3 rounded-xl hover:bg-farm-mid transition-colors disabled:opacity-60 flex items-center gap-2">
          {loading ? (
            <>
              <Loader2 size={18} className="animate-spin" />
              {useAI ? 'AI is analyzing...' : tr('health_loading')}
            </>
          ) : (
            <>
              {useAI ? <Sparkles size={18} /> : <Shield size={18} />}
              {useAI ? 'Run AI Analysis' : tr('health_btn')}
            </>
          )}
        </button>
      </div>

      {/* Results */}
      {result && (
        <div className="space-y-6">
          {result._demo && (
            <div className="bg-orange-50 border border-orange-200 rounded-xl px-4 py-2 font-mono text-xs text-orange-700">
              {tr('api_offline')}
            </div>
          )}

          {/* Analysis source badge */}
          <div className={`flex items-center gap-3 px-4 py-3 rounded-xl border text-sm font-mono ${
            result.ai_powered
              ? 'bg-violet-50 border-violet-200 text-violet-800'
              : 'bg-sky-50 border-sky-200 text-sky-800'
          }`}>
            {result.ai_powered
              ? <Sparkles size={15} className="text-violet-600 shrink-0" />
              : <BookOpen size={15} className="text-sky-600 shrink-0" />}
            <div>
              <span className="font-bold mr-2">
                {result.ai_powered ? 'AI-Powered Analysis (Claude)' : 'Rule-Based Advisory'}
              </span>
              <span className="text-xs opacity-70">{result.analysis_note}</span>
            </div>
          </div>

          {/* Overview */}
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
              <div>
                <p className="font-syne font-semibold text-sky-800 mb-1 lang-slide">{tr('health_weather')}</p>
                <p className="text-sm text-sky-700 leading-relaxed">{result.weather_advisory}</p>
              </div>
            </div>
          )}

          {/* Diseases */}
          <div>
            <h3 className="font-syne font-bold text-farm-deep text-lg mb-3 lang-slide">{tr('health_diseases')}</h3>
            <div className="space-y-4">
              {result.diseases_to_watch.map((d, i) => (
                <div key={i} className={`rounded-2xl border-l-4 p-5 ${RISK_COLORS[d.risk_level] || 'border-gray-300 bg-gray-50'}`}>
                  <div className="flex items-start justify-between gap-4 mb-3">
                    <div className="flex items-center gap-2">
                      <AlertTriangle size={18} className="shrink-0 opacity-70" />
                      <h4 className="font-syne font-bold text-gray-800">{d.disease}</h4>
                    </div>
                    <RiskBadge level={d.risk_level} tr={tr} />
                  </div>
                  <p className="text-sm text-gray-700 mb-3 leading-relaxed">{d.description}</p>
                  <div className="bg-white/70 rounded-xl p-3">
                    <p className="font-mono text-xs text-gray-500 uppercase tracking-wider mb-1 lang-slide">
                      {tr('health_prevention')}
                    </p>
                    <p className="text-sm text-gray-700 leading-relaxed">{d.prevention}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Price impact */}
          <div className="bg-yellow-50 border border-yellow-200 rounded-2xl p-5 flex gap-3">
            <Sprout size={20} className="text-yellow-700 shrink-0 mt-0.5" />
            <div>
              <p className="font-syne font-semibold text-yellow-800 mb-1 lang-slide">{tr('health_price_impact')}</p>
              <p className="text-sm text-yellow-700 leading-relaxed">{result.price_impact}</p>
            </div>
          </div>

          {/* Tips */}
          <div className="bg-white rounded-2xl border border-gray-100 p-6 shadow-sm">
            <h3 className="font-syne font-bold text-farm-deep text-lg mb-4 flex items-center gap-2 lang-slide">
              <Sprout size={18} className="text-farm-bright" />
              {tr('health_tips')}
            </h3>
            <ul className="space-y-3">
              {result.tips.map((tip, i) => (
                <li key={i} className="flex items-start gap-3 text-sm text-gray-700">
                  <span className="w-6 h-6 bg-farm-pale rounded-full flex items-center justify-center shrink-0 text-farm-deep font-mono font-bold text-xs">
                    {i + 1}
                  </span>
                  <span className="leading-relaxed">{tip}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}
    </div>
  )
}
