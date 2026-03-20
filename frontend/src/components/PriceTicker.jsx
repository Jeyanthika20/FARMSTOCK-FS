/**
 * PriceTicker.jsx — Real-time scrolling price ticker
 * Uses WebSocket /ws/prices for live data.
 * Shows: Crop name, price Rs/kg, change %, trend arrow
 */
import { TrendingUp, TrendingDown, Minus, Wifi, WifiOff } from 'lucide-react'
import { useWebSocket } from '../hooks/useWebSocket'

function TickerItem({ item, tr }) {
  const up = item.trend === 'up'
  const neutral = Math.abs(item.change_pct) < 0.5
  return (
    <span className="inline-flex items-center gap-2 px-5 border-r border-farm-mid/50 shrink-0">
      <span className="font-syne font-semibold text-white text-sm">{item.crop}</span>
      <span className="font-mono text-farm-light font-medium">
        {tr('rs')}{item.price_kg}{tr('kg')}
      </span>
      <span className={`inline-flex items-center gap-0.5 font-mono text-xs ${
        neutral ? 'text-white/50' : up ? 'text-emerald-400' : 'text-red-400'
      }`}>
        {neutral ? <Minus size={10} /> : up ? <TrendingUp size={10} /> : <TrendingDown size={10} />}
        {item.change_pct > 0 ? '+' : ''}{item.change_pct}%
      </span>
    </span>
  )
}

export default function PriceTicker({ tr }) {
  const { lastMessage, connected } = useWebSocket('/ws/prices')

  const items = lastMessage?.type === 'price_update' ? lastMessage.data : [
    { crop:'Tomato', market:'Coimbatore', price_kg:45.00, change_pct:0, trend:'up', price_quintal:4500 },
    { crop:'Onion',  market:'Chennai',    price_kg:32.00, change_pct:0, trend:'up', price_quintal:3200 },
    { crop:'Potato', market:'Salem',      price_kg:28.00, change_pct:0, trend:'up', price_quintal:2800 },
    { crop:'Rice',   market:'Madurai',    price_kg:55.00, change_pct:0, trend:'up', price_quintal:5500 },
    { crop:'Wheat',  market:'Trichy',     price_kg:38.00, change_pct:0, trend:'up', price_quintal:3800 },
  ]

  return (
    <div className="bg-farm-deep border-b border-farm-mid overflow-hidden">
      <div className="flex items-center">
        {/* Label */}
        <div className="flex items-center gap-2 px-4 py-2 bg-farm-gold/20 border-r border-farm-gold/30 shrink-0">
          <span className={`w-2 h-2 rounded-full ${connected ? 'bg-emerald-400 live-dot' : 'bg-red-400'}`} />
          <span className="font-mono text-xs font-medium text-farm-gold tracking-widest">
            {tr('ticker_label')}
          </span>
          {connected
            ? <Wifi size={12} className="text-emerald-400" />
            : <WifiOff size={12} className="text-red-400" />
          }
        </div>

        {/* Scrolling items — doubled for seamless loop */}
        <div className="flex-1 overflow-hidden">
          <div className="ticker-inner flex whitespace-nowrap py-2">
            {[...items, ...items].map((item, i) => (
              <TickerItem key={i} item={item} tr={tr} />
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
