/**
 * Predict.jsx — Crop Price Prediction Page
 * Features: Autocomplete from API crop/market lists, bilingual labels,
 *           detailed result card with recommendation badge, demo fallback
 * CHANGE: Market dropdown now filters based on selected State.
 */
import { useState, useEffect } from 'react'
import { TrendingUp, TrendingDown, Minus, Loader2, AlertCircle } from 'lucide-react'
import RiskBadge from '../components/RiskBadge'
import { predictPrice, getCrops, getStates, getMarketsByState } from '../utils/api'
import { CROPS_TA_MAP, STATES_TA_MAP, MARKETS_TA_MAP } from '../utils/inputstranslations'

export default function Predict({ tr, lang = 'en' }) {
  const [crops, setCrops]     = useState([])
  const [states, setStates]   = useState([])
  const [markets, setMarkets] = useState([])
  const [form, setForm] = useState({
    commodity: 'Tomato', market: '', state: 'Tamil Nadu',
    current_price: '', min_price: '', max_price: '',
    lag_7: '', lag_14: '', lag_30: '',
    date: new Date().toISOString().split('T')[0]
  })
  const [result, setResult]   = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError]     = useState(null)
  const [marketsLoading, setMarketsLoading] = useState(false)

  // Load crops and states once on mount
  useEffect(() => {
    getCrops().then(r => setCrops(r.crops || []))
    getStates().then(r => {
      const stateList = r.states || []
      setStates(stateList)
      // Trigger initial market load for default state
      if (stateList.length > 0) {
        loadMarketsForState('Tamil Nadu')
      }
    })
  }, [])

  // Whenever state changes, reload markets and reset market selection
  const loadMarketsForState = (state) => {
    setMarketsLoading(true)
    setMarkets([])
    setForm(f => ({ ...f, market: '' }))
    getMarketsByState(state).then(r => {
      const mList = r.markets || []
      setMarkets(mList)
      // Auto-select first market
      setForm(f => ({ ...f, market: mList[0] || '' }))
      setMarketsLoading(false)
    })
  }

  const set = (k, v) => {
    if (k === 'state') {
      setForm(f => ({ ...f, state: v }))
      loadMarketsForState(v)
    } else {
      setForm(f => ({ ...f, [k]: v }))
    }
  }

  const submit = async () => {
    if (!form.commodity || !form.market || !form.current_price) {
      setError('Please fill Crop, Market and Current Price.')
      return
    }
    setError(null)
    setLoading(true)
    try {
      const data = {
        commodity: form.commodity, market: form.market, state: form.state,
        current_price: +form.current_price, date: form.date,
        min_price:  form.min_price  ? +form.min_price  : undefined,
        max_price:  form.max_price  ? +form.max_price  : undefined,
        lag_7:      form.lag_7      ? +form.lag_7      : undefined,
        lag_14:     form.lag_14     ? +form.lag_14     : undefined,
        lag_30:     form.lag_30     ? +form.lag_30     : undefined,
      }
      const res = await predictPrice(data)
      setResult(res)
    } catch (e) {
      setError(tr('error'))
    } finally {
      setLoading(false)
    }
  }

  const changePct = result?.change_pct || 0
  const trendUp   = changePct > 0
  const trendDown = changePct < 0

  return (
    <div className="max-w-5xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-8">
        <p className="font-mono text-xs text-farm-bright uppercase tracking-widest mb-1">{tr('predict_tagline')}</p>
        <h1 className="font-syne font-bold text-3xl text-farm-deep lang-slide">{tr('predict_title')}</h1>
        <p className="text-gray-500 mt-1 lang-slide">{tr('predict_sub')}</p>
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        {/* Form */}
        <div className="bg-white rounded-2xl border border-gray-100 p-6 shadow-sm">
          <div className="space-y-4">
            {/* Crop */}
            <div>
              <label className="block font-mono text-xs text-gray-500 uppercase tracking-wider mb-1 lang-slide">
                {tr('predict_crop')}
              </label>
              {lang === 'ta' ? (
                <select
                  value={form.commodity}
                  onChange={e => set('commodity', e.target.value)}
                  className="w-full border border-gray-200 rounded-xl px-4 py-2.5 font-mono text-sm focus:outline-none focus:ring-2 focus:ring-farm-bright bg-white"
                >
                  {crops.length > 0
                    ? crops.map(c => <option key={c} value={c}>{CROPS_TA_MAP[c] || c}</option>)
                    : ['Tomato','Onion','Potato','Wheat','Rice','Maize','Brinjal','Cabbage',
                       'Cauliflower','Banana','Mango','Green Chilli','Garlic','Turmeric','Carrot'
                      ].map(c => <option key={c} value={c}>{CROPS_TA_MAP[c] || c}</option>)
                  }
                </select>
              ) : (
                <>
                  <input
                    list="crop-list"
                    value={form.commodity}
                    onChange={e => set('commodity', e.target.value)}
                    className="w-full border border-gray-200 rounded-xl px-4 py-2.5 font-mono text-sm focus:outline-none focus:ring-2 focus:ring-farm-bright"
                    placeholder="e.g. Tomato"
                  />
                  <datalist id="crop-list">
                    {crops.map(c => <option key={c} value={c} />)}
                  </datalist>
                </>
              )}
            </div>

            {/* State — select this FIRST to filter markets */}
            <div>
              <label className="block font-mono text-xs text-gray-500 uppercase tracking-wider mb-1 lang-slide">
                {tr('predict_state')}
              </label>
              <select
                value={form.state}
                onChange={e => set('state', e.target.value)}
                className="w-full border border-gray-200 rounded-xl px-4 py-2.5 font-mono text-sm focus:outline-none focus:ring-2 focus:ring-farm-bright bg-white"
              >
                {states.length > 0
                  ? states.map(s => <option key={s} value={s}>{lang === 'ta' ? (STATES_TA_MAP[s] || s) : s}</option>)
                  : <option value="Tamil Nadu">{lang === 'ta' ? 'தமிழ் நாடு' : 'Tamil Nadu'}</option>
                }
              </select>
            </div>

            {/* Market — filtered by selected state */}
            <div>
              <label className="block font-mono text-xs text-gray-500 uppercase tracking-wider mb-1 lang-slide">
                {tr('predict_market')}
                {marketsLoading && (
                  <span className="ml-2 text-farm-bright normal-case">{tr('loading')}</span>
                )}
                {!marketsLoading && markets.length > 0 && (
                  <span className="ml-2 text-gray-400 normal-case font-normal">({markets.length} {tr('markets_in')} {lang === 'ta' ? (STATES_TA_MAP[form.state] || form.state) : form.state})</span>
                )}
              </label>
              <select
                value={form.market}
                onChange={e => set('market', e.target.value)}
                disabled={marketsLoading || markets.length === 0}
                className="w-full border border-gray-200 rounded-xl px-4 py-2.5 font-mono text-sm focus:outline-none focus:ring-2 focus:ring-farm-bright bg-white disabled:opacity-50"
              >
                {marketsLoading ? (
                  <option>{tr('loading_markets')}</option>
                ) : markets.length === 0 ? (
                  <option>{tr('no_markets')}</option>
                ) : (
                  markets.map(m => <option key={m} value={m}>{lang === 'ta' ? (MARKETS_TA_MAP[m] || m) : m}</option>)
                )}
              </select>
              {!marketsLoading && markets.length === 0 && form.state && (
                <p className="text-xs text-red-500 mt-1 font-mono">
                  {tr('no_markets_state')} {lang === 'ta' ? (STATES_TA_MAP[form.state] || form.state) : form.state}. {tr('select_diff_state')}
                </p>
              )}
            </div>

            {/* Current price */}
            <div>
              <label className="block font-mono text-xs text-gray-500 uppercase tracking-wider mb-1 lang-slide">
                {tr('predict_price')}
              </label>
              <input
                type="number" step="0.01" min="0"
                value={form.current_price}
                onChange={e => set('current_price', e.target.value)}
                className="w-full border border-gray-200 rounded-xl px-4 py-2.5 font-mono text-sm focus:outline-none focus:ring-2 focus:ring-farm-bright"
                placeholder="45.00"
              />
            </div>

            {/* Optional prices row */}
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block font-mono text-xs text-gray-500 mb-1 lang-slide">{tr('predict_min_price')}</label>
                <input type="number" value={form.min_price} onChange={e => set('min_price', e.target.value)}
                  className="w-full border border-gray-200 rounded-xl px-3 py-2 font-mono text-sm focus:outline-none focus:ring-2 focus:ring-farm-bright" placeholder="40" />
              </div>
              <div>
                <label className="block font-mono text-xs text-gray-500 mb-1 lang-slide">{tr('predict_max_price')}</label>
                <input type="number" value={form.max_price} onChange={e => set('max_price', e.target.value)}
                  className="w-full border border-gray-200 rounded-xl px-3 py-2 font-mono text-sm focus:outline-none focus:ring-2 focus:ring-farm-bright" placeholder="50" />
              </div>
            </div>

            {/* Lag prices row */}
            <div className="grid grid-cols-3 gap-2">
              {[7,14,30].map(n => (
                <div key={n}>
                  <label className="block font-mono text-xs text-gray-500 mb-1 lang-slide">{tr(`predict_lag_${n}`)}</label>
                  <input type="number" value={form[`lag_${n}`]} onChange={e => set(`lag_${n}`, e.target.value)}
                    className="w-full border border-gray-200 rounded-xl px-3 py-2 font-mono text-sm focus:outline-none focus:ring-2 focus:ring-farm-bright" placeholder="—" />
                </div>
              ))}
            </div>

            {/* Date */}
            <div>
              <label className="block font-mono text-xs text-gray-500 uppercase tracking-wider mb-1 lang-slide">
                {tr('predict_date')}
              </label>
              <input
                type="date"
                value={form.date}
                onChange={e => set('date', e.target.value)}
                className="w-full border border-gray-200 rounded-xl px-4 py-2.5 font-mono text-sm focus:outline-none focus:ring-2 focus:ring-farm-bright"
              />
            </div>

            {error && (
              <div className="flex items-center gap-2 bg-red-50 border border-red-200 rounded-xl px-4 py-3 text-red-700 text-sm">
                <AlertCircle size={16} /> {error}
              </div>
            )}

            <button
              onClick={submit}
              disabled={loading || marketsLoading}
              className="w-full bg-farm-deep text-white font-syne font-bold py-3 rounded-xl hover:bg-farm-mid transition-colors disabled:opacity-60 flex items-center justify-center gap-2"
            >
              {loading ? <><Loader2 size={18} className="animate-spin" /> {tr('predict_loading')}</> : tr('predict_btn')}
            </button>
          </div>
        </div>

        {/* Result */}
        {result && (
          <div className="bg-white rounded-2xl border border-gray-100 p-6 shadow-sm">
            <div className="flex items-center justify-between mb-6">
              <h2 className="font-syne font-bold text-farm-deep text-xl lang-slide">{tr('predict_result')}</h2>
              {result._demo && (
                <span className="font-mono text-xs bg-orange-100 text-orange-700 px-2 py-0.5 rounded-full">DEMO</span>
              )}
            </div>

            {/* Price comparison */}
            <div className="grid grid-cols-2 gap-4 mb-6">
              <div className="bg-gray-50 rounded-xl p-4">
                <p className="font-mono text-xs text-gray-500 mb-1 lang-slide">{tr('predict_current')}</p>
                <p className="font-syne font-bold text-2xl text-farm-deep">
                  {tr('rs')}{result.current_price_kg}<span className="text-sm font-normal">{tr('kg')}</span>
                </p>
                <p className="font-mono text-xs text-gray-400">{tr('rs')}{+(result.current_price_kg * 100).toFixed(0)}{tr('quintal')}</p>
              </div>
              <div className={`rounded-xl p-4 ${trendUp ? 'bg-emerald-50' : trendDown ? 'bg-red-50' : 'bg-gray-50'}`}>
                <p className="font-mono text-xs text-gray-500 mb-1 lang-slide">{tr('predict_predicted')}</p>
                <p className={`font-syne font-bold text-2xl ${trendUp ? 'text-emerald-700' : trendDown ? 'text-red-700' : 'text-farm-deep'}`}>
                  {tr('rs')}{result.predicted_price_kg}<span className="text-sm font-normal">{tr('kg')}</span>
                </p>
                <p className="font-mono text-xs text-gray-400">{tr('rs')}{result.predicted_price_quintal}{tr('quintal')}</p>
              </div>
            </div>

            {/* Change indicator */}
            <div className={`flex items-center gap-3 p-3 rounded-xl mb-4 ${trendUp ? 'bg-emerald-50' : trendDown ? 'bg-red-50' : 'bg-gray-50'}`}>
              {trendUp ? <TrendingUp className="text-emerald-600" size={20} />
                : trendDown ? <TrendingDown className="text-red-600" size={20} />
                : <Minus className="text-gray-500" size={20} />}
              <div>
                <p className="font-mono text-xs text-gray-500 lang-slide">{tr('predict_change')}</p>
                <p className={`font-syne font-bold ${trendUp ? 'text-emerald-700' : trendDown ? 'text-red-700' : 'text-gray-700'}`}>
                  {changePct > 0 ? '+' : ''}{changePct}%
                </p>
              </div>
            </div>

            {/* Details */}
            <div className="space-y-3">
              <div className="flex justify-between items-center py-2 border-b border-gray-100">
                <span className="font-mono text-xs text-gray-500 lang-slide">{tr('predict_rec')}</span>
                <RiskBadge level={result.recommendation} tr={tr} />
              </div>
              <div className="flex justify-between items-center py-2 border-b border-gray-100">
                <span className="font-mono text-xs text-gray-500 lang-slide">{tr('predict_confidence')}</span>
                <div className="flex items-center gap-2">
                  <div className="w-24 h-2 bg-gray-100 rounded-full overflow-hidden">
                    <div className="h-full bg-farm-bright rounded-full" style={{ width: `${result.confidence}%` }} />
                  </div>
                  <span className="font-mono text-sm font-medium text-farm-deep">{result.confidence}%</span>
                </div>
              </div>
              <div className="flex justify-between py-2 border-b border-gray-100">
                <span className="font-mono text-xs text-gray-500 lang-slide">{tr('predict_model')}</span>
                <span className="font-mono text-xs text-farm-mid">{result.model_used}</span>
              </div>
              <div className="flex justify-between py-2">
                <span className="font-mono text-xs text-gray-500">MAE</span>
                <span className="font-mono text-xs text-gray-600">{tr('rs')}{result.mae_kg}{tr('kg')}</span>
              </div>
            </div>
          </div>
        )}

        {!result && !loading && (
          <div className="bg-farm-pale/40 rounded-2xl border border-farm-pale flex items-center justify-center p-12">
            <div className="text-center text-farm-mid">
              <TrendingUp size={40} className="mx-auto mb-3 opacity-40" />
              <p className="font-syne font-semibold">{tr('fill_form_prediction')}</p>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
