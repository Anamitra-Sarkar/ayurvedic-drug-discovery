/**
 * Targets.jsx — "/targets" protein-shape browse page.
 * Tries the real endpoint (/api/pipeline/targets); otherwise shows a
 * clearly-marked starter list with a loading/placeholder state — no fake numbers.
 */
import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Page, LoadingSpinner, EmptyState, SkeletonCard } from '../components/ui.jsx';
import { PROTEIN_SHAPES } from '../utils/friendly.js';
import { apiClient } from '../services/api.js';

export default function Targets() {
  const [shapes, setShapes] = useState(null);
  const [loading, setLoading] = useState(true);
  const [fromLive, setFromLive] = useState(false);

  useEffect(() => {
    (async () => {
      setLoading(true);
      try {
        const live = await apiClient.getTargets?.();
        if (live && (live.targets || live.data || Array.isArray(live))) {
          const arr = live.targets || live.data || live;
          if (Array.isArray(arr) && arr.length > 0) {
            setShapes(arr.map((t, i) => ({
              code: t.code || t.id || t.pdb || `shape-${i}`,
              name: t.name || t.label || 'Protein shape',
              hint: t.hint || t.organism || 'Target under study',
              plantContext: t.plantContext || '',
              live: true,
            })));
            setFromLive(true);
            setLoading(false);
            return;
          }
        }
      } catch { /* fall through to starter list */ }
      // Clearly-marked starter list: codes are real, friendly names are generic.
      setShapes(PROTEIN_SHAPES.map((p) => ({ ...p, live: false })));
      setFromLive(false);
      setLoading(false);
    })();
  }, []);

  return (
    <Page className="space-y-6">
      <div>
        <h1 className="font-display text-3xl md:text-4xl font-semibold text-forest-950 dark:text-cream-50">Protein shapes to explore</h1>
        <p className="mt-2 max-w-2xl text-[15px] leading-relaxed text-forest-800/80 dark:text-cream-100/70">
          Each “shape” is a 3D protein scientists study. We test how snugly natural compounds fit inside it —
          a geometry game, not a health claim.
        </p>
        {!loading && !fromLive && (
          <p className="mt-2 inline-block rounded-full bg-gold-50 border border-gold-300/60 px-3 py-1 text-xs text-gold-700 dark:bg-gold-400/10 dark:text-gold-300">
            Showing a starter list while the live catalogue loads — scores will appear after you run an analysis.
          </p>
        )}
      </div>

      {loading ? (
        <div className="grid gap-4 sm:grid-cols-2"><SkeletonCard /><SkeletonCard /></div>
      ) : !shapes || shapes.length === 0 ? (
        <EmptyState icon="🧬" title="Shapes are loading" hint="Please check back in a moment — the catalogue is still waking up." />
      ) : (
        <div className="grid gap-4 sm:grid-cols-2">
          {shapes.map((s) => (
            <div key={s.code} className="card card-lift p-6">
              <div className="flex items-start justify-between gap-3">
                <div className="flex items-center gap-3">
                  <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-forest-700 text-xl text-white">🧬</div>
                  <div>
                    <h2 className="font-display text-lg font-semibold text-forest-950 dark:text-cream-50">{s.name}</h2>
                    <p className="text-xs text-forest-700/70 dark:text-cream-100/60">Shape code {s.code} · {s.hint}</p>
                  </div>
                </div>
              </div>
              {s.plantContext && <p className="mt-3 text-xs text-forest-800/75 dark:text-cream-100/65">Often explored with: {s.plantContext}</p>}
              {s.live ? (
                <p className="mt-2 text-xs text-forest-700">Live catalogue entry — open the shortlist to see its numbers.</p>
              ) : (
                <p className="mt-2 text-xs text-forest-700/60 dark:text-cream-100/50">Preview entry — real fit scores load after analysis.</p>
              )}
              <div className="mt-4 flex flex-wrap gap-2">
                <Link to="/ranking" className="btn-primary !px-5 !py-2 !text-xs">See shortlist →</Link>
                <Link to="/pipeline" className="btn-secondary !px-5 !py-2 !text-xs">Test a compound</Link>
              </div>
            </div>
          ))}
        </div>
      )}
      {loading && <LoadingSpinner label="Loading protein shapes…" />}
    </Page>
  );
}
