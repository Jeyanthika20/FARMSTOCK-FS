/**
 * AlertBanner.jsx — Real-time alert toast notifications
 * Subscribes to /ws/alerts WebSocket.
 * Shows bilingual alert toast at top-right, auto-dismisses after 8s.
 */
import { useEffect, useState } from 'react'
import { X, AlertTriangle, TrendingUp, Sprout, Wifi } from 'lucide-react'
import { useWebSocket } from '../hooks/useWebSocket'

const ICONS = {
  disease: AlertTriangle,
  market:  TrendingUp,
  planting: Sprout,
}

const COLORS = {
  CRITICAL: 'border-red-500 bg-red-50',
  HIGH:     'border-orange-500 bg-orange-50',
  MEDIUM:   'border-yellow-500 bg-yellow-50',
  LOW:      'border-emerald-500 bg-emerald-50',
}

const DOT_COLORS = {
  CRITICAL: 'bg-red-500', HIGH: 'bg-orange-500', MEDIUM: 'bg-yellow-500', LOW: 'bg-emerald-500'
}

export default function AlertBanner({ lang }) {
  const { lastMessage } = useWebSocket('/ws/alerts')
  const [toasts, setToasts] = useState([])

  useEffect(() => {
    if (!lastMessage || lastMessage.type !== 'alert') return
    const alert = lastMessage.data
    const id = Date.now()
    setToasts(prev => [...prev.slice(-2), { ...alert, id }])

    // Auto-dismiss after 8s
    setTimeout(() => {
      setToasts(prev => prev.filter(t => t.id !== id))
    }, 8000)
  }, [lastMessage])

  const dismiss = (id) => setToasts(prev => prev.filter(t => t.id !== id))

  if (toasts.length === 0) return null

  return (
    <div className="fixed top-20 right-4 z-50 flex flex-col gap-2 max-w-sm w-full">
      {toasts.map(toast => {
        const Icon = ICONS[toast.category] || AlertTriangle
        const title   = lang === 'ta' ? (toast.title_ta   || toast.title)   : toast.title
        const message = lang === 'ta' ? (toast.message_ta || toast.message) : toast.message

        return (
          <div
            key={toast.id}
            className={`farm-card border-l-4 rounded-xl p-4 shadow-xl bg-white ${COLORS[toast.severity]} animate-in slide-in-from-right`}
          >
            <div className="flex items-start gap-3">
              <div className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 ${DOT_COLORS[toast.severity]} bg-opacity-15`}>
                <Icon size={16} className={toast.severity === 'CRITICAL' ? 'text-red-600' : toast.severity === 'HIGH' ? 'text-orange-600' : 'text-yellow-600'} />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <span className={`inline-block w-2 h-2 rounded-full ${DOT_COLORS[toast.severity]}`} />
                  <span className="font-mono text-xs font-medium text-gray-500 uppercase tracking-wider">{toast.severity}</span>
                </div>
                <p className="font-syne font-semibold text-farm-deep text-sm leading-tight mb-1 lang-slide">{title}</p>
                <p className="text-xs text-gray-600 leading-relaxed lang-slide">{message}</p>
              </div>
              <button onClick={() => dismiss(toast.id)} className="text-gray-400 hover:text-gray-600 shrink-0">
                <X size={14} />
              </button>
            </div>
          </div>
        )
      })}
    </div>
  )
}
