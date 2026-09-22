
/**
 * MLPredictionCard.jsx
 * Shows affinity prediction, applicability domain, tier ML_PREDICTION
 */
import EvidenceTierBadge from './EvidenceTierBadge.jsx';

export default function MLPredictionCard({ prediction, loading }) {
  if (loading) {
    return <div className="rounded-2xl border border-pink-100 bg-pink-50/50 p-6 animate-pulse h-[220px]" />;
  }
  if (!prediction) {
    return <div className="rounded-2xl border border-slate-200 bg-white p-6 text-center font-mono text-xs text-slate-500">No ML prediction yet — run pipeline.</div>;
  }

  const ad = prediction.applicability_domain || {};
  const inside = ad.inside;
  const conf = ad.confidence || prediction.confidence || 0.7;

  return (
    <div className="rounded-2xl border border-pink-200 bg-white shadow-card overflow-hidden">
      <div className="px-4 py-3 border-b border-pink-100 bg-pink-50/60 flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-pink-600 text-white flex items-center justify-center">🤖</div>
          <div>
            <div className="font-display font-semibold text-sm">Binding Affinity — Supervised ML</div>
            <div className="font-mono text-[11px] text-pink-700">Model {prediction.modelVersion} • {prediction.featuresUsed} feats</div>
          </div>
        </div>
        <EvidenceTierBadge tier="ML_PREDICTION" />
      </div>

      <div className="p-4 grid grid-cols-2 gap-4">
        <div className="rounded-xl bg-slate-50 border border-slate-200 p-3 text-center">
          <div className="font-mono text-[10px] tracking-widest text-slate-500">pKd (pred)</div>
          <div className="font-mono text-2xl font-bold text-slate-900 mt-1">{prediction.pKd_pred?.toFixed(2)}</div>
          <div className="font-mono text-[11px] text-slate-500 mt-1">≈ {prediction.affinity_nM} nM • Kd = 10^-pKd</div>
        </div>
        <div className="rounded-xl bg-white border border-slate-200 p-3">
          <div className="font-mono text-[10px] tracking-widest text-slate-500">APPLICABILITY DOMAIN</div>
          <div className={`mt-2 inline-flex px-2.5 py-1 rounded-full text-xs font-medium border ${inside ? 'bg-green-50 border-green-200 text-green-700' : 'bg-red-50 border-red-200 text-red-700'}`}>
            {inside ? '✓ Inside AD' : '✗ Outside AD — low trust'}
          </div>
          <div className="mt-2 space-y-1 font-mono text-[11px] text-slate-600">
            <div className="flex justify-between"><span>distance</span><span>{ad.distance}</span></div>
            <div className="flex justify-between"><span>threshold</span><span>{ad.threshold}</span></div>
            <div className="flex justify-between"><span>uncertainty ±</span><span>{prediction.uncertainty}</span></div>
          </div>
          <div className="mt-2 w-full h-1.5 bg-slate-100 rounded-full overflow-hidden">
            <div className="h-full bg-pink-600" style={{width: `${Math.round(conf*100)}%`}} />
          </div>
          <div className="font-mono text-[10px] text-slate-500 mt-1">{Math.round(conf*100)}% model confidence (not clinical confidence)</div>
        </div>
      </div>

      <div className="px-4 pb-4">
        <div className="rounded-xl bg-amber-50 border border-amber-200 p-3">
          <div className="font-mono text-[10px] tracking-widest font-bold text-amber-900">TIER ML_PREDICTION — STATISTICAL INFERENCE ONLY</div>
          <div className="text-[11px] text-amber-800 mt-1 leading-relaxed">
            Trained on curated ChEMBL/bioactivity data using ECFP4 + RDKit descriptors; predicts affinity via RandomForest/GraphNN. Applicability domain checks if phytochemical is within training chemical space. Like AYUSH-64 AI repurposing, ML score informs <span className="font-semibold">computational triage</span> only — NOT therapeutic potency. Requires experimental IC50/Kd.
          </div>
        </div>
      </div>
    </div>
  );
}
