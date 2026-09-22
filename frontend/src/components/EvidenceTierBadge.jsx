
/**
 * EvidenceTierBadge.jsx
 * Shows 5 tiers with colors, icons, tooltip explaining AYUSH-64 justification
 * Core UI enforcement of evidence separation.
 * 
 * @component
 */
import { useState } from 'react';
import { EVIDENCE_TIERS } from '../utils/evidence.js';

const TIER_META = EVIDENCE_TIERS;

export default function EvidenceTierBadge({ tier, size='md', showTooltip=true, showLabel=true, className='' }) {
  const [hover, setHover] = useState(false);
  const meta = TIER_META[tier];
  if (!meta) {
    return <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-mono bg-gray-100 text-gray-600 ${className}`}>UNKNOWN TIER</span>;
  }

  const sizeClasses = {
    sm: 'px-2 py-0.5 text-[10px] gap-1',
    md: 'px-2.5 py-1 text-xs gap-1.5',
    lg: 'px-3 py-1.5 text-sm gap-2',
  };

  return (
    <div className="relative inline-block" onMouseEnter={()=>setHover(true)} onMouseLeave={()=>setHover(false)}>
      <span
        className={`inline-flex items-center font-mono font-semibold tracking-wide rounded-full border ${sizeClasses[size]} ${meta.bg} ${meta.border} ${meta.text} ${className} transition-all cursor-help`}
        style={{ borderColor: meta.color + '33' }}
      >
        <span className="text-[13px] leading-none">{meta.icon}</span>
        {showLabel && <span>{size==='sm'? meta.shortLabel : meta.label}</span>}
        <span className={`w-1.5 h-1.5 rounded-full ${meta.badge}`} style={{background: meta.color}}></span>
      </span>

      {showTooltip && hover && (
        <div className="absolute z-50 left-0 top-full mt-2 w-[340px] p-4 bg-white border border-slate-200 rounded-xl shadow-xl text-left animate-in fade-in">
          <div className="flex items-start gap-3 mb-2">
            <div className="w-9 h-9 rounded-lg flex items-center justify-center text-lg" style={{background: meta.color + '15', border: `1px solid ${meta.color}30`}}>
              {meta.icon}
            </div>
            <div>
              <div className="font-display font-bold text-slate-900 text-sm">{meta.label}</div>
              <div className="font-mono text-[10px] text-slate-500 tracking-widest mt-0.5">{meta.layer}</div>
            </div>
          </div>
          <p className="text-xs text-slate-700 leading-relaxed">{meta.description}</p>

          <div className="mt-3 p-2.5 rounded-lg bg-amber-50 border border-amber-200">
            <div className="flex gap-1.5 items-start">
              <span className="text-[11px]">⚖️</span>
              <div>
                <div className="font-semibold text-[11px] text-amber-900 tracking-wide">AYUSH-64 JUSTIFICATION</div>
                <div className="text-[11px] text-amber-800 mt-1 leading-relaxed">{meta.ayush64Note}</div>
              </div>
            </div>
          </div>

          <div className="mt-2.5 flex items-center justify-between">
            <span className="text-[10px] font-mono text-slate-500">Confidence basis:</span>
            <span className="text-[10px] font-mono text-slate-700">{meta.confidenceBasis}</span>
          </div>

          <div className="mt-2 pt-2 border-t border-slate-100">
            <span className="text-[10px] font-mono font-semibold text-red-700 tracking-wide">⚠️ NOT CLINICAL PROOF</span>
          </div>
        </div>
      )}
    </div>
  );
}

/**
 * All tiers legend bar
 */
export function EvidenceTierLegend({ className='' }) {
  return (
    <div className={`flex flex-wrap gap-2 ${className}`}>
      {Object.values(TIER_META).map(t => (
        <EvidenceTierBadge key={t.id} tier={t.id} size="sm" />
      ))}
    </div>
  );
}

/**
 * Tier separator - visual indicator that tiers must remain separated
 */
export function TierSeparator({ tiersPresent }) {
  return (
    <div className="flex items-center gap-2 py-2">
      <div className="h-px flex-1 bg-slate-200" />
      <span className="font-mono text-[10px] tracking-widest text-slate-400">EVIDENCE TIERS SEPARATED — NO MERGED CLINICAL SCORE</span>
      <div className="h-px flex-1 bg-slate-200" />
    </div>
  );
}
