/**
 * Navbar.jsx — Top navigation with language toggle
 * Features: Active page highlighting, mobile-responsive, bilingual toggle button
 */
import { useState } from 'react'
import { Menu, X, Leaf, Globe } from 'lucide-react'

export default function Navbar({ page, setPage, lang, toggleLang, tr }) {
  const [open, setOpen] = useState(false)

  const links = [
    { key: 'home',     label: tr('nav_home') },
    { key: 'predict',  label: tr('nav_predict') },
    { key: 'forecast', label: tr('nav_forecast') },
    { key: 'health',   label: tr('nav_health') },
    { key: 'alerts',   label: tr('nav_alerts') },
  ]

  const go = (k) => { setPage(k); setOpen(false) }

  return (
    <nav className="sticky top-0 z-50 bg-farm-deep border-b border-farm-mid shadow-lg">
      <div className="max-w-6xl mx-auto px-4 flex items-center justify-between h-16">
        {/* Logo */}
        <button onClick={() => go('home')} className="flex items-center gap-2 group">
          <div className="w-8 h-8 bg-farm-light rounded-lg flex items-center justify-center">
            <Leaf size={18} className="text-farm-deep" />
          </div>
          <div>
            <span className="font-syne font-bold text-white text-lg leading-none">{tr('nav_title')}</span>
            <p className="font-mono text-xs text-farm-light leading-none hidden sm:block">{tr('nav_tagline')}</p>
          </div>
        </button>

        {/* Desktop links */}
        <div className="hidden md:flex items-center gap-1">
          {links.map(l => (
            <button
              key={l.key}
              onClick={() => go(l.key)}
              className={`px-3 py-2 rounded-lg font-mono text-sm transition-colors ${
                page === l.key
                  ? 'bg-farm-light text-farm-deep font-medium'
                  : 'text-white/70 hover:text-white hover:bg-farm-mid'
              }`}
            >
              {l.label}
            </button>
          ))}
        </div>

        {/* Lang toggle + mobile menu */}
        <div className="flex items-center gap-2">
          <button
            onClick={toggleLang}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-farm-mid hover:bg-farm-bright rounded-lg font-mono text-sm text-white transition-colors"
            title={lang === 'en' ? 'Switch to Tamil' : 'Switch to English'}
          >
            <Globe size={14} />
            <span className="lang-slide">{lang === 'en' ? 'தமிழ்' : 'EN'}</span>
          </button>

          <button
            onClick={() => setOpen(!open)}
            className="md:hidden p-2 text-white/70 hover:text-white"
          >
            {open ? <X size={20} /> : <Menu size={20} />}
          </button>
        </div>
      </div>

      {/* Mobile drawer */}
      {open && (
        <div className="md:hidden bg-farm-mid border-t border-farm-bright px-4 py-3 flex flex-col gap-1">
          {links.map(l => (
            <button
              key={l.key}
              onClick={() => go(l.key)}
              className={`w-full text-left px-3 py-2 rounded-lg font-mono text-sm transition-colors ${
                page === l.key ? 'bg-farm-light text-farm-deep font-medium' : 'text-white/80 hover:bg-farm-deep'
              }`}
            >
              {l.label}
            </button>
          ))}
        </div>
      )}
    </nav>
  )
}
