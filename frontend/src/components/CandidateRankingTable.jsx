
/**
 * CandidateRankingTable.jsx
 * Ranked list of candidates with evidence tiers separated
 * Must not present as clinical proof — warning banner
 */
import { useState } from 'react';
import EvidenceTierBadge, { TierSeparator } from './EvidenceTierBadge.jsx';
import { getDisclaimerForTiers } from '../utils/evidence.js';

export default function CandidateRankingTable({ ranking, loading, onSelect }) {
  const [sortBy, setSortBy] = useState('rank');
  const [expanded, setExpanded] = useState(null);

  if (loading) {
    return <div className="rounded-2xl border border-slate-200 bg-white p-6 animate-pulse space-y-3"><div className="h-6 bg-slate-100 rounded w-1/3" /><div className="h-32 bg-slate-50 rounded" /></div>;
  }
  if (!ranking?.candidates) {
    return <div className="rounded-2xl border border-slate-200 bg-white p-6 text-center font-mono text-xs text-slate-500">No ranking — run pipeline or check target.</div>;
  }

  const candidates = [...ranking.candidates].sort((a,b)=>{
    if (sortBy==='docking') return (a.docking?.affinity_kcal_mol||0) - (b.docking?.affinity_kcal_mol||0);
    if (sortBy==='ml') return (b.ml?.pKd_pred||0) - (a.ml?.pKd_pred||0);
    if (sortBy==='qed') return (b.database?.qed||0) - (a.database?.qed||0);
    return a.rank - b.rank;
  });

  const allTiers = ['DATABASE_DERIVED','DOCKING_RESULT','ML_PREDICTION','XAI_INTERPRETATION','LITERATURE_DERIVED'];
  const disclaimer = getDisclaimerForTiers(allTiers);

  return (
    <div className="rounded-2xl border border-slate-200 bg-white shadow-card overflow-hidden">
      {/* Warning banner - HARD REQUIREMENT */}
      <div className="bg-gradient-to-r from-amber-50 to-red-50 border-b-2 border-amber-300 px-5 py-4">
        <div className="flex gap-3">
          <div className="w-10 h-10 rounded-xl bg-amber-600 text-white flex items-center justify-center flex-shrink-0">⚠️</div>
          <div className="flex-1">
            <div className="font-display font-bold text-amber-900 text-sm tracking-wide">{disclaimer.title}</div>
            <div className="mt-1 text-xs text-amber-900 leading-relaxed">{disclaimer.message}</div>
            <div className="mt-2 flex flex-wrap gap-2">
              <span className="font-mono text-[10px] px-2 py-0.5 rounded-full bg-white border border-amber-200 text-amber-800">TIER SEPARATION ENFORCED</span>
              <span className="font-mono text-[10px] px-2 py-0.5 rounded-full bg-white border border-red-200 text-red-700">NO CLINICAL RANK IMPLICATION</span>
              <span className="font-mono text-[10px] px-2 py-0.5 rounded-full bg-white border border-slate-200 text-slate-600">Ref: AYUSH-64 required RCTs after computational hypothesis</span>
            </div>
          </div>
        </div>
      </div>

      {/* Controls */}
      <div className="px-5 py-3 border-b border-slate-100 bg-slate-50/60 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <span className="font-mono text-[11px] tracking-widest text-slate-600">SORT BY</span>
          {[
            {id:'rank', label:'# Rank'},
            {id:'docking', label:'ΔG Docking'},
            {id:'ml', label:'pKd ML'},
            {id:'qed', label:'QED Drug-like'},
          ].map(o=>(
            <button key={o.id} onClick={()=>setSortBy(o.id)} className={`px-3 py-1 rounded-full text-xs font-medium border ${sortBy===o.id ? 'bg-slate-900 text-white border-slate-900' : 'bg-white border-slate-200 text-slate-700 hover:bg-slate-50'}`}>{o.label}</button>
          ))}
        </div>
        <div className="font-mono text-[11px] text-slate-500">Target: {ranking.target} • {candidates.length} candidates • {allTiers.length} tiers separated</div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <div className="min-w-[980px]">
          {/* Header */}
          <div className="grid grid-cols-12 gap-0 bg-slate-50 border-b border-slate-200 font-mono text-[10px] tracking-widest text-slate-500 px-4 py-2.5">
            <span className="col-span-1">#</span>
            <span className="col-span-3">COMPOUND (IMPPAT)</span>
            <span className="col-span-2">DATABASE_DERIVED</span>
            <span className="col-span-2">DOCKING_RESULT</span>
            <span className="col-span-2">ML_PREDICTION</span>
            <span className="col-span-2">XAI + LIT</span>
          </div>

          {candidates.map((c, idx)=>(
            <div key={c.compound.id} className={`grid grid-cols-12 gap-0 px-4 py-3 border-b border-slate-100 hover:bg-[#f8faf6] transition ${idx===0 ? 'bg-amber-50/50' : 'bg-white'}`}>
              <div className="col-span-1 flex items-center gap-2">
                <span className={`w-7 h-7 rounded-full flex items-center justify-center font-mono text-xs font-bold ${idx===0? 'bg-amber-600 text-white' : idx<3 ? 'bg-slate-900 text-white' : 'bg-slate-100 text-slate-600'}`}>{c.rank}</span>
              </div>

              <div className="col-span-3 min-w-0">
                <div className="font-display font-semibold text-sm text-slate-900 truncate">{c.compound.name}</div>
                <div className="font-mono text-[11px] text-slate-500 truncate">{c.compound.id} • {c.compound.plant?.slice(0,28)}</div>
                <div className="mt-1 flex gap-1">
                  <EvidenceTierBadge tier="DATABASE_DERIVED" size="sm" showLabel={false} />
                </div>
              </div>

              <div className="col-span-2">
                <div className="rounded-lg bg-cyan-50 border border-cyan-100 p-2">
                  <div className="font-mono text-[10px] text-cyan-700">QED {c.database?.qed?.toFixed(2)} • Lipinski ✓</div>
                  <div className="font-mono text-[11px] text-slate-700 mt-1">{c.compound.formula}</div>
                </div>
              </div>

              <div className="col-span-2">
                <div className="rounded-lg bg-violet-50 border border-violet-100 p-2">
                  <div className="font-mono text-xs font-bold text-violet-800">{c.docking?.affinity_kcal_mol?.toFixed(1)} kcal/mol</div>
                  <div className="font-mono text-[10px] text-violet-600 mt-1">conf {(c.docking?.confidence*100).toFixed(0)}% • computational</div>
                </div>
              </div>

              <div className="col-span-2">
                <div className="rounded-lg bg-pink-50 border border-pink-100 p-2">
                  <div className="font-mono text-xs font-bold text-pink-800">pKd {c.ml?.pKd_pred?.toFixed(1)}</div>
                  <div className="font-mono text-[10px] text-pink-600 mt-1">AD {Math.round((c.ml?.applicability||0)*100)}% • model infer</div>
                </div>
              </div>

              <div className="col-span-2 flex flex-col gap-1">
                <div className="rounded-lg bg-orange-50 border border-orange-100 p-1.5">
                  <div className="font-mono text-[10px] text-orange-700 truncate">XAI: {c.xai?.topFeature}</div>
                </div>
                <div className="rounded-lg bg-green-50 border border-green-100 p-1.5">
                  <div className="font-mono text-[10px] text-green-700">{c.literature?.citations} cites • {Math.round((c.literature?.faithfulness||0)*100)}% faithful</div>
                </div>
                <button onClick={()=>setExpanded(expanded===c.compound.id?null:c.compound.id)} className="mt-1 text-[11px] font-medium text-slate-700 hover:text-slate-900">{expanded===c.compound.id? 'Hide':'Evidence breakdown'}</button>
              </div>

              {expanded===c.compound.id && (
                <div className="col-span-12 mt-3 rounded-xl border border-slate-200 bg-slate-50 p-3">
                  <TierSeparator tiersPresent={c.tiersPresent} />
                  <div className="grid grid-cols-5 gap-2 mt-2">
                    {[
                      { tier:'DATABASE_DERIVED', val: `QED ${c.database?.qed?.toFixed(2)} • ${c.compound.plant}` },
                      { tier:'DOCKING_RESULT', val: `${c.docking?.affinity_kcal_mol} kcal/mol • pose hypothesis` },
                      { tier:'ML_PREDICTION', val: `pKd ${c.ml?.pKd_pred} • AD ${Math.round(c.ml?.applicability*100)}%` },
                      { tier:'XAI_INTERPRETATION', val: `${c.xai?.topFeature} • SHAP ${c.xai?.shapSum?.toFixed(2)}` },
                      { tier:'LITERATURE_DERIVED', val: `${c.literature?.citations} papers • faithful ${Math.round(c.literature?.faithfulness*100)}%` },
                    ].map(row=>(
                      <div key={row.tier} className="rounded-lg bg-white border border-slate-200 p-2">
                        <EvidenceTierBadge tier={row.tier} size="sm" />
                        <div className="font-mono text-[11px] text-slate-700 mt-2 leading-tight">{row.val}</div>
                      </div>
                    ))}
                  </div>
                  <div className="mt-3 flex gap-2">
                    <button onClick={()=>onSelect?.(c.compound)} className="px-3 py-1.5 rounded-full bg-slate-900 text-white text-xs font-medium">View compound →</button>
                    <span className="font-mono text-[10px] text-slate-500 self-center">Each column is independent evidence — not summed into clinical score per AYUSH-64 compliance</span>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      <div className="px-5 py-3 bg-slate-50 border-t border-slate-100 flex items-center justify-between">
        <span className="font-mono text-[11px] text-slate-500">Ranking = computational triage only. No column implies therapeutic effect. See Documentation for AYUSH-64 justification.</span>
        <button className="font-mono text-[11px] px-2.5 py-1 rounded-full bg-white border border-slate-200">Export (CSV tier-separated)</button>
      </div>
    </div>
  );
}
