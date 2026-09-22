
/**
 * DockingResults.jsx
 * Table of docking scores, confidence, evidence tier DOCKING_RESULT
 * MUST include disclaimer not clinical proof
 */
import EvidenceTierBadge from './EvidenceTierBadge.jsx';

export default function DockingResults({ result, loading }) {
  if (loading) {
    return (
      <div className="rounded-2xl border border-violet-100 bg-violet-50/50 p-6 animate-pulse">
        <div className="h-4 bg-violet-100 rounded w-1/3 mb-4" />
        <div className="h-24 bg-white rounded-xl border border-violet-100" />
      </div>
    );
  }
  if (!result) {
    return (
      <div className="rounded-2xl border border-slate-200 bg-white p-6 text-center">
        <div className="font-mono text-xs text-slate-500">No docking result yet — run pipeline for DOCKING_RESULT tier.</div>
      </div>
    );
  }

  const poses = result.poses || [];
  const interactions = result.interactions || [];

  return (
    <div className="rounded-2xl border border-violet-200 bg-white shadow-card overflow-hidden">
      <div className="px-4 py-3 border-b border-violet-100 bg-violet-50/60 flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-violet-600 text-white flex items-center justify-center">🧬</div>
          <div>
            <div className="font-display font-semibold text-sm text-slate-900">Molecular Docking — Vina Style</div>
            <div className="font-mono text-[11px] text-violet-700">{result.target} • Affinity {result.affinity_kcal_mol} kcal/mol • confidence {(result.confidence*100).toFixed(0)}%</div>
          </div>
        </div>
        <EvidenceTierBadge tier="DOCKING_RESULT" />
      </div>

      {/* Score cards */}
      <div className="grid grid-cols-3 divide-x divide-violet-100 border-b border-violet-100">
        <div className="p-4 text-center">
          <div className="font-mono text-[10px] tracking-widest text-violet-600">ΔG (BEST)</div>
          <div className="font-mono font-bold text-lg text-slate-900 mt-1">{result.affinity_kcal_mol} <span className="text-xs font-normal">kcal/mol</span></div>
          <div className="font-mono text-[10px] text-slate-500 mt-1">Lower = stronger (hypothesis)</div>
        </div>
        <div className="p-4 text-center">
          <div className="font-mono text-[10px] tracking-widest text-violet-600">RMSD LOWER</div>
          <div className="font-mono font-bold text-lg text-slate-900 mt-1">{result.rmsd ?? '0.00'} <span className="text-xs font-normal">Å</span></div>
          <div className="font-mono text-[10px] text-slate-500 mt-1">Pose stability</div>
        </div>
        <div className="p-4 text-center">
          <div className="font-mono text-[10px] tracking-widest text-violet-600">CLUSTERS</div>
          <div className="font-mono font-bold text-lg text-slate-900 mt-1">{result.poseCluster ?? poses.length}</div>
          <div className="font-mono text-[10px] text-slate-500 mt-1">Distinct binding modes</div>
        </div>
      </div>

      {/* Poses table */}
      <div className="p-4">
        <div className="font-mono text-[11px] tracking-widest font-semibold text-slate-700 mb-2">TOP POSES (Vina scoring, physics-inspired, mock fallback if binary absent)</div>
        <div className="rounded-xl border border-slate-200 overflow-hidden">
          <div className="grid grid-cols-4 bg-slate-50 border-b border-slate-200 font-mono text-[10px] tracking-widest text-slate-500 px-3 py-2">
            <span>MODE</span><span>AFFINITY (kcal/mol)</span><span>RMSD LB</span><span>RMSD UB</span>
          </div>
          {poses.map((p,i)=>(
            <div key={i} className={`grid grid-cols-4 px-3 py-2 font-mono text-xs border-b last:border-0 border-slate-100 ${i===0 ? 'bg-violet-50/60 font-semibold' : 'bg-white'}`}>
              <span>#{i+1}</span><span className={p.affinity < -7 ? 'text-violet-700' : ''}>{p.affinity}</span><span>{p.rmsd_lb}</span><span>{p.rmsd_ub}</span>
            </div>
          ))}
        </div>

        {interactions.length>0 && (
          <div className="mt-4">
            <div className="font-mono text-[11px] tracking-widest font-semibold text-slate-700 mb-2">INTERACTIONS (PLIP-style heuristic)</div>
            <div className="flex flex-wrap gap-2">
              {interactions.map((it, idx)=>(
                <span key={idx} className="px-2.5 py-1 rounded-full bg-white border border-slate-200 text-xs font-mono">
                  {it.type} • {it.residue} • {it.distance}Å
                </span>
              ))}
            </div>
          </div>
        )}

        <div className="mt-4 rounded-xl bg-amber-50 border border-amber-200 p-3">
          <div className="font-mono text-[10px] tracking-widest font-bold text-amber-900">EVIDENCE TIER DOCKING_RESULT — NON-CLINICAL DISCLAIMER</div>
          <div className="mt-1 text-[11px] text-amber-800 leading-relaxed">
            Docking score is a <span className="font-semibold">computational binding hypothesis</span> using AutoDock Vina-style empirical scoring (ΔG ≈ vdW + Hbond + Elec + Desolv + Tors). It does NOT demonstrate in vitro activity, let alone clinical efficacy. AYUSH-64 precedent: docking served only as target-mapping step before Ayurvedic pharmacology assessment and RCTs. Fallback: if Vina binary absent, physics-inspired mock scoring with same API shape.
          </div>
        </div>
      </div>
    </div>
  );
}
