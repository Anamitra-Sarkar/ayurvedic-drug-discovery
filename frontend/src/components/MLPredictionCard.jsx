/**
 * MLPredictionCard.jsx — plain-language "Strength prediction".
 */
import { ConfidenceBadge, HowCalculated, ResearchNote } from './ui.jsx';

const FRIENDLY_FEATURE = {
  NumAromaticRings: 'Ring shapes',
  MolLogP: 'Oil–water mix',
  TPSA: 'Exposed surface',
  NumHDonors: 'Bonding spots',
  FractionCSP3: '3D bendiness',
};

export function friendlyFeatureName(raw) {
  if (!raw) return 'Chemical pattern';
  if (FRIENDLY_FEATURE[raw]) return FRIENDLY_FEATURE[raw];
  const m = raw.match(/ECFP4:\d+\s*(present)?\s*(\(.*\))?/);
  if (m) return 'Special fragment pattern';
  if (raw.startsWith('ECFP4')) return 'Special fragment pattern';
  return raw.replace(/([A-Z])/g, ' $1').trim();
}

export default function MLPredictionCard({ prediction, loading }) {
  if (loading) {
    return <div className="rounded-3xl border border-forest-900/10 bg-white p-6 animate-pulse h-[220px] dark:bg-forest-900" />;
  }
  if (!prediction) {
    return (
      <div className="card p-8 text-center">
        <div className="text-3xl">✨</div>
        <div className="text-sm font-medium text-forest-800 dark:text-cream-100 mt-2">No strength prediction yet</div>
        <div className="text-xs text-forest-700/70 dark:text-cream-100/60 mt-1">Run an analysis and the computer will make its best guess here.</div>
      </div>
    );
  }

  const ad = prediction.applicability_domain || {};
  const inside = ad.inside;
  const conf = ad.confidence || prediction.confidence || 0.7;

  return (
    <div className="card overflow-hidden">
      <div className="px-5 py-4 border-b border-forest-900/10 bg-gold-50/50 flex items-center justify-between dark:bg-white/5">
        <div className="flex items-center gap-2.5">
          <div className="w-9 h-9 rounded-2xl bg-gold-500 text-white flex items-center justify-center">✨</div>
          <div>
            <div className="font-display font-semibold text-[15px] text-forest-950 dark:text-cream-50">
              Strength prediction
              <HowCalculated title="strength prediction">
                A computer model that has seen many past examples predicts a strength score for this compound. We also check whether this compound looks enough like past examples for the guess to count (“inside its comfort zone”). Predictions are triage hints, never answers.
              </HowCalculated>
            </div>
            <div className="text-[11px] text-forest-700/75 dark:text-cream-100/60">Our model’s best guess · based on {prediction.featuresUsed || 'many'} chemical patterns</div>
          </div>
        </div>
        <ConfidenceBadge tier="ML_PREDICTION" />
      </div>

      <div className="p-5 grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div className="rounded-2xl bg-cream-50 border border-forest-900/10 p-4 text-center dark:bg-white/5">
          <div className="text-[10px] tracking-widest uppercase text-forest-700/60 dark:text-cream-100/50">Strength score</div>
          <div className="font-display text-3xl font-bold text-forest-950 dark:text-cream-50 mt-1">{prediction.pKd_pred?.toFixed(2)}</div>
          <div className="text-[11px] text-forest-700/70 dark:text-cream-100/60 mt-1">≈ {prediction.affinity_nM} in lab units · higher means stronger (predicted)</div>
        </div>
        <div className="rounded-2xl bg-white border border-forest-900/10 p-4 dark:bg-transparent">
          <div className="text-[10px] tracking-widest uppercase text-forest-700/60 dark:text-cream-100/50">
            Trust check
            <HowCalculated title="trust check">We measure how similar this compound is to the examples the model learned from. “Inside its comfort zone” means the guess is on familiar ground; “outside” means take it with extra salt.</HowCalculated>
          </div>
          <div className={`mt-2 inline-flex px-3 py-1 rounded-full text-xs font-medium border ${inside ? 'bg-forest-50 border-forest-200 text-forest-700' : 'bg-clay-100 border-clay-500/30 text-clay-700'}`}>
            {inside ? '✓ On familiar ground' : '✗ Unfamiliar territory — low trust'}
          </div>
          <div className="mt-2 space-y-1 text-[11px] text-forest-800/80 dark:text-cream-100/70">
            <div className="flex justify-between"><span>Give-or-take</span><span>± {prediction.uncertainty}</span></div>
          </div>
          <div className="mt-2 w-full h-1.5 bg-cream-200 rounded-full overflow-hidden dark:bg-white/10">
            <div className="h-full bg-forest-600 transition-all duration-500" style={{ width: `${Math.round(conf * 100)}%` }} />
          </div>
          <div className="text-[10px] text-forest-700/60 dark:text-cream-100/50 mt-1">{Math.round(conf * 100)}% model confidence (not real-world certainty)</div>
        </div>
      </div>

      <div className="px-5 pb-5">
        <ResearchNote text="This is a statistical guess from past examples — useful for shortlisting, but it cannot tell us how anything behaves in real life. Real lab measurements are still needed." />
      </div>
    </div>
  );
}
