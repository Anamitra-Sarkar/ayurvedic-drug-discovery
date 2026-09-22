/**
 * DockingResults.jsx — plain-language "Shape fit test".
 * Numbers come straight from the API; only labels/explanations changed.
 */
import { ConfidenceBadge, HowCalculated, ResearchNote } from './ui.jsx';
import { fitScoreToMeter, fitVerdict } from '../utils/friendly.js';

export default function DockingResults({ result, loading }) {
  if (loading) {
    return (
      <div className="rounded-3xl border border-forest-900/10 bg-white p-6 animate-pulse dark:bg-forest-900">
        <div className="h-4 bg-cream-200 rounded w-1/3 mb-4 dark:bg-white/10" />
        <div className="h-24 bg-cream-100 rounded-2xl dark:bg-white/5" />
      </div>
    );
  }
  if (!result) {
    return (
      <div className="card p-8 text-center">
        <div className="text-3xl">🧩</div>
        <div className="text-sm text-forest-800 dark:text-cream-100 mt-2 font-medium">No shape-fit test yet</div>
        <div className="text-xs text-forest-700/70 dark:text-cream-100/60 mt-1">Run an analysis to see how this compound fits the protein shape.</div>
      </div>
    );
  }

  const poses = result.poses || [];
  const interactions = result.interactions || [];
  const meter = fitScoreToMeter(result.affinity_kcal_mol);

  return (
    <div className="card overflow-hidden">
      <div className="px-5 py-4 border-b border-forest-900/10 bg-forest-50/60 flex items-center justify-between dark:bg-white/5">
        <div className="flex items-center gap-2.5">
          <div className="w-9 h-9 rounded-2xl bg-forest-700 text-white flex items-center justify-center">🧩</div>
          <div>
            <div className="font-display font-semibold text-[15px] text-forest-950 dark:text-cream-50">
              Shape fit test
              <HowCalculated title="shape fit test">
                The computer rotates the compound inside the 3D protein shape thousands of ways and scores each try. The best score is shown here. Lower (more negative) numbers mean a snugger fit. It is a geometry guess — it cannot tell us what happens in real life.
              </HowCalculated>
            </div>
            <div className="text-[11px] text-forest-700/75 dark:text-cream-100/60">
              {fitVerdict(result.affinity_kcal_mol)} · score {result.affinity_kcal_mol}
            </div>
          </div>
        </div>
        <ConfidenceBadge tier="DOCKING_RESULT" />
      </div>

      {meter != null && (
        <div className="px-5 pt-4">
          <div className="flex items-center justify-between text-[11px] text-forest-700 dark:text-cream-100/70 mb-1.5">
            <span className="font-semibold tracking-wide uppercase">Match strength</span>
            <span>{meter}/100 · {fitVerdict(result.affinity_kcal_mol)}</span>
          </div>
          <div className="h-2.5 rounded-full bg-cream-200 dark:bg-white/10 overflow-hidden">
            <div
              className="h-full rounded-full bg-gradient-to-r from-forest-500 via-forest-600 to-gold-500 transition-all duration-700"
              style={{ width: `${meter}%` }}
            />
          </div>
        </div>
      )}

      <div className="grid grid-cols-3 divide-x divide-forest-900/10 border-b border-forest-900/10 mt-4">
        <div className="p-4 text-center">
          <div className="text-[10px] tracking-widest uppercase text-forest-700/70 dark:text-cream-100/60">Best fit score</div>
          <div className="font-display font-bold text-lg text-forest-950 dark:text-cream-50 mt-1">{result.affinity_kcal_mol}</div>
          <div className="text-[10px] text-forest-700/60 dark:text-cream-100/50 mt-1">Lower = snugger (a guess)</div>
        </div>
        <div className="p-4 text-center">
          <div className="text-[10px] tracking-widest uppercase text-forest-700/70 dark:text-cream-100/60">
            Steadiness
            <HowCalculated title="steadiness">How much the best poses wobble compared with each other. Steadier poses are a little more reassuring — but still only computer guesses.</HowCalculated>
          </div>
          <div className="font-display font-bold text-lg text-forest-950 dark:text-cream-50 mt-1">{result.rmsd ?? '0.00'}</div>
          <div className="text-[10px] text-forest-700/60 dark:text-cream-100/50 mt-1">How steady the pose looks</div>
        </div>
        <div className="p-4 text-center">
          <div className="text-[10px] tracking-widest uppercase text-forest-700/70 dark:text-cream-100/60">Fit styles</div>
          <div className="font-display font-bold text-lg text-forest-950 dark:text-cream-50 mt-1">{result.poseCluster ?? poses.length}</div>
          <div className="text-[10px] text-forest-700/60 dark:text-cream-100/50 mt-1">Different ways it can sit</div>
        </div>
      </div>

      <div className="p-5">
        <div className="text-[11px] tracking-wide font-semibold text-forest-800 dark:text-cream-100 mb-2 uppercase">Best attempts</div>
        <div className="rounded-2xl border border-forest-900/10 overflow-hidden">
          <div className="grid grid-cols-4 bg-cream-50 border-b border-forest-900/10 text-[10px] tracking-widest uppercase text-forest-700/60 px-3 py-2 dark:bg-white/5">
            <span>Try</span><span>Fit score</span><span>Wobble (low)</span><span>Wobble (high)</span>
          </div>
          {poses.map((p, i) => (
            <div key={i} className={`grid grid-cols-4 px-3 py-2 text-xs border-b last:border-0 border-forest-900/5 ${i === 0 ? 'bg-forest-50/60 font-semibold dark:bg-white/5' : 'bg-white dark:bg-transparent'}`}>
              <span>#{i + 1}</span><span className={p.affinity < -7 ? 'text-forest-700 font-bold' : ''}>{p.affinity}</span><span>{p.rmsd_lb}</span><span>{p.rmsd_ub}</span>
            </div>
          ))}
        </div>

        {interactions.length > 0 && (
          <div className="mt-4">
            <div className="text-[11px] tracking-wide font-semibold text-forest-800 dark:text-cream-100 mb-2 uppercase">Touch points with the protein</div>
            <div className="flex flex-wrap gap-2">
              {interactions.map((it, idx) => (
                <span key={idx} className="chip bg-white border-forest-900/10 text-xs dark:bg-white/5 dark:text-cream-100">
                  {it.type === 'H-bond' ? '🤝 Held' : it.type === 'Hydrophobic' ? '💧 Snug' : '🔗 Touch'} · {it.residue} · {it.distance}Å
                </span>
              ))}
            </div>
          </div>
        )}

        <div className="mt-4">
          <ResearchNote text="This fit score is a computer guess about 3D shape — a bit like testing puzzle pieces. It cannot tell us whether anything happens in real life. Lab testing is still needed." />
        </div>
      </div>
    </div>
  );
}
