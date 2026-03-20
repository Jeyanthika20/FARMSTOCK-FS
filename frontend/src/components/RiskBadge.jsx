/**
 * RiskBadge.jsx — Reusable risk/status badge component
 * Colors: CRITICAL=red, HIGH=orange, MEDIUM=yellow, LOW=green
 * Also handles: SELL/HOLD/NEUTRAL recommendations, GOOD TIME/CAUTION/AVOID plant advice
 */
export default function RiskBadge({ level, tr }) {
  const map = {
    CRITICAL:  { bg: 'bg-red-100',    text: 'text-red-700',    border: 'border-red-300',    label: tr ? tr('severity_critical') : 'CRITICAL' },
    HIGH:      { bg: 'bg-orange-100', text: 'text-orange-700', border: 'border-orange-300', label: tr ? tr('severity_high')     : 'HIGH' },
    MEDIUM:    { bg: 'bg-yellow-100', text: 'text-yellow-700', border: 'border-yellow-300', label: tr ? tr('severity_medium')   : 'MEDIUM' },
    LOW:       { bg: 'bg-emerald-100',text: 'text-emerald-700',border: 'border-emerald-300',label: tr ? tr('severity_low')      : 'LOW' },
    'SELL NOW — prices falling': { bg:'bg-red-100',    text:'text-red-700',    border:'border-red-300',    label: tr ? tr('sell')   : 'SELL NOW' },
    'HOLD — prices rising':      { bg:'bg-emerald-100',text:'text-emerald-700',border:'border-emerald-300',label: tr ? tr('hold')   : 'HOLD' },
    'NEUTRAL — stable market':   { bg:'bg-gray-100',   text:'text-gray-700',   border:'border-gray-300',   label: tr ? tr('neutral'): 'NEUTRAL' },
    'SELL':    { bg:'bg-red-100',    text:'text-red-700',    border:'border-red-300',    label: tr ? tr('sell')       : 'SELL' },
    'HOLD':    { bg:'bg-emerald-100',text:'text-emerald-700',border:'border-emerald-300',label: tr ? tr('hold')       : 'HOLD' },
    'NEUTRAL': { bg:'bg-gray-100',   text:'text-gray-700',   border:'border-gray-300',   label: tr ? tr('neutral')    : 'NEUTRAL' },
    'GOOD TIME': { bg:'bg-emerald-100',text:'text-emerald-700',border:'border-emerald-300',label: tr ? tr('good_time') : 'GOOD TIME' },
    'CAUTION':   { bg:'bg-yellow-100', text:'text-yellow-700', border:'border-yellow-300', label: tr ? tr('caution')   : 'CAUTION' },
    'AVOID':     { bg:'bg-red-100',    text:'text-red-700',    border:'border-red-300',    label: tr ? tr('avoid')     : 'AVOID' },
  }

  const style = map[level] || { bg:'bg-gray-100', text:'text-gray-600', border:'border-gray-200', label: level }

  return (
    <span className={`inline-block px-2.5 py-0.5 rounded-full text-xs font-mono font-semibold border ${style.bg} ${style.text} ${style.border}`}>
      {style.label}
    </span>
  )
}
