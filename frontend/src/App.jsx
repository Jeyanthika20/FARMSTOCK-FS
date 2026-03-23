/**
 * App.jsx — FarmStock Root Component
 * Wires: Navbar, AlertBanner, page routing, enhanced footer
 * CHANGES:
 *   - Removed PriceTicker (live scrolling price bar)
 *   - Removed API status banner (removed from Home too)
 *   - Enhanced professional footer with 3-column layout (Tech Stack removed)
 *   - Footer is fully bilingual (English + Tamil) based on lang toggle
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

  const footerFeatureLinks = [
    { icon: TrendingUp, labelKey: 'nav_predict',  page: 'predict' },
    { icon: BarChart3,  labelKey: 'nav_forecast', page: 'forecast' },
    { icon: Shield,     labelKey: 'nav_health',   page: 'health' },
    { icon: Bell,       labelKey: 'nav_alerts',   page: 'alerts' },
  ]

  const platformFeatures = lang === 'ta' ? [
    '224 பயிர்கள் மற்றும் 1,289 சந்தைகள்',
    'RandomForest ML விலை கணிப்பு',
    'AI நோய் ஆலோசனை',
    '90 நாள் விலை முன்னறிவிப்பு',
    'இருமொழி (ஆங்கிலம் + தமிழ்)',
    'நேரடி WebSocket எச்சரிக்கைகள்',
  ] : [
    '224 crops across 1,289 markets',
    'RandomForest ML price prediction',
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

      {/* ── Enhanced Footer (Bilingual, No Tech Stack) ──────────────────────────────────── */}
      <footer className="bg-farm-deep text-white mt-16">

        {/* Top section — 3 columns */}
        <div className="max-w-6xl mx-auto px-4 py-12 grid grid-cols-1 md:grid-cols-3 gap-10">

          {/* ── Column 1: Brand + Contact ── */}
          <div className="md:col-span-1">
            <div className="flex items-center gap-2 mb-3">
              <div className="w-8 h-8 bg-farm-bright rounded-lg flex items-center justify-center">
                <Leaf size={16} className="text-white" />
              </div>
              <span className="font-syne font-extrabold text-xl text-white">
                {lang === 'ta' ? 'விவசாய பங்கு' : 'FarmStock'}
              </span>
            </div>
            <p className="font-mono text-xs text-white/60 leading-relaxed mb-2">
              {tr('footer_brand_desc')}
            </p>
            {lang === 'en' && (
              <p className="font-mono text-xs text-farm-light/70 leading-relaxed">
                இந்திய விவசாயிகளுக்கான ML விலை அறிவு
              </p>
            )}
            <div className="mt-5 pt-4 border-t border-white/10 space-y-2">
              <a
                href="mailto:farmstock@example.com"
                className="flex items-center gap-2 font-mono text-xs text-white/50 hover:text-farm-light transition-colors"
              >
                <Mail size={11} /> farmstock@example.com
              </a>
              <a
                href="tel:+911800000000"
                className="flex items-center gap-2 font-mono text-xs text-white/50 hover:text-farm-light transition-colors"
              >
                <Phone size={11} /> 1800-000-0000 ({lang === 'ta' ? 'உதவி மையம்' : 'Helpline'})
              </a>
            </div>
          </div>

          {/* ── Column 2: Features / Quick Links ── */}
          <div>
            <p className="font-syne font-bold text-white/90 mb-4 text-sm tracking-wide uppercase">
              {tr('footer_features')}
            </p>
            <ul className="space-y-2.5">
              {footerFeatureLinks.map(({ icon: Icon, labelKey, page: pg }) => (
                <li key={pg}>
                  <button
                    onClick={() => setPage(pg)}
                    className="flex items-center gap-2 font-mono text-xs text-white/60 hover:text-farm-light transition-colors group"
                  >
                    <Icon size={12} className="group-hover:text-farm-bright transition-colors" />
                    {tr(labelKey)}
                  </button>
                </li>
              ))}
            </ul>
          </div>

          {/* ── Column 3: Platform ── */}
          <div>
            <p className="font-syne font-bold text-white/90 mb-4 text-sm tracking-wide uppercase">
              {tr('footer_platform')}
            </p>
            <ul className="space-y-2">
              {platformFeatures.map(f => (
                <li key={f} className="flex items-start gap-2 font-mono text-xs text-white/60">
                  <span className="text-farm-bright mt-0.5">›</span>
                  {f}
                </li>
              ))}
            </ul>
          </div>

        </div>

        {/* Divider */}
        <div className="border-t border-white/10" />

        {/* Bottom bar */}
        <div className="max-w-6xl mx-auto px-4 py-5 flex flex-col md:flex-row items-center justify-between gap-3">
          <p className="font-mono text-xs text-white/30">
            {tr('footer_copyright')}
          </p>
          <p className="font-mono text-xs text-white/20">
            {tr('footer_disclaimer')}
          </p>
        </div>

      </footer>
    </div>
  )
}
