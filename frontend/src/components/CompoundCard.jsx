
/**
 * CompoundCard.jsx
 * Shows phytochemical info, ADMET, drug-likeness, tier label
 * Evidence Tier: DATABASE_DERIVED
 */
import EvidenceTierBadge from './EvidenceTierBadge.jsx';
import { Link } from 'react-router-dom';

export default function CompoundCard({ compound, compact=false, onSelect }) {
  if (!compound) return null;
  const dl = compound.drugLikeness || {};
  const admet = compound.admet || {};

  const qedColor = (dl.qed || 0) > 0.7 ? 'text-green-700 bg-green-50 border-green-200' : (dl.qed || 0) > 0.5 ? 'text-amber-700 bg-amber-50 border-amber-200' : 'text-slate-600 bg-slate-50 border-slate-200';

  return (
    <div className={`group rounded-2xl border border-slate-200 bg-white shadow-card hover:shadow-card-hover transition-all overflow-hidden ${compact ? 'p-3' : 'p-0'} ${onSelect ? 'cursor-pointer' : ''}`} onClick={()=>onSelect?.(compound)}>
      <div className={compact ? '' : 'p-4'}>
        {/* Top */}
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2 flex-wrap">
              <h3 className="font-display font-semibold text-[15px] text-slate-900 truncate">{compound.name}</h3>
              <span className="font-mono text-[10px] px-1.5 py-0.5 rounded bg-slate-100 border border-slate-200 text-slate-600">{compound.id}</span>
            </div>
            <div className="mt-1 flex items-center gap-2">
              <span className="font-mono text-[11px] text-slate-500 truncate">{compound.plant}</span>
              {compound.ayurvedicName && <span className="text-[11px] px-1.5 py-0.5 rounded-full bg-amber-50 border border-amber-200 text-amber-800">{compound.ayurvedicName}</span>}
            </div>
          </div>
          <EvidenceTierBadge tier={compound.evidenceTier || 'DATABASE_DERIVED'} size="sm" />
        </div>

        {/* Structure preview placeholder */}
        {!compact && (
          <div className="mt-3 rounded-xl bg-[#fcfcfa] border border-slate-100 h-[96px] flex items-center justify-center relative overflow-hidden">
            <div className="font-mono text-[11px] text-slate-400 text-center px-3">
              <div className="text-lg">⬡</div>
              <div className="mt-1">{compound.formula || 'C?'} • {compound.mw ? `${compound.mw} Da` : 'MW unknown'}</div>
              <div className="text-[10px] mt-0.5">{compound.smiles ? compound.smiles.slice(0,42)+'...' : 'SMILES not shown'}</div>
            </div>
            <div className="absolute top-2 right-2 font-mono text-[9px] px-1.5 py-0.5 rounded-full bg-white border border-slate-200 text-slate-500">IMPPAT • DB Tier</div>
          </div>
        )}

        {/* Props */}
        <div className="mt-3 grid grid-cols-4 gap-2">
          <div className="rounded-lg bg-slate-50 border border-slate-100 p-2">
            <div className="font-mono text-[9px] tracking-widest text-slate-500">LOGP</div>
            <div className="font-mono text-xs font-medium text-slate-800 mt-0.5">{compound.logP ?? '—'}</div>
          </div>
          <div className="rounded-lg bg-slate-50 border border-slate-100 p-2">
            <div className="font-mono text-[9px] tracking-widest text-slate-500">TPSA</div>
            <div className="font-mono text-xs font-medium text-slate-800 mt-0.5">{compound.tpsa ?? '—'}</div>
          </div>
          <div className="rounded-lg bg-slate-50 border border-slate-100 p-2">
            <div className="font-mono text-[9px] tracking-widest text-slate-500">HBD/HBA</div>
            <div className="font-mono text-xs font-medium text-slate-800 mt-0.5">{compound.hbd ?? '-'}/{compound.hba ?? '-'}</div>
          </div>
          <div className={`rounded-lg border p-2 ${qedColor}`}>
            <div className="font-mono text-[9px] tracking-widest opacity-80">QED</div>
            <div className="font-mono text-xs font-medium mt-0.5">{dl.qed ? dl.qed.toFixed(2) : '—'}</div>
          </div>
        </div>

        {/* Traditional use & ADMET */}
        {!compact && (
          <>
            <div className="mt-3 flex flex-wrap gap-1.5">
              {compound.traditionalUse && <span className="inline-flex px-2 py-1 rounded-full bg-[#f6f7f0] border border-[#e8e9d8] text-[11px] text-[#5f5f40]">Ayurveda: {compound.traditionalUse}</span>}
              {admet.giAbsorption && <span className="inline-flex px-2 py-1 rounded-full bg-white border border-slate-200 text-[11px] font-mono text-slate-600">GI: {admet.giAbsorption}</span>}
              {admet.bbb !== undefined && <span className="inline-flex px-2 py-1 rounded-full bg-white border border-slate-200 text-[11px] font-mono text-slate-600">BBB: {admet.bbb}</span>}
              {dl.ruleOfFivePass !== undefined && (
                <span className={`inline-flex px-2 py-1 rounded-full text-[11px] font-mono border ${dl.ruleOfFivePass ? 'bg-green-50 border-green-200 text-green-700' : 'bg-red-50 border-red-200 text-red-700'}`}>Lipinski {dl.lipinski ?? ''}/4</span>
              )}
            </div>

            <div className="mt-3 flex items-center justify-between">
              <span className="font-mono text-[10px] text-slate-400">Evidence: {compound.evidenceTier} • Layer i</span>
              <Link to={`/compound/${compound.id}`} className="text-xs font-medium text-cyan-700 hover:text-cyan-800 inline-flex items-center gap-1">
                Detail → 
              </Link>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
