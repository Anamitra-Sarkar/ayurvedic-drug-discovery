/**
 * SearchBar.jsx — plain-language plant & compound search.
 */
import { useState, useEffect, useRef } from 'react';
import { ConfidenceBadge } from './ui.jsx';

export default function SearchBar({ onSearch, loading, results, onSelect }) {
  const [q, setQ] = useState('');
  const [plantFilter, setPlantFilter] = useState('');
  const [showResults, setShowResults] = useState(false);
  const ref = useRef(null);

  useEffect(() => {
    const handler = (e) => {
      if (ref.current && !ref.current.contains(e.target)) setShowResults(false);
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  const handleSubmit = (e) => {
    e.preventDefault();
    setShowResults(true);
    onSearch?.(q, { plant: plantFilter });
  };

  const data = results?.data || [];

  return (
    <div ref={ref} className="relative">
      <form onSubmit={handleSubmit} className="card p-3 flex flex-col md:flex-row gap-3 items-stretch">
        <div className="flex-1 relative">
          <span className="absolute left-3 top-1/2 -translate-y-1/2 text-forest-600/50">⌕</span>
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            onFocus={() => q && setShowResults(true)}
            placeholder="Search plants or compounds — try Ashwagandha, Turmeric, Amla…"
            className="w-full pl-9 pr-3 py-2.5 rounded-2xl border border-forest-900/10 bg-cream-50 focus:bg-white focus:outline-none focus:ring-2 focus:ring-forest-600/20 focus:border-forest-600 text-sm dark:bg-white/5 dark:border-white/10 dark:text-cream-50"
            aria-label="Search plants or compounds"
          />
        </div>
        <div className="flex flex-col sm:flex-row gap-2">
          <div className="relative min-w-0 flex-1">
            <select
              value={plantFilter}
              onChange={(e) => setPlantFilter(e.target.value)}
              className="w-full appearance-none px-3 py-2.5 pr-9 rounded-2xl border border-forest-900/10 bg-white text-sm text-forest-950 dark:bg-white/5 dark:border-white/10 dark:text-cream-50 focus:outline-none focus:ring-2 focus:ring-forest-600/20 focus:border-forest-600 transition-shadow"
              aria-label="Filter by plant"
            >
              <option value="">All plants</option>
              <option>Withania somnifera</option>
              <option>Curcuma longa</option>
              <option>Phyllanthus emblica</option>
              <option>Terminalia chebula</option>
              <option>Terminalia bellirica</option>
              <option>Berberis aristata</option>
            </select>
            <span className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-forest-700/50 dark:text-cream-100/50 text-xs">▾</span>
          </div>
          <button disabled={loading} type="submit" className="btn-primary w-full sm:w-auto shrink-0 !py-2.5">
            {loading ? <span className="spinner" /> : 'Search'}
          </button>
        </div>
        <div className="hidden md:flex items-center gap-2 pl-2 border-l border-forest-900/10">
          <ConfidenceBadge tier="DATABASE_DERIVED" size="sm" />
        </div>
      </form>

      {showResults && (
        <div className="modal-panel absolute z-30 mt-2 w-full rounded-3xl border border-forest-900/10 bg-white shadow-lift overflow-hidden max-h-[60vh] sm:max-h-[420px] flex flex-col dark:bg-forest-900 dark:border-white/10">
          <div className="px-4 py-2.5 border-b border-forest-900/10 bg-cream-50 flex items-center justify-between dark:bg-white/5">
            <div className="text-[11px] tracking-wide text-forest-700 dark:text-cream-100/70">
              Plant library · {results?.count ?? data.length} matches
            </div>
            <button onClick={() => setShowResults(false)} className="text-[11px] px-2.5 py-1 rounded-full bg-white border border-forest-900/10 hover:shadow-card transition active:scale-95 dark:bg-white/10 dark:text-cream-50">
              ✕ Close
            </button>
          </div>
          <div className="overflow-auto">
            {data.length === 0 ? (
              <div className="p-8 text-center">
                <div className="text-3xl">🌱</div>
                <div className="text-sm text-forest-800 dark:text-cream-100 mt-2 font-medium">No matches for “{q || 'your search'}”.</div>
                <div className="text-xs text-forest-700/70 dark:text-cream-100/60 mt-1">Try “Ashwagandha”, “Turmeric”, or part of a name — spelling can be tricky.</div>
              </div>
            ) : data.map((c) => (
                <button key={c.id} onClick={() => { onSelect?.(c); setShowResults(false); }} className="w-full text-left px-3 sm:px-4 py-3 border-b last:border-0 border-forest-900/5 hover:bg-forest-50/60 dark:hover:bg-white/5 flex items-center justify-between gap-3 transition active:scale-[0.99]">
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2 min-w-0 flex-wrap">
                    <span className="font-display font-semibold text-sm text-forest-950 dark:text-cream-50 truncate">{c.name}</span>
                    <span className="text-[10px] shrink-0 px-1.5 py-0.5 rounded bg-cream-100 border border-forest-900/10 dark:bg-white/10">{c.id}</span>
                    {c.drugLikeness?.qed && (
                      <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-forest-50 border border-forest-200 text-forest-700">
                        Balance {c.drugLikeness.qed.toFixed(2)}
                      </span>
                    )}
                  </div>
                  <div className="text-[11px] text-forest-700/70 dark:text-cream-100/60 truncate mt-0.5">{c.plant} · {c.formula} · {c.ayurvedicName}</div>
                </div>
                <span className="text-[11px] shrink-0 font-medium text-forest-700">View →</span>
              </button>
            ))}
          </div>
          <div className="px-4 py-2 bg-gold-50 border-t border-gold-300/50 text-[11px] text-gold-700 dark:bg-gold-400/10 dark:text-gold-300">
            Library entries describe plants and compounds — not health effects.
          </div>
        </div>
      )}
    </div>
  );
}
