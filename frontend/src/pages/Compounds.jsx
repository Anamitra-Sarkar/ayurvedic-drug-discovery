/**
 * Compounds.jsx — "/compounds" browse & search page.
 */
import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import SearchBar from '../components/SearchBar.jsx';
import CompoundCard from '../components/CompoundCard.jsx';
import { Page, LoadingSpinner, EmptyState, SkeletonCard } from '../components/ui.jsx';
import { apiClient } from '../services/api.js';

export default function Compounds() {
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(true);
  const [searching, setSearching] = useState(false);
  const [picked, setPicked] = useState(null);

  useEffect(() => {
    (async () => {
      setLoading(true);
      const res = await apiClient.searchCompounds('', {});
      setResults(res);
      setLoading(false);
    })();
  }, []);

  const handleSearch = async (q, filters) => {
    setSearching(true);
    const res = await apiClient.searchCompounds(q, filters);
    setResults(res);
    setSearching(false);
  };

  const list = results?.data || [];

  return (
    <Page className="space-y-6">
      <div>
        <h1 className="font-display text-3xl md:text-4xl font-semibold text-forest-950 dark:text-cream-50">Find a plant or compound</h1>
        <p className="mt-2 max-w-2xl text-[15px] leading-relaxed text-forest-800/80 dark:text-cream-100/70">
          Search by a familiar name — “Ashwagandha”, “Turmeric”, “Amla” — or by a compound like “Curcumin”.
          Each card shows a quick chemical snapshot in plain words.
        </p>
      </div>

      <SearchBar onSearch={handleSearch} loading={searching} results={results} onSelect={setPicked} />

      {picked && (
        <div className="card modal-panel border-2 !border-forest-600/30 p-2">
          <div className="rounded-3xl bg-cream-50 p-2 dark:bg-white/5">
            <CompoundCard compound={picked} />
          </div>
          <div className="flex gap-2 p-3">
            <Link to={`/compounds/${picked.id}`} className="btn-primary flex-1 !py-2.5">Open full page →</Link>
            <button onClick={() => setPicked(null)} className="btn-secondary">Close</button>
          </div>
        </div>
      )}

      {loading ? (
        <div className="grid gap-4 md:grid-cols-3">
          <SkeletonCard /><SkeletonCard /><SkeletonCard />
        </div>
      ) : list.length === 0 ? (
        <EmptyState
          icon="🌱"
          title="No matches found"
          hint="Try a shorter word — “Amla” instead of “Emblica officinalis” — or clear the plant filter."
          action={<button className="btn-secondary" onClick={() => handleSearch('', {})}>Show everything</button>}
        />
      ) : (
        <>
          <div className="flex items-center justify-between">
            <h2 className="font-display text-lg font-semibold text-forest-950 dark:text-cream-50">
              {results?.query ? `Matches for “${results.query}”` : 'Popular right now'}
            </h2>
            <span className="text-xs text-forest-700/60 dark:text-cream-100/50">{list.length} shown · from the plant library</span>
          </div>
          {searching && <LoadingSpinner label="Searching the plant library…" />}
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {list.map((c) => (
              <CompoundCard key={c.id} compound={c} onSelect={setPicked} />
            ))}
          </div>
        </>
      )}
    </Page>
  );
}
