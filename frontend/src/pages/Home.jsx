/**
 * Home.jsx — FarmStock Landing/Home Page
 * Sections: Hero banner, Live stats, Info slides carousel, Quick actions
 */
import { useEffect, useState } from 'react'
import { TrendingUp, Shield, BarChart3, ArrowRight, Leaf } from 'lucide-react'
import InfoSlides from '../components/InfoSlides'

export default function Home({ tr, lang, setPage }) {

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      {/* ── Hero ─────────────────────────────────────────────── */}
      <div className="relative bg-farm-deep rounded-3xl overflow-hidden mb-8 p-8 md:p-12">
        {/* Decorative blobs */}
        <div className="absolute top-0 right-0 w-72 h-72 rounded-full opacity-10"
             style={{ background: 'radial-gradient(circle, #74c69d 0%, transparent 70%)', transform: 'translate(30%, -30%)' }} />
        <div className="absolute bottom-0 left-1/4 w-48 h-48 rounded-full opacity-10"
             style={{ background: 'radial-gradient(circle, #f4a261 0%, transparent 70%)', transform: 'translateY(30%)' }} />

        <div className="relative z-10">
          <div className="inline-flex items-center gap-2 bg-farm-light/20 border border-farm-light/30 rounded-full px-4 py-1.5 mb-6">
            <span className="w-2 h-2 rounded-full bg-farm-light live-dot" />
            <span className="font-mono text-xs text-farm-light tracking-widest uppercase lang-slide">
              {tr('hero_badge')}
            </span>
          </div>

          <h1 className="font-syne font-extrabold text-white text-4xl md:text-6xl leading-tight mb-4">
            <span className="lang-slide block">{tr('hero_title')}</span>
            <span className="text-farm-light lang-slide block">{tr('hero_title2')}</span>
          </h1>

          <p className="text-white/70 text-lg max-w-xl mb-8 leading-relaxed lang-slide">
            {tr('hero_sub')}
          </p>

          <div className="flex flex-wrap gap-4">
            <button
              onClick={() => setPage('predict')}
              className="inline-flex items-center gap-2 bg-farm-gold text-farm-deep font-syne font-bold px-6 py-3 rounded-xl hover:bg-farm-gold/90 transition-colors"
            >
              <TrendingUp size={18} />
              <span className="lang-slide">{tr('hero_cta')}</span>
            </button>
            <button
              onClick={() => setPage('forecast')}
              className="inline-flex items-center gap-2 bg-white/10 text-white border border-white/20 font-syne font-semibold px-6 py-3 rounded-xl hover:bg-white/20 transition-colors"
            >
              <BarChart3 size={18} />
              <span className="lang-slide">{tr('hero_cta2')}</span>
            </button>
          </div>
        </div>
      </div>

      {/* ── Stats row ────────────────────────────────────────── */}
      <div className="grid grid-cols-3 gap-4 mb-8">
        {[
          { icon: Leaf,       stat: tr('hero_stat1'), color: 'bg-farm-pale text-farm-deep' },
          { icon: BarChart3,  stat: tr('hero_stat2'), color: 'bg-yellow-50 text-yellow-800' },
          { icon: Shield,     stat: tr('hero_stat3'), color: 'bg-sky-50 text-sky-800' },
        ].map(({ icon: Icon, stat, color }, i) => (
          <div key={i} className={`farm-card rounded-2xl p-4 md:p-6 text-center border border-transparent ${color}`}>
            <Icon size={24} className="mx-auto mb-2 opacity-70" />
            <p className="font-syne font-bold text-sm md:text-lg lang-slide">{stat}</p>
          </div>
        ))}
      </div>

      {/* ── Info slides + Quick actions ───────────────────────── */}
      <div className="grid md:grid-cols-2 gap-6 mb-8">
        <InfoSlides tr={tr} lang={lang} />

        {/* Quick action cards */}
        <div className="flex flex-col gap-4">
          {[
            { icon: TrendingUp, label: tr('nav_predict'), sub: tr('predict_sub'), page: 'predict', color: 'border-farm-bright' },
            { icon: BarChart3,  label: tr('nav_forecast'),label2: tr('forecast_sub'), page: 'forecast', color: 'border-farm-gold' },
            { icon: Shield,     label: tr('nav_health'),  label2: tr('health_sub'),   page: 'health',  color: 'border-farm-sky' },
          ].map(({ icon: Icon, label, sub, label2, page: pg, color }) => (
            <button
              key={pg}
              onClick={() => setPage(pg)}
              className={`farm-card text-left bg-white rounded-2xl p-4 border-l-4 ${color} border border-gray-100 w-full`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 bg-farm-pale rounded-lg flex items-center justify-center">
                    <Icon size={18} className="text-farm-deep" />
                  </div>
                  <div className="text-left">
                    <p className="font-syne font-bold text-farm-deep text-sm lang-slide">{label}</p>
                    <p className="text-xs text-gray-500 lang-slide">{sub || label2}</p>
                  </div>
                </div>
                <ArrowRight size={16} className="text-farm-bright" />
              </div>
            </button>
          ))}
        </div>
      </div>

    </div>
  )
}
