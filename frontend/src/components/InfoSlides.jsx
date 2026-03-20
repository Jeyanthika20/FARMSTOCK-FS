/**
 * InfoSlides.jsx — Bilingual farmer education carousel
 * Slides auto-advance every 5s. Touch/click navigation.
 * Content switches between English and Tamil via lang prop.
 */
import { useState, useEffect } from 'react'
import { ChevronLeft, ChevronRight, Brain, Zap, Shield, Calendar } from 'lucide-react'

const SLIDE_DATA = [
  { key: 1, icon: Brain,    color: 'bg-farm-pale text-farm-deep',   accent: '#40916c' },
  { key: 2, icon: Zap,     color: 'bg-yellow-50 text-yellow-800',  accent: '#f4a261' },
  { key: 3, icon: Shield,  color: 'bg-red-50 text-red-800',        accent: '#e76f51' },
  { key: 4, icon: Calendar,color: 'bg-sky-50 text-sky-800',        accent: '#4cc9f0' },
]

export default function InfoSlides({ tr, lang }) {
  const [active, setActive] = useState(0)

  useEffect(() => {
    const t = setInterval(() => setActive(prev => (prev + 1) % 4), 5000)
    return () => clearInterval(t)
  }, [])

  const prev = () => setActive(p => (p - 1 + 4) % 4)
  const next = () => setActive(p => (p + 1) % 4)

  const slide = SLIDE_DATA[active]
  const Icon = slide.icon

  return (
    <div className="bg-farm-deep rounded-2xl overflow-hidden relative select-none">
      {/* Slide content */}
      <div className={`p-8 min-h-48 transition-all duration-500 ${slide.color}`} key={`${active}-${lang}`}>
        <div className="flex items-start gap-4">
          <div className="w-12 h-12 rounded-2xl flex items-center justify-center shrink-0"
               style={{ background: slide.accent + '22', border: `1px solid ${slide.accent}44` }}>
            <Icon size={24} style={{ color: slide.accent }} />
          </div>
          <div className="flex-1">
            <h3 className="font-syne font-bold text-xl mb-2 lang-slide">
              {tr(`slide${slide.key}_title`)}
            </h3>
            <p className="text-sm leading-relaxed opacity-80 lang-slide">
              {tr(`slide${slide.key}_body`)}
            </p>
          </div>
        </div>
      </div>

      {/* Controls */}
      <div className="flex items-center justify-between px-4 py-3 bg-farm-deep">
        <button onClick={prev} className="p-1 text-white/50 hover:text-white transition-colors">
          <ChevronLeft size={18} />
        </button>
        <div className="flex gap-2">
          {SLIDE_DATA.map((_, i) => (
            <button
              key={i}
              onClick={() => setActive(i)}
              className={`h-1.5 rounded-full transition-all ${i === active ? 'bg-farm-light w-6' : 'bg-white/30 w-1.5'}`}
            />
          ))}
        </div>
        <button onClick={next} className="p-1 text-white/50 hover:text-white transition-colors">
          <ChevronRight size={18} />
        </button>
      </div>
    </div>
  )
}
