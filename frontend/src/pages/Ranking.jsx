/**
 * Ranking.jsx — "/ranking" shortlist page.
 */
import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import CandidateRankingTable from '../components/CandidateRankingTable.jsx';
import { Page, LoadingSpinner, EmptyState } from '../components/ui.jsx';
import { PROTEIN_SHAPES, proteinShapeName } from '../utils/friendly.js';
import { apiClient } from '../services/api.js';

export default function Ranking() {
  const [shape, setShape] = useState('6LU7');
  const [ranking, setRanking] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const load = async (target) => {
    setLoading(true);
    setError(null);
    try {
      const r = await apiClient.getRankedCandidates(target, 8);
      setRanking(r);
    } catch {
      setError('We could not load the shortlist right now. Please try again in a moment.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load(shape);
  }, [shape]);

  return (
    <Page className="space-y-5">
      <div>
        <h1 className="font-display text-3xl md:text-4xl font-semibold text-forest-950 dark:text-cream-50">This week’s shortlist</h1>
        <p className="mt-2 max-w-2xl text-[15px] leading-relaxed text-forest-800/80 dark:text-cream-100/70">
          The compounds our computer finds most interesting for <strong>{proteinShapeName(shape)}</strong> —
          ordered by early guesses, with the reasoning shown for each. A high spot is a nudge to study more, never a health claim.
        </p>
      </div>

      <div className="card flex flex-wrap items-center gap-2 p-3">
        <span className="text-xs uppercase tracking-widest text-forest-700/60 dark:text-cream-100/50 ml-1">Compare with</span>
        {PROTEIN_SHAPES.map((p) => (
          <button
            key={p.code}
            onClick={() => setShape(p.code)}
            className={`rounded-full px-4 py-2 text-xs font-medium border transition active:scale-95 ${shape === p.code ? 'bg-forest-700 text-white border-forest-700' : 'bg-white border-forest-900/10 text-forest-800 hover:shadow-card dark:bg-white/5 dark:text-cream-100'}`}
          >
            {p.name}
          </button>
        ))}
      </div>

      {loading && <LoadingSpinner label="Ordering the shortlist…" />}
      {!loading && error && (
        <EmptyState
          icon="😕"
          title="Something didn't load"
          hint={error}
          action={<button className="btn-secondary" onClick={() => load(shape)}>Try again</button>}
        />
      )}
      {!error && <CandidateRankingTable ranking={ranking} loading={loading} onSelect={() => {}} />}

      <div className="flex flex-wrap gap-2">
        <Link to="/network" className="btn-secondary !text-xs">See how plants connect →</Link>
        <Link to="/pipeline" className="btn-secondary !text-xs">Test your own pick →</Link>
      </div>
    </Page>
  );
}
