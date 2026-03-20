/**
 * App.jsx — FarmStock Root Component
 * Wires: Navbar, AlertBanner, page routing, enhanced footer
 * CHANGES:
 *   - Removed PriceTicker (live scrolling price bar)
 *   - Removed API status banner (removed from Home too)
 *   - Enhanced professional footer with 4-column layout
 */
import { useState } from 'react'
import Navbar      from './components/Navbar'
import AlertBanner from './components/AlertBanner'
import Home        from './pages/Home'
import Predict     from './pages/Predict'
import Forecast    from './pages/Forecast'
import CropHealth  from './pages/CropHealth'
import Alerts      from './pages/Alerts'
import { useLang } from './hooks/useLang'
import { Leaf, TrendingUp, Shield, Bell, BarChart3, Mail, Phone } from 'lucide-react'

export default function App() {
  const [page, setPage] = useState('home')
  const { lang, toggleLang, tr } = useLang()

  const pages = {
    home:     <Home     tr={tr} lang={lang} setPage={setPage} />,
    predict:  <Predict  tr={tr} lang={lang} />,
    forecast: <Forecast tr={tr} lang={lang} />,
    health:   <CropHealth tr={tr} lang={lang} />,
    alerts:   <Alerts   tr={tr} lang={lang} />,
  }

  const footerLinks = [
    { icon: TrendingUp, label: 'Price Predict', page: 'predict' },
    { icon: BarChart3,  label: 'Forecast',      page: 'forecast' },
    { icon: Shield,     label: 'Crop Health',   page: 'health' },
    { icon: Bell,       label: 'Alerts',        page: 'alerts' },
  ]

  const features = [
    '224 crops across 1,289 markets',
    'XGBoost ML price prediction',
    'AI-powered disease advisory',
    '90-day price forecasting',
    'Bilingual (English + Tamil)',
    'Real-time WebSocket alerts',
  ]

  return (
    <div className="min-h-screen bg-farm-cream flex flex-col">
      <Navbar page={page} setPage={setPage} lang={lang} toggleLang={toggleLang} tr={tr} />
      <AlertBanner lang={lang} />
      <main className="flex-1">
        {pages[page] || pages.home}
      </main>

      {/* ── Enhanced Footer ──────────────────────────────────── */}
      <footer className="bg-farm-deep text-white mt-16">
        {/* Top section */}
        <div className="max-w-6xl mx-auto px-4 py-12 grid grid-cols-1 md:grid-cols-4 gap-10">

          {/* Brand column */}
          <div className="md:col-span-1">
            <div className="flex items-center gap-2 mb-3">
              <div className="w-8 h-8 bg-farm-bright rounded-lg flex items-center justify-center">
                <Leaf size={16} className="text-white" />
              </div>
              <span className="font-syne font-extrabold text-xl text-white">FarmStock</span>
            </div>
            <p className="font-mono text-xs text-white/60 leading-relaxed mb-2">
              ML-powered crop price intelligence for Indian farmers.
            </p>
            <p className="font-mono text-xs text-farm-light/70 leading-relaxed">
              இந்திய விவசாயிகளுக்கான ML விலை அறிவு
            </p>
            {/* <div className="mt-4 flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-emerald-400 live-dot" />
              <span className="font-mono text-xs text-emerald-400">v3.0 — Active</span>
            </div> */}
          </div>

          {/* Quick links */}
          <div>
            <p className="font-syne font-bold text-white/90 mb-4 text-sm tracking-wide uppercase">Features</p>
            <ul className="space-y-2.5">
              {footerLinks.map(({ icon: Icon, label, page: pg }) => (
                <li key={pg}>
                  <button
                    onClick={() => setPage(pg)}
                    className="flex items-center gap-2 font-mono text-xs text-white/60 hover:text-farm-light transition-colors group"
                  >
                    <Icon size={12} className="group-hover:text-farm-bright transition-colors" />
                    {label}
                  </button>
                </li>
              ))}
            </ul>
          </div>

          {/* Platform features */}
          <div>
            <p className="font-syne font-bold text-white/90 mb-4 text-sm tracking-wide uppercase">Platform</p>
            <ul className="space-y-2">
              {features.map(f => (
                <li key={f} className="flex items-start gap-2 font-mono text-xs text-white/60">
                  <span className="text-farm-bright mt-0.5">›</span>
                  {f}
                </li>
              ))}
            </ul>
          </div>

          {/* Tech stack + contact */}
          <div>
            <p className="font-syne font-bold text-white/90 mb-4 text-sm tracking-wide uppercase">Tech Stack</p>
            <div className="space-y-2 mb-6">
              {[
                ['Backend',  'FastAPI + XGBoost'],
                ['Frontend', 'React + Recharts'],
                ['ML',       'Scikit-learn + Pandas'],
                ['Realtime', 'WebSocket (ASGI)'],
                ['Data',     '5 Years Mandi Records'],
              ].map(([k, v]) => (
                <div key={k} className="flex items-center justify-between">
                  <span className="font-mono text-xs text-white/40">{k}</span>
                  <span className="font-mono text-xs text-farm-light/80">{v}</span>
                </div>
              ))}
            </div>
            <div className="space-y-2 pt-4 border-t border-white/10">
              <a href="mailto:farmstock@example.com"
                className="flex items-center gap-2 font-mono text-xs text-white/50 hover:text-farm-light transition-colors">
                <Mail size={11} /> farmstock@example.com
              </a>
              <a href="tel:+911800000000"
                className="flex items-center gap-2 font-mono text-xs text-white/50 hover:text-farm-light transition-colors">
                <Phone size={11} /> 1800-000-0000 (Helpline)
              </a>
            </div>
          </div>
        </div>

        {/* Divider */}
        <div className="border-t border-white/10" />

        {/* Bottom bar */}
        <div className="max-w-6xl mx-auto px-4 py-5 flex flex-col md:flex-row items-center justify-between gap-3">
          <p className="font-mono text-xs text-white/30">
            © 2025 FarmStock · Built for Indian farmers · Data source: AGMARKNET
          </p>
          <p className="font-mono text-xs text-white/20">
            Predictions are advisory only — not financial advice.
          </p>
        </div>
      </footer>
    </div>
  )
}
