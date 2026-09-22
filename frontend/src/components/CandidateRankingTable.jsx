/**
 * CandidateRankingTable.jsx — plain-language "Most promising picks".
 * Sorting/data logic unchanged; headings and warnings rewritten plainly.
 */
import { useState } from 'react';
import { ConfidenceBadge } from './ui.jsx';
import { TierSeparator } from './EvidenceTierBadge.jsx';
import { fitVerdict } from '../utils/friendly.js';

// The real /candidates/rank endpoint only ever runs DATABASE_DERIVED +
// DOCKING_RESULT for a shortlist (no ML/XAI/literature call per candidate -
// too slow to run for a whole ranked list, unlike a single compound's
// Results page). Showing "Trust 0%"/"0% grounded" from undefined ml/
// literature fields presented an absent computation as a real zero result -
// exactly what this app's own evidentiary-tier rule says never to do.
// tiersPresent (real, from the backend) is the source of truth for what
// was actually computed for a given candidate.
const hasTier = (c, tier) => Array.isArray(c.tiersPresent) && c.tiersPresent.includes(tier);

export default function CandidateRankingTable({ ranking, loading, onSelect }) {
  const [sortBy, setSortBy] = useState('rank');
  const [expanded, setExpanded] = useState(null);

  if (loading) {
    return <div className="card p-6 animate-pulse space-y-3"><div className="h-6 bg-cream-200 rounded w-1/3 dark:bg-white/10" /><div className="h-32 bg-cream-100 rounded dark:bg-white/5" /></div>;
  }
  if (!ranking?.candidates) {
    return (
      <div className="card p-8 text-center">
        <div className="text-3xl">🌱</div>
        <div className="text-sm font-medium text-forest-800 dark:text-cream-100 mt-2">No shortlist yet</div>
        <div className="text-xs text-forest-700/70 dark:text-cream-100/60 mt-1">Run an analysis and the most promising picks will appear here.</div>
      </div>
    );
  }

  const candidates = [...ranking.candidates].sort((a, b) => {
    if (sortBy === 'docking') return (a.docking?.affinity_kcal_mol || 0) - (b.docking?.affinity_kcal_mol || 0);
    if (sortBy === 'ml') return (b.ml?.pKd_pred || 0) - (a.ml?.pKd_pred || 0);
    if (sortBy === 'qed') return (b.database?.qed || 0) - (a.database?.qed || 0);
    return a.rank - b.rank;
  });

  return (
    <div className="card overflow-hidden">
      <div className="bg-gradient-to-r from-gold-50 to-cream-100 border-b-2 border-gold-300/60 px-5 py-4 dark:from-gold-400/10 dark:to-transparent">
        <div className="flex gap-3">
          <div className="w-10 h-10 rounded-2xl bg-gold-500 text-white flex items-center justify-center flex-shrink-0">🌼</div>
          <div className="flex-1">
            <div className="font-display font-bold text-gold-700 text-sm tracking-wide dark:text-gold-300">A computer shortlist — not a recommendation</div>
            <div className="mt-1 text-xs text-forest-900/80 dark:text-cream-100/75 leading-relaxed">
              These picks are ordered by early computer guesses only. A top spot does not mean something works or is safe — every candidate still needs real lab testing.
            </div>
            <div className="mt-2 flex flex-wrap gap-2">
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-white border border-gold-300/60 text-gold-700">Judged separately, not blended</span>
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-white border border-forest-900/10 text-forest-700">Research stage only</span>
            </div>
          </div>
        </div>
      </div>

      <div className="px-5 py-3 border-b border-forest-900/10 bg-cream-50/60 flex flex-wrap items-center justify-between gap-3 dark:bg-white/5">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-[11px] tracking-widest uppercase text-forest-700/70 dark:text-cream-100/60">Order by</span>
          {[
            { id: 'rank', label: '# Our order' },
            { id: 'docking', label: 'Snuggest fit' },
            { id: 'ml', label: 'Strongest guess' },
            { id: 'qed', label: 'Most balanced' },
          ].map((o) => (
            <button key={o.id} onClick={() => setSortBy(o.id)} className={`px-3 py-1 rounded-full text-xs font-medium border transition active:scale-95 ${sortBy === o.id ? 'bg-forest-700 text-white border-forest-700' : 'bg-white border-forest-900/10 text-forest-800 hover:shadow-card dark:bg-white/5 dark:text-cream-100'}`}>{o.label}</button>
          ))}
        </div>
        <div className="text-[11px] text-forest-700/60 dark:text-cream-100/50">{candidates.length} candidates · each judged on its own</div>
      </div>

      <div className="overflow-x-auto">
        <p className="px-5 pt-2 text-[11px] text-forest-700/60 dark:text-cream-100/50 md:hidden">Swipe sideways to see all columns →</p>
        {/* Mobile card layout (below md) — same data, stacked */}
        <div className="px-4 py-3 space-y-3 md:hidden">
          {candidates.map((c, idx) => (
            <div key={c.compound.id} className={`rounded-2xl border border-forest-900/10 p-3 ${idx === 0 ? 'bg-gold-50/60 dark:bg-gold-400/5' : 'bg-white dark:bg-transparent'}`}>
              <div className="flex items-center gap-2 min-w-0">
                <span className={`w-7 h-7 shrink-0 rounded-full flex items-center justify-center text-xs font-bold ${idx === 0 ? 'bg-gold-500 text-white' : idx < 3 ? 'bg-forest-700 text-white' : 'bg-cream-200 text-forest-700 dark:bg-white/10 dark:text-cream-100'}`}>{c.rank}</span>
                <div className="min-w-0 flex-1">
                  <div className="font-display font-semibold text-sm text-forest-950 dark:text-cream-50 truncate">{c.compound.name}</div>
                  <div className="text-[11px] text-forest-700/60 dark:text-cream-100/50 truncate">{c.compound.id} · {c.compound.plant?.slice(0, 28)}</div>
                </div>
                <ConfidenceBadge tier="DATABASE_DERIVED" size="sm" showLabel={false} />
              </div>
              <div className="mt-2 grid grid-cols-2 gap-2">
                <div className="rounded-xl bg-forest-50 border border-forest-900/10 p-2 dark:bg-white/5">
                  <div className="text-[10px] text-forest-700">Balance {c.database?.qed?.toFixed(2)}</div>
                  <div className="text-[11px] text-forest-800/80 dark:text-cream-100/70 mt-0.5 truncate">{c.compound.formula}</div>
                </div>
                <div className="rounded-xl bg-cream-100 border border-gold-300/50 p-2 dark:bg-white/5">
                  <div className="text-xs font-bold text-forest-800 dark:text-cream-50">{c.docking?.affinity_kcal_mol?.toFixed(1)} fit score</div>
                  <div className="text-[10px] text-forest-700/70 dark:text-cream-100/60 mt-0.5">{fitVerdict(c.docking?.affinity_kcal_mol)}</div>
                </div>
                <div className="rounded-xl bg-gold-50 border border-gold-300/50 p-2 dark:bg-white/5">
                  {hasTier(c, 'ML_PREDICTION') ? (
                    <>
                      <div className="text-xs font-bold text-forest-800 dark:text-cream-50">Strength {c.ml?.pKd_pred?.toFixed(1)}</div>
                      <div className="text-[10px] text-forest-700/70 dark:text-cream-100/60 mt-0.5">Trust {Math.round((c.ml?.applicability || 0) * 100)}%</div>
                    </>
                  ) : (
                    <div className="text-[10px] italic text-forest-700/60 dark:text-cream-100/50">Not scored for this shortlist</div>
                  )}
                </div>
                <div className="rounded-xl bg-forest-50 border border-forest-900/10 p-2 dark:bg-white/5">
                  <div className="text-[10px] text-forest-700 dark:text-cream-100/70 truncate">Why: {hasTier(c, 'XAI_INTERPRETATION') ? plainTop(c.xai?.topFeature) : 'not explained here'}</div>
                  <div className="text-[10px] text-forest-700/70 dark:text-cream-100/60 mt-0.5">
                    {hasTier(c, 'LITERATURE_DERIVED') ? `${c.literature?.citations} papers · ${Math.round((c.literature?.faithfulness || 0) * 100)}% grounded` : 'Papers not checked here'}
                  </div>
                </div>
              </div>
              <button onClick={() => setExpanded(expanded === c.compound.id ? null : c.compound.id)} className="mt-2 w-full rounded-full border border-forest-900/10 bg-white py-2 text-[12px] font-medium text-forest-700 active:scale-[0.98] dark:bg-white/5 dark:text-cream-100">
                {expanded === c.compound.id ? 'Hide breakdown ▲' : 'See breakdown ▼'}
              </button>
              {expanded === c.compound.id && (
                <div className="mt-2 rounded-2xl border border-forest-900/10 bg-cream-50 p-3 dark:bg-white/5">
                  <TierSeparator tiersPresent={c.tiersPresent} />
                  <div className="grid grid-cols-1 gap-2 mt-2">
                    {[
                      { tier: 'DATABASE_DERIVED', val: `Balance ${c.database?.qed?.toFixed(2)} · ${c.compound.plant}` },
                      { tier: 'DOCKING_RESULT', val: `${c.docking?.affinity_kcal_mol?.toFixed(2)} fit score` },
                      { tier: 'ML_PREDICTION', val: hasTier(c, 'ML_PREDICTION') ? `Strength ${c.ml?.pKd_pred?.toFixed(2)}` : 'Not computed for this shortlist' },
                      { tier: 'XAI_INTERPRETATION', val: hasTier(c, 'XAI_INTERPRETATION') ? plainTop(c.xai?.topFeature) : 'Not computed for this shortlist' },
                      { tier: 'LITERATURE_DERIVED', val: hasTier(c, 'LITERATURE_DERIVED') ? `${c.literature?.citations} papers` : 'Not computed for this shortlist' },
                    ].map((row) => (
                      <div key={row.tier} className="rounded-xl bg-white border border-forest-900/10 p-2 dark:bg-white/5">
                        <ConfidenceBadge tier={row.tier} size="sm" />
                        <div className="text-[11px] text-forest-800/80 dark:text-cream-100/70 mt-1.5 leading-snug">{row.val}</div>
                      </div>
                    ))}
                  </div>
                  <button onClick={() => onSelect?.(c.compound)} className="btn-primary mt-3 w-full !px-4 !py-2 !text-xs">View compound →</button>
                </div>
              )}
            </div>
          ))}
        </div>
        {/* Wide grid table for md screens and up (horizontally scrollable) */}
        <div className="hidden md:block min-w-[980px]">
          <div className="grid grid-cols-12 gap-0 bg-cream-50 border-b border-forest-900/10 text-[10px] tracking-widest uppercase text-forest-700/60 px-4 py-2.5 dark:bg-white/5">
            <span className="col-span-1">#</span>
            <span className="col-span-3">Compound</span>
            <span className="col-span-2">Library</span>
            <span className="col-span-2">Shape fit</span>
            <span className="col-span-2">Prediction</span>
            <span className="col-span-2">Why + research</span>
          </div>

          {candidates.map((c, idx) => (
            <div key={c.compound.id} className={`grid grid-cols-12 gap-0 px-4 py-3 border-b border-forest-900/5 hover:bg-forest-50/50 dark:hover:bg-white/5 transition ${idx === 0 ? 'bg-gold-50/60 dark:bg-gold-400/5' : 'bg-white dark:bg-transparent'}`}>
              <div className="col-span-1 flex items-center gap-2">
                <span className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold ${idx === 0 ? 'bg-gold-500 text-white' : idx < 3 ? 'bg-forest-700 text-white' : 'bg-cream-200 text-forest-700 dark:bg-white/10 dark:text-cream-100'}`}>{c.rank}</span>
              </div>

              <div className="col-span-3 min-w-0">
                <div className="font-display font-semibold text-sm text-forest-950 dark:text-cream-50 truncate">{c.compound.name}</div>
                <div className="text-[11px] text-forest-700/60 dark:text-cream-100/50 truncate">{c.compound.id} · {c.compound.plant?.slice(0, 28)}</div>
                <div className="mt-1 flex gap-1">
                  <ConfidenceBadge tier="DATABASE_DERIVED" size="sm" showLabel={false} />
                </div>
              </div>

              <div className="col-span-2">
                <div className="rounded-xl bg-forest-50 border border-forest-900/10 p-2 dark:bg-white/5">
                  <div className="text-[10px] text-forest-700">Balance {c.database?.qed?.toFixed(2)}</div>
                  <div className="text-[11px] text-forest-800/80 dark:text-cream-100/70 mt-1">{c.compound.formula}</div>
                </div>
              </div>

              <div className="col-span-2">
                <div className="rounded-xl bg-cream-100 border border-gold-300/50 p-2 dark:bg-white/5">
                  <div className="text-xs font-bold text-forest-800 dark:text-cream-50">{c.docking?.affinity_kcal_mol?.toFixed(1)} fit score</div>
                  <div className="text-[10px] text-forest-700/70 dark:text-cream-100/60 mt-1">{fitVerdict(c.docking?.affinity_kcal_mol)} · computer guess</div>
                </div>
              </div>

              <div className="col-span-2">
                <div className="rounded-xl bg-gold-50 border border-gold-300/50 p-2 dark:bg-white/5">
                  {hasTier(c, 'ML_PREDICTION') ? (
                    <>
                      <div className="text-xs font-bold text-forest-800 dark:text-cream-50">Strength {c.ml?.pKd_pred?.toFixed(1)}</div>
                      <div className="text-[10px] text-forest-700/70 dark:text-cream-100/60 mt-1">Trust {Math.round((c.ml?.applicability || 0) * 100)}% · model guess</div>
                    </>
                  ) : (
                    <div className="text-[10px] italic text-forest-700/60 dark:text-cream-100/50">Not scored for this shortlist</div>
                  )}
                </div>
              </div>

              <div className="col-span-2 flex flex-col gap-1">
                <div className="rounded-xl bg-cream-50 border border-forest-900/10 p-1.5 dark:bg-white/5">
                  <div className="text-[10px] text-forest-700/80 dark:text-cream-100/70 truncate">Why: {hasTier(c, 'XAI_INTERPRETATION') ? plainTop(c.xai?.topFeature) : 'not explained here'}</div>
                </div>
                <div className="rounded-xl bg-forest-50 border border-forest-900/10 p-1.5 dark:bg-white/5">
                  <div className="text-[10px] text-forest-700 dark:text-cream-100/70">
                    {hasTier(c, 'LITERATURE_DERIVED') ? `${c.literature?.citations} papers · ${Math.round((c.literature?.faithfulness || 0) * 100)}% grounded` : 'Papers not checked here'}
                  </div>
                </div>
                <button onClick={() => setExpanded(expanded === c.compound.id ? null : c.compound.id)} className="mt-1 text-[11px] font-medium text-forest-700 hover:text-forest-900 dark:text-cream-100 transition active:scale-95">
                  {expanded === c.compound.id ? 'Hide breakdown' : 'See breakdown'}
                </button>
              </div>

              {expanded === c.compound.id && (
                <div className="col-span-12 mt-3 rounded-2xl border border-forest-900/10 bg-cream-50 p-3 dark:bg-white/5">
                  <TierSeparator tiersPresent={c.tiersPresent} />
                  <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-2 mt-2">
                    {[
                      { tier: 'DATABASE_DERIVED', val: `Balance ${c.database?.qed?.toFixed(2)} · ${c.compound.plant}` },
                      { tier: 'DOCKING_RESULT', val: `${c.docking?.affinity_kcal_mol?.toFixed(2)} fit score` },
                      { tier: 'ML_PREDICTION', val: hasTier(c, 'ML_PREDICTION') ? `Strength ${c.ml?.pKd_pred?.toFixed(2)}` : 'Not computed for this shortlist' },
                      { tier: 'XAI_INTERPRETATION', val: hasTier(c, 'XAI_INTERPRETATION') ? plainTop(c.xai?.topFeature) : 'Not computed for this shortlist' },
                      { tier: 'LITERATURE_DERIVED', val: hasTier(c, 'LITERATURE_DERIVED') ? `${c.literature?.citations} papers` : 'Not computed for this shortlist' },
                    ].map((row) => (
                      <div key={row.tier} className="rounded-xl bg-white border border-forest-900/10 p-2 dark:bg-white/5">
                        <ConfidenceBadge tier={row.tier} size="sm" />
                        <div className="text-[11px] text-forest-800/80 dark:text-cream-100/70 mt-2 leading-tight">{row.val}</div>
                      </div>
                    ))}
                  </div>
                  <div className="mt-3 flex gap-2 flex-wrap items-center">
                    <button onClick={() => onSelect?.(c.compound)} className="btn-primary !px-4 !py-1.5 !text-xs">View compound →</button>
                    <span className="text-[10px] text-forest-700/60 dark:text-cream-100/50">Each column is a separate clue — never blended into one health score.</span>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      <div className="px-5 py-3 bg-cream-50 border-t border-forest-900/10 flex items-center justify-between flex-wrap gap-2 dark:bg-white/5">
        <span className="text-[11px] text-forest-700/70 dark:text-cream-100/60">A shortlist for researchers — every pick still needs lab testing.</span>
        <button className="btn-secondary !px-3 !py-1 !text-[11px] shrink-0">Download list</button>
      </div>
    </div>
  );
}

function plainTop(raw) {
  if (!raw) return 'pattern mix';
  return String(raw)
    .replace(/lactone chemotype/i, 'ring pattern')
    .replace(/SHAP/i, 'push score')
    .replace(/ECFP4[^,]*/gi, 'fragment pattern');
}

