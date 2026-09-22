/**
 * CompoundDetail.jsx — "/compounds/:id" single compound page, plain language.
 * Same five API calls; presented as friendly sections with tabs.
 */
import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { apiClient } from '../services/api.js';
import CompoundCard from '../components/CompoundCard.jsx';
import MoleculeViewer from '../components/MoleculeViewer.jsx';
import DockingResults from '../components/DockingResults.jsx';
import MLPredictionCard from '../components/MLPredictionCard.jsx';
import XAIExplanation from '../components/XAIExplanation.jsx';
import LiteraturePanel from '../components/LiteraturePanel.jsx';
import { Page, LoadingSpinner, SkeletonCard, ResearchNote, EmptyState } from '../components/ui.jsx';
import { ConfidenceLegend } from '../components/ui.jsx';

const SECTIONS = [
  { id: 'story', label: 'Plant story' },
  { id: 'shape', label: '3D shape' },
  { id: 'scores', label: 'Scores & why' },
  { id: 'reading', label: 'Further reading' },
];

export default function CompoundDetail() {
  const { id } = useParams();
  const [section, setSection] = useState('story');
  const [compound, setCompound] = useState(null);
  const [fit, setFit] = useState(null);
  const [guess, setGuess] = useState(null);
  const [why, setWhy] = useState(null);
  const [papers, setPapers] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const [c, d, m, x, l] = await Promise.all([
        apiClient.getCompound(id),
        apiClient.runDocking(id, '6LU7'),
        apiClient.predictAffinity(id, '6LU7'),
        apiClient.explainPrediction(id, '6LU7'),
        apiClient.queryLiterature(`${id} natural compound plant`),
      ]);
      setCompound(c); setFit(d); setGuess(m); setWhy(x); setPapers(l);
    } catch (e) {
      const status = e?.response?.status;
      if (status === 404) {
        setError('We could not find that compound.');
      } else {
        setError('We could not load this compound right now. Please try again in a moment.');
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, [id]);

  if (loading) {
    return (
      <Page className="space-y-4">
        <SkeletonCard />
        <LoadingSpinner label={`Opening ${id}…`} />
      </Page>
    );
  }

  if (error) {
    return (
      <Page className="space-y-4">
        <EmptyState
          icon="😕"
          title="Something didn't load"
          hint={error}
          action={<button className="btn-secondary" onClick={load}>Try again</button>}
        />
        <div className="flex flex-wrap gap-2">
          <Link to="/compounds" className="btn-secondary !text-xs">← Back to compounds</Link>
        </div>
      </Page>
    );
  }

  return (
    <Page className="space-y-5">
      <div className="flex items-center gap-2 text-[12px] text-forest-700/70 dark:text-cream-100/60">
        <Link to="/compounds" className="hover:text-forest-900">Compounds</Link><span>/</span>
        <span className="text-forest-950 dark:text-cream-50 font-semibold">{compound?.name}</span>
      </div>

      <div>
        <h1 className="font-display text-3xl md:text-4xl font-semibold text-forest-950 dark:text-cream-50">{compound?.name}</h1>
        <p className="mt-1 text-sm text-forest-800/75 dark:text-cream-100/65">
          {compound?.plant} · everything below is an early computer preview for research.
        </p>
      </div>

      <div className="card flex gap-1.5 overflow-x-auto scrollbar-hide p-2" role="tablist" aria-label="Compound sections">
        {SECTIONS.map((s) => (
          <button
            key={s.id}
            role="tab"
            aria-selected={section === s.id}
            onClick={() => setSection(s.id)}
            className={`shrink-0 flex-1 min-w-[120px] sm:min-w-0 whitespace-nowrap rounded-2xl px-4 py-2.5 text-sm font-medium transition active:scale-[0.98] ${section === s.id ? 'bg-forest-700 text-white shadow-card' : 'text-forest-800 hover:bg-cream-100 dark:text-cream-100 dark:hover:bg-white/10'}`}
          >
            {s.label}
          </button>
        ))}
      </div>

      <div key={section} className="page-wrap">
        {section === 'story' && (
          <div className="grid gap-5 lg:grid-cols-2">
            {compound && <CompoundCard compound={compound} />}
            <div className="space-y-5">
              <div className="card p-6">
                <h2 className="font-display text-lg font-semibold text-forest-950 dark:text-cream-50">🌿 The plant story</h2>
                <p className="mt-2 text-sm leading-relaxed text-forest-900/85 dark:text-cream-100/80">
                  {compound?.name} is found in <strong>{compound?.plant}</strong>
                  {compound?.traditionalUse ? <> and is traditionally associated with <strong>{compound.traditionalUse}</strong></> : null}.
                  Library records like this are our starting point — they describe the plant, not health effects.
                </p>
                <div className="mt-3"><ConfidenceLegend /></div>
              </div>
              <LiteraturePanel literature={papers} query={`${compound?.name} plant`} />
            </div>
          </div>
        )}
        {section === 'shape' && (
          <div className="grid gap-5 lg:grid-cols-5">
            <div className="lg:col-span-3"><MoleculeViewer dockingResult={fit} height={440} /></div>
            <div className="lg:col-span-2"><DockingResults result={fit} /></div>
          </div>
        )}
        {section === 'scores' && (
          <div className="grid gap-5 lg:grid-cols-2">
            <MLPredictionCard prediction={guess} />
            <XAIExplanation explanation={why} />
          </div>
        )}
        {section === 'reading' && (
          <div className="max-w-3xl space-y-5">
            <LiteraturePanel literature={papers} query={`${compound?.name} research`} />
            <ResearchNote />
          </div>
        )}
      </div>

      <div className="flex flex-wrap gap-2">
        <Link to={`/results/${id}?shape=6LU7`} className="btn-primary !text-xs">Open the tabbed results view →</Link>
        <Link to="/ranking" className="btn-secondary !text-xs">Back to the shortlist</Link>
      </div>
    </Page>
  );
}
