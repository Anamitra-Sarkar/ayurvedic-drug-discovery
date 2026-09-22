/**
 * Network.jsx — "/network" plant-connections map page.
 */
import { useEffect, useState } from 'react';
import NetworkGraph from '../components/NetworkGraph.jsx';
import { Page, LoadingSpinner, EmptyState } from '../components/ui.jsx';
import { apiClient } from '../services/api.js';

export default function Network() {
  const [network, setNetwork] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const n = await apiClient.getTriphalaNetwork();
      setNetwork(n);
    } catch {
      setError('We could not draw the plant map right now. Please try again in a moment.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  return (
    <Page className="space-y-5">
      <div>
        <h1 className="font-display text-3xl md:text-4xl font-semibold text-forest-950 dark:text-cream-50">How plants connect</h1>
        <p className="mt-2 max-w-2xl text-[15px] leading-relaxed text-forest-800/80 dark:text-cream-100/70">
          A living map of <strong>Triphala</strong> — three fruits, their natural compounds, and the protein shapes
          those compounds were compared with. Drag your eyes across it: green dots are plants, purple are compounds, pink are protein shapes.
        </p>
      </div>
      {loading && <LoadingSpinner label="Drawing the plant map…" />}
      {!loading && error && (
        <EmptyState
          icon="😕"
          title="Something didn't load"
          hint={error}
          action={<button className="btn-secondary" onClick={load}>Try again</button>}
        />
      )}
      {!error && <NetworkGraph networkData={network} loading={loading} />}
      <div className="card p-5">
        <h2 className="font-display text-lg font-semibold text-forest-950 dark:text-cream-50">How to read this map 🌿</h2>
        <ul className="mt-2 space-y-1.5 text-sm text-forest-800/80 dark:text-cream-100/70 leading-relaxed">
          <li><strong>Big green dots</strong> — the three Triphala plants: Amla, Bibhitaki, Haritaki.</li>
          <li><strong>Small purple dots</strong> — natural compounds found in those plants.</li>
          <li><strong>Pink dots</strong> — protein shapes the compounds were compared with.</li>
          <li><strong>Grey lines</strong> — “this compound comes from this plant”. <strong>Pink lines</strong> — “compared with this shape”.</li>
        </ul>
        <p className="mt-3 text-xs text-forest-700/70 dark:text-cream-100/60">A busy, well-connected map hints at variety worth studying — never at health effects.</p>
      </div>
    </Page>
  );
}
