/**
 * Forecast.jsx — 7–90 Day Price Forecast Page
 * CHANGES:
 *   - Best and worst sell dates are now always DISTINCT (fix via backend wave signal)
 *   - Best/Worst sell day highlighted in day-by-day table with color badges
 *   - Worst sell price shown in summary card
 *   - State-linked market dropdown (from previous fix)
 *   - Demo fallback also guarantees distinct best/worst
 */
import { useState, useEffect } from 'react'
import { Loader2, TrendingUp, TrendingDown, BarChart3, Star, AlertOctagon } from 'lucide-react'
import {
  XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, ReferenceLine, Area, AreaChart
} from 'recharts'
import RiskBadge from '../components/RiskBadge'
import { forecastPrices, getCrops, getStates, getMarketsByState } from '../utils/api'

const CustomTooltip = ({ active, payload, label, tr, bestDate, worstDate }) => {
  if (!active || !payload?.length) return null
  const d = payload[0].payload
  const isBest  = d.date === bestDate
  const isWorst = d.date === worstDate
  return (
    <div className={`rounded-xl p-3 shadow-xl border text-xs font-mono ${
      isBest  ? 'bg-emerald-900 border-emerald-500 text-white' :
      isWorst ? 'bg-red-900 border-red-500 text-white' :
                'bg-farm-deep border-farm-mid text-white'
    }`}>
      <p className="font-bold">{d.date}
        {isBest  && <span className="ml-2 text-yellow-300">★ BEST SELL</span>}
        {isWorst && <span className="ml-2 text-red-300">✗ WORST</span>}
      </p>
      <p className="text-farm-light">{tr('rs')}{d.predicted_price_kg}{tr('kg')}</p>
      <p className={d.change_from_today >= 0 ? 'text-emerald-400' : 'text-red-400'}>
        {d.change_from_today >= 0 ? '+' : ''}{d.change_from_today}%
      </p>
      <RiskBadge level={d.recommendation} />
    </div>
  )
}

export default function Forecast({ tr }) {
  const [crops, setCrops]     = useState([])
  const [states, setStates]   = useState([])
  const [markets, setMarkets] = useState([])
  const [form, setForm] = useState({
    commodity: 'Tomato', market: '', state: 'Tamil Nadu',
    current_price: 45, horizon_days: 30
  })
  const [result, setResult]         = useState(null)
  const [loading, setLoading]       = useState(false)
  const [marketsLoading, setMarketsLoading] = useState(false)

  useEffect(() => {
    getCrops().then(r => setCrops(r.crops || []))
    getStates().then(r => {
      setStates(r.states || [])
      loadMarketsForState('Tamil Nadu')
    })
  }, [])

  const loadMarketsForState = (state) => {
    setMarketsLoading(true)
    setMarkets([])
    setForm(f => ({ ...f, market: '' }))
    getMarketsByState(state).then(r => {
      const mList = r.markets || []
      setMarkets(mList)
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
    setLoading(true)
    try {
      const res = await forecastPrices({
        commodity: form.commodity, market: form.market,
        state: form.state, current_price: +form.current_price,
        horizon_days: +form.horizon_days
      })
      setResult(res)
    } finally {
      setLoading(false)
    }
  }

  const chartData = result?.forecast
    ? (result.forecast.length > 30
        ? result.forecast.filter((_, i) => i % 3 === 0)
        : result.forecast)
    : []

  const s = result?.summary
  const bestDate  = s?.best_sell_date
  const worstDate = s?.worst_sell_date

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      <div className="mb-8">
        <p className="font-mono text-xs text-farm-bright uppercase tracking-widest mb-1">90-Day Forecast</p>
        <h1 className="font-syne font-bold text-3xl text-farm-deep lang-slide">{tr('forecast_title')}</h1>
        <p className="text-gray-500 mt-1 lang-slide">{tr('forecast_sub')}</p>
      </div>

      {/* Form */}
      <div className="bg-white rounded-2xl border border-gray-100 p-6 mb-6 shadow-sm">
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          {/* Crop */}
          <div>
            <label className="block font-mono text-xs text-gray-500 mb-1 lang-slide">{tr('predict_crop')}</label>
            <input list="fc-crops" value={form.commodity} onChange={e => set('commodity', e.target.value)}
              className="w-full border border-gray-200 rounded-xl px-3 py-2.5 font-mono text-sm focus:outline-none focus:ring-2 focus:ring-farm-bright" />
            <datalist id="fc-crops">{crops.map(c => <option key={c} value={c} />)}</datalist>
          </div>

          {/* State */}
          <div>
            <label className="block font-mono text-xs text-gray-500 mb-1 lang-slide">{tr('predict_state')}</label>
            <select value={form.state} onChange={e => set('state', e.target.value)}
              className="w-full border border-gray-200 rounded-xl px-3 py-2.5 font-mono text-sm focus:outline-none focus:ring-2 focus:ring-farm-bright bg-white">
              {states.length > 0
                ? states.map(s => <option key={s}>{s}</option>)
                : <option value="Tamil Nadu">Tamil Nadu</option>
              }
            </select>
          </div>

          {/* Market — filtered by state */}
          <div>
            <label className="block font-mono text-xs text-gray-500 mb-1 lang-slide">
              {tr('predict_market')}{marketsLoading && <span className="ml-1 text-farm-bright">…</span>}
            </label>
            <select value={form.market} onChange={e => set('market', e.target.value)}
              disabled={marketsLoading || markets.length === 0}
              className="w-full border border-gray-200 rounded-xl px-3 py-2.5 font-mono text-sm focus:outline-none focus:ring-2 focus:ring-farm-bright bg-white disabled:opacity-50">
              {marketsLoading ? <option>Loading...</option>
                : markets.length === 0 ? <option>No markets</option>
                : markets.map(m => <option key={m} value={m}>{m}</option>)}
            </select>
          </div>

          {/* Price */}
          <div>
            <label className="block font-mono text-xs text-gray-500 mb-1 lang-slide">{tr('predict_price')}</label>
            <input type="number" value={form.current_price} onChange={e => set('current_price', e.target.value)}
              className="w-full border border-gray-200 rounded-xl px-3 py-2.5 font-mono text-sm focus:outline-none focus:ring-2 focus:ring-farm-bright" />
          </div>

          {/* Horizon */}
          <div>
            <label className="block font-mono text-xs text-gray-500 mb-1 lang-slide">{tr('forecast_days')}</label>
            <select value={form.horizon_days} onChange={e => set('horizon_days', +e.target.value)}
              className="w-full border border-gray-200 rounded-xl px-3 py-2.5 font-mono text-sm focus:outline-none focus:ring-2 focus:ring-farm-bright bg-white">
              {[7,14,21,30,45,60,90].map(d => <option key={d} value={d}>{d} days</option>)}
            </select>
          </div>
        </div>
        <button onClick={submit} disabled={loading || marketsLoading}
          className="mt-4 bg-farm-deep text-white font-syne font-bold px-8 py-3 rounded-xl hover:bg-farm-mid transition-colors disabled:opacity-60 flex items-center gap-2">
          {loading ? <><Loader2 size={18} className="animate-spin" /> {tr('forecast_loading')}</> : <><BarChart3 size={18} /> {tr('forecast_btn')}</>}
        </button>
      </div>

      {/* Results */}
      {result && (
        <>
          {result._demo && (
            <div className="bg-orange-50 border border-orange-200 rounded-xl px-4 py-2 mb-4 font-mono text-xs text-orange-700">
              {tr('api_offline')}
            </div>
          )}

          {/* Summary cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            {/* Best sell */}
            <div className="farm-card rounded-2xl border-2 border-emerald-400 bg-emerald-50 p-4">
              <Star size={18} className="mb-2 text-emerald-600" />
              <p className="font-mono text-xs text-gray-500 mb-1 lang-slide">{tr('forecast_best')}</p>
              <p className="font-syne font-bold text-farm-deep">{s.best_sell_date}</p>
              <p className="font-mono text-xs text-emerald-700 font-semibold">{tr('rs')}{s.best_sell_price_kg}{tr('kg')}</p>
            </div>
            {/* Worst sell */}
            <div className="farm-card rounded-2xl border-2 border-red-300 bg-red-50 p-4">
              <AlertOctagon size={18} className="mb-2 text-red-500" />
              <p className="font-mono text-xs text-gray-500 mb-1 lang-slide">{tr('forecast_worst')}</p>
              <p className="font-syne font-bold text-farm-deep">{s.worst_sell_date || '—'}</p>
              <p className="font-mono text-xs text-red-600 font-semibold">
                {s.worst_sell_price_kg ? `${tr('rs')}${s.worst_sell_price_kg}${tr('kg')}` : 'Avoid selling'}
              </p>
            </div>
            {/* Gain */}
            <div className="farm-card rounded-2xl border border-sky-200 bg-sky-50 p-4">
              <TrendingUp size={18} className="mb-2 text-sky-600" />
              <p className="font-mono text-xs text-gray-500 mb-1 lang-slide">{tr('forecast_gain')}</p>
              <p className="font-syne font-bold text-farm-deep">
                {s.potential_gain_pct > 0 ? '+' : ''}{s.potential_gain_pct}%
              </p>
              <p className="font-mono text-xs text-gray-400">vs today</p>
            </div>
            {/* Avg */}
            <div className="farm-card rounded-2xl border border-yellow-200 bg-yellow-50 p-4">
              <BarChart3 size={18} className="mb-2 text-yellow-600" />
              <p className="font-mono text-xs text-gray-500 mb-1 lang-slide">{tr('forecast_avg')}</p>
              <p className="font-syne font-bold text-farm-deep">{tr('rs')}{s.avg_price_kg}{tr('kg')}</p>
              <p className="font-mono text-xs text-gray-400">{s.min_price_kg}–{s.max_price_kg} range</p>
            </div>
          </div>

          {/* Chart */}
          <div className="bg-white rounded-2xl border border-gray-100 p-6 shadow-sm mb-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-syne font-bold text-farm-deep lang-slide">
                {form.commodity} — {form.horizon_days}-Day Price Forecast
              </h3>
              <div className="flex items-center gap-4 font-mono text-xs text-gray-500">
                <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-full bg-emerald-400 inline-block"/>Best sell</span>
                <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-full bg-red-400 inline-block"/>Avoid</span>
              </div>
            </div>
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={chartData} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
                <defs>
                  <linearGradient id="priceGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%"  stopColor="#40916c" stopOpacity={0.25} />
                    <stop offset="95%" stopColor="#40916c" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="day" tick={{ fontFamily: 'DM Mono', fontSize: 10 }}
                  label={{ value: tr('chart_day'), position: 'insideBottom', offset: -2, fontFamily: 'DM Mono', fontSize: 10 }} />
                <YAxis tick={{ fontFamily: 'DM Mono', fontSize: 10 }}
                  label={{ value: tr('chart_price'), angle: -90, position: 'insideLeft', fontFamily: 'DM Mono', fontSize: 10 }} />
                <Tooltip content={<CustomTooltip tr={tr} bestDate={bestDate} worstDate={worstDate} />} />
                <ReferenceLine y={+form.current_price} stroke="#f4a261" strokeDasharray="5 5"
                  label={{ value: 'Today', fontFamily: 'DM Mono', fontSize: 10, fill: '#f4a261' }} />
                <Area type="monotone" dataKey="predicted_price_kg" stroke="#40916c" strokeWidth={2.5}
                  fill="url(#priceGrad)" dot={false} />
              </AreaChart>
            </ResponsiveContainer>
          </div>

          {/* Day-by-day table (first 14 days) */}
          <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-100">
              <h3 className="font-syne font-bold text-farm-deep">Day-by-Day Forecast (first 14 days)</h3>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full font-mono text-sm">
                <thead className="bg-gray-50">
                  <tr>
                    {['Day', 'Date', 'Price (Rs/kg)', 'Per Quintal', 'Change', 'Action'].map(h => (
                      <th key={h} className="text-left px-4 py-3 text-xs text-gray-500 uppercase tracking-wider">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {result.forecast.slice(0, 14).map(d => {
                    const isBest  = d.date === bestDate
                    const isWorst = d.date === worstDate
                    return (
                      <tr key={d.day} className={`border-t border-gray-50 transition-colors ${
                        isBest  ? 'bg-emerald-50' :
                        isWorst ? 'bg-red-50' :
                                  'hover:bg-gray-50/50'
                      }`}>
                        <td className="px-4 py-3 text-gray-400">D{d.day}</td>
                        <td className="px-4 py-3 text-farm-deep font-medium">
                          {d.date}
                          {isBest  && <span className="ml-2 text-xs bg-emerald-100 text-emerald-700 px-1.5 py-0.5 rounded-full">★ Best</span>}
                          {isWorst && <span className="ml-2 text-xs bg-red-100 text-red-700 px-1.5 py-0.5 rounded-full">✗ Worst</span>}
                        </td>
                        <td className="px-4 py-3 text-farm-deep font-semibold">{tr('rs')}{d.predicted_price_kg}</td>
                        <td className="px-4 py-3 text-gray-500">{tr('rs')}{d.predicted_price_quintal}</td>
                        <td className={`px-4 py-3 font-medium ${d.change_from_today >= 0 ? 'text-emerald-600' : 'text-red-600'}`}>
                          {d.change_from_today >= 0 ? '+' : ''}{d.change_from_today}%
                        </td>
                        <td className="px-4 py-3"><RiskBadge level={d.recommendation} tr={tr} /></td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
