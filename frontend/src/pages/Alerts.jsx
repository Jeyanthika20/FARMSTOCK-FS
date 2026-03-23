/**
 * Alerts.jsx — Real-Time Alerts & Notification Registration Page
 * Features: Live WebSocket alert feed, bilingual titles/messages,
 *           category filter tabs, notification preference registration
 */
import { useState } from 'react'
import { Wifi, WifiOff, Bell, AlertTriangle, TrendingUp, Sprout, CheckCircle } from 'lucide-react'
import { useWebSocket } from '../hooks/useWebSocket'
import RiskBadge from '../components/RiskBadge'
import { registerNotifications } from '../utils/api'

const ICONS = { disease: AlertTriangle, market: TrendingUp, planting: Sprout }
const SEV_COLORS = {
  CRITICAL: 'border-l-red-500 bg-red-50/50',
  HIGH:     'border-l-orange-500 bg-orange-50/50',
  MEDIUM:   'border-l-yellow-500 bg-yellow-50/50',
  LOW:      'border-l-emerald-500 bg-emerald-50/50',
}

function AlertCard({ alert, lang }) {
  const Icon = ICONS[alert.category] || Bell
  const title   = lang === 'ta' ? (alert.title_ta   || alert.title)   : alert.title
  const message = lang === 'ta' ? (alert.message_ta || alert.message) : alert.message
  const ts = alert.timestamp ? new Date(alert.timestamp).toLocaleTimeString() : ''

  return (
    <div className={`bg-white rounded-2xl border border-gray-100 border-l-4 ${SEV_COLORS[alert.severity]} p-5 farm-card`}>
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-start gap-3 flex-1">
          <div className="w-9 h-9 bg-gray-100 rounded-xl flex items-center justify-center shrink-0">
            <Icon size={16} className="text-gray-600" />
          </div>
          <div>
            <div className="flex items-center gap-2 mb-1 flex-wrap">
              <RiskBadge level={alert.severity} />
              <span className="font-mono text-xs text-gray-400 capitalize">{alert.category}</span>
            </div>
            <h4 className="font-syne font-bold text-farm-deep text-sm mb-1 lang-slide">{title}</h4>
            <p className="text-xs text-gray-600 leading-relaxed lang-slide">{message}</p>
          </div>
        </div>
        <span className="font-mono text-xs text-gray-300 shrink-0">{ts}</span>
      </div>
    </div>
  )
}

export default function Alerts({ tr, lang }) {
  const { messages, connected } = useWebSocket('/ws/alerts')
  const [filter, setFilter] = useState('all')
  const [notifForm, setNotifForm] = useState({
    user_id: `farmer_${Date.now()}`, crops: 'Tomato, Onion',
    markets: 'Coimbatore, Chennai', language: lang,
  })
  const [notifResult, setNotifResult] = useState(null)

  const alerts = messages
    .filter(m => m.type === 'alert')
    .map(m => m.data)
    .filter(a => filter === 'all' || a.category === filter)

  const tabs = [
    { key: 'all',      label: tr('alerts_all') },
    { key: 'disease',  label: tr('alerts_disease') },
    { key: 'market',   label: tr('alerts_market') },
    { key: 'planting', label: tr('alerts_planting') },
  ]

  const registerNotif = async () => {
    const res = await registerNotifications({
      user_id:  notifForm.user_id,
      crops:    notifForm.crops.split(',').map(s => s.trim()),
      markets:  notifForm.markets.split(',').map(s => s.trim()),
      language: notifForm.language,
      alert_types: ['disease', 'market', 'planting']
    })
    setNotifResult(res)
  }

  return (
    <div className="max-w-5xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex items-start justify-between mb-8 flex-wrap gap-4">
        <div>
          <p className="font-mono text-xs text-farm-bright uppercase tracking-widest mb-1">{tr('alerts_tagline')}</p>
          <h1 className="font-syne font-bold text-3xl text-farm-deep lang-slide">{tr('alerts_title')}</h1>
          <p className="text-gray-500 mt-1 lang-slide">{tr('alerts_sub')}</p>
        </div>
        <div className="flex items-center gap-2 px-4 py-2 rounded-xl bg-white border border-gray-100 shadow-sm">
          <span className={`w-2.5 h-2.5 rounded-full ${connected ? 'bg-emerald-500 live-dot' : 'bg-red-400'}`} />
          {connected ? <Wifi size={14} className="text-emerald-600" /> : <WifiOff size={14} className="text-red-500" />}
          <span className="font-mono text-xs text-gray-600">
            {connected ? tr('alerts_live') : 'Reconnecting...'}
          </span>
        </div>
      </div>

      <div className="grid md:grid-cols-3 gap-6">
        {/* Alert feed */}
        <div className="md:col-span-2">
          {/* Filter tabs */}
          <div className="flex gap-2 mb-4">
            {tabs.map(t => (
              <button
                key={t.key}
                onClick={() => setFilter(t.key)}
                className={`px-4 py-1.5 rounded-lg font-mono text-xs transition-colors ${
                  filter === t.key
                    ? 'bg-farm-deep text-white'
                    : 'bg-white border border-gray-200 text-gray-600 hover:bg-gray-50'
                }`}
              >
                {t.label}
              </button>
            ))}
          </div>

          {/* Alert list */}
          <div className="space-y-3 max-h-[600px] overflow-y-auto scrollbar-hide">
            {alerts.length === 0 ? (
              <div className="bg-white rounded-2xl border border-gray-100 p-12 text-center">
                <div className="w-12 h-12 bg-farm-pale rounded-full flex items-center justify-center mx-auto mb-3">
                  <Bell size={20} className="text-farm-mid" />
                </div>
                <p className="font-syne font-semibold text-farm-deep lang-slide">{tr('alerts_empty')}</p>
                <p className="font-mono text-xs text-gray-400 mt-1">
                  {connected ? 'Waiting for next alert...' : 'Connecting to server...'}
                </p>
              </div>
            ) : (
              alerts.map((alert, i) => (
                <AlertCard key={`${alert.id}-${i}`} alert={alert} lang={lang} />
              ))
            )}
          </div>
        </div>

        {/* Notification registration */}
        <div className="bg-white rounded-2xl border border-gray-100 p-5 shadow-sm h-fit">
          <div className="flex items-center gap-2 mb-4">
            <Bell size={16} className="text-farm-bright" />
            <h3 className="font-syne font-bold text-farm-deep lang-slide">{tr('notif_register')}</h3>
          </div>

          <div className="space-y-3">
            <div>
              <label className="block font-mono text-xs text-gray-500 mb-1 lang-slide">{tr('notif_crops')}</label>
              <input value={notifForm.crops}
                onChange={e => setNotifForm(f => ({ ...f, crops: e.target.value }))}
                className="w-full border border-gray-200 rounded-xl px-3 py-2 font-mono text-xs focus:outline-none focus:ring-2 focus:ring-farm-bright"
                placeholder="Tomato, Onion, Potato" />
            </div>
            <div>
              <label className="block font-mono text-xs text-gray-500 mb-1 lang-slide">{tr('notif_markets')}</label>
              <input value={notifForm.markets}
                onChange={e => setNotifForm(f => ({ ...f, markets: e.target.value }))}
                className="w-full border border-gray-200 rounded-xl px-3 py-2 font-mono text-xs focus:outline-none focus:ring-2 focus:ring-farm-bright"
                placeholder="Coimbatore, Chennai" />
            </div>
            <div>
              <label className="block font-mono text-xs text-gray-500 mb-1 lang-slide">{tr('notif_lang')}</label>
              <select value={notifForm.language}
                onChange={e => setNotifForm(f => ({ ...f, language: e.target.value }))}
                className="w-full border border-gray-200 rounded-xl px-3 py-2 font-mono text-xs bg-white focus:outline-none focus:ring-2 focus:ring-farm-bright">
                <option value="en">English</option>
                <option value="ta">தமிழ் (Tamil)</option>
              </select>
            </div>

            {notifResult ? (
              <div className="flex items-center gap-2 bg-emerald-50 border border-emerald-200 rounded-xl px-3 py-2">
                <CheckCircle size={14} className="text-emerald-600" />
                <span className="font-mono text-xs text-emerald-700 lang-slide">{tr('notif_success')}</span>
              </div>
            ) : (
              <button onClick={registerNotif}
                className="w-full bg-farm-deep text-white font-syne font-bold py-2.5 rounded-xl hover:bg-farm-mid transition-colors text-sm lang-slide">
                {tr('notif_btn')}
              </button>
            )}
          </div>

          {/* Stats */}
          <div className="mt-5 pt-4 border-t border-gray-100">
            <p className="font-mono text-xs text-gray-400 mb-2">Alert Summary</p>
            {['CRITICAL','HIGH','MEDIUM','LOW'].map(level => {
              const count = messages.filter(m => m.type === 'alert' && m.data?.severity === level).length
              return (
                <div key={level} className="flex justify-between items-center py-1">
                  <RiskBadge level={level} tr={tr} />
                  <span className="font-mono text-xs text-gray-500">{count}</span>
                </div>
              )
            })}
          </div>
        </div>
      </div>
    </div>
  )
}
