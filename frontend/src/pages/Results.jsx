/**
 * Results.jsx — "/results/:id" tabbed result page.
 * Tabs: Overview | 3D Shape | Why? | Research. Data calls unchanged.
 */
import { useEffect, useState } from 'react';
import { useParams, Link, useSearchParams } from 'react-router-dom';
import { apiClient } from '../services/api.js';
import CompoundCard from '../components/CompoundCard.jsx';
import MoleculeViewer from '../components/MoleculeViewer.jsx';
import DockingResults from '../components/DockingResults.jsx';
import MLPredictionCard from '../components/MLPredictionCard.jsx';
import XAIExplanation from '../components/XAIExplanation.jsx';
import LiteraturePanel from '../components/LiteraturePanel.jsx';
import { Page, LoadingSpinner, SkeletonCard, ResearchNote, EmptyState } from '../components/ui.jsx';
import { proteinShapeName } from '../utils/friendly.js';

const TABS = [
  { id: 'overview', label: 'Overview', icon: '🌿' },
  { id: 'shape', label: '3D Shape', icon: '🧩' },
  { id: 'why', label: 'Why this result?', icon: '💡' },
  { id: 'research', label: 'Research', icon: '📖' },
];

export default function Results() {
  const { id } = useParams();
  const [params] = useSearchParams();
  const shapeCode = params.get('shape') || '6LU7';
  const [tab, setTab] = useState('overview');
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
      // Docking/ML/XAI all need a real SMILES string, not the compound ID
      // (e.g. "IMP000013") - resolve the compound first so downstream calls
      // send real chemistry instead of an ID string in the smiles field.
      const c = await apiClient.getCompound(id);
      const smiles = c?.smiles;
      const [d, m, x, l] = await Promise.all([
        smiles ? apiClient.runDocking(smiles, shapeCode, id) : Promise.resolve(null),
        smiles ? apiClient.predictAffinity(smiles, shapeCode) : Promise.resolve(null),
        smiles ? apiClient.explainPrediction(smiles, shapeCode) : Promise.resolve(null),
        apiClient.queryLiterature(`${c?.name || id} natural compound protein`),
      ]);
      setCompound(c); setFit(d); setGuess(m); setWhy(x); setPapers(l);
    } catch (e) {
      const status = e?.response?.status;
      if (status === 404) {
        setError('We could not find that result.');
      } else {
        setError('We could not load these results right now. Please try again in a moment.');
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id, shapeCode]);

  return (
    <Page className="space-y-5">
      <div className="flex items-center gap-2 text-[12px] text-forest-700/70 dark:text-cream-100/60">
        <Link to="/compounds" className="hover:text-forest-900">Compounds</Link><span>/</span>
        <Link to={`/compounds/${id}`} className="hover:text-forest-900">{compound?.name || id}</Link><span>/</span>
        <span className="font-semibold text-forest-950 dark:text-cream-50">Results · {proteinShapeName(shapeCode)}</span>
      </div>

      <div>
        <h1 className="font-display text-3xl font-semibold text-forest-950 dark:text-cream-50">
          {compound?.name || 'Loading…'} <span className="text-forest-700/60 dark:text-cream-100/50 text-xl">× {proteinShapeName(shapeCode)}</span>
        </h1>
        <p className="mt-1 text-sm text-forest-800/75 dark:text-cream-100/65 max-w-2xl">
          How this compound compares with this protein shape — four short tabs, plain words throughout.
        </p>
      </div>

      {/* Tabs */}
      <div className="card flex gap-1.5 overflow-x-auto p-2" role="tablist" aria-label="Result sections">
        {TABS.map((t) => (
          <button
            key={t.id}
            role="tab"
            aria-selected={tab === t.id}
            onClick={() => setTab(t.id)}
            className={`flex flex-1 shrink-0 min-w-[130px] sm:min-w-0 items-center justify-center gap-2 whitespace-nowrap rounded-2xl px-4 py-2.5 text-sm font-medium transition active:scale-[0.98] ${tab === t.id ? 'bg-forest-700 text-white shadow-card' : 'text-forest-800 hover:bg-cream-100 dark:text-cream-100 dark:hover:bg-white/10'}`}
          >
            <span>{t.icon}</span>{t.label}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="space-y-4"><SkeletonCard /><LoadingSpinner label="Gathering the four result tabs…" /></div>
      ) : error ? (
        <EmptyState
          icon="😕"
          title="Something didn't load"
          hint={error}
          action={<button className="btn-secondary" onClick={load}>Try again</button>}
        />
      ) : (
        <div key={tab} className="page-wrap">
          {tab === 'overview' && (
            <div className="grid gap-5 lg:grid-cols-2">
              {compound && <CompoundCard compound={compound} />}
              <div className="space-y-5">
                <DockingResults result={fit} />
                <MLPredictionCard prediction={guess} />
              </div>
            </div>
          )}
          {tab === 'shape' && (
            <div className="grid gap-5 lg:grid-cols-5">
              <div className="lg:col-span-3"><MoleculeViewer dockingResult={fit} proteinPDB={fit?.protein_pdb} ligandPDB={fit?.ligand_pdb} height={440} /></div>
              <div className="lg:col-span-2"><DockingResults result={fit} /></div>
            </div>
          )}
          {tab === 'why' && (
            <div className="grid gap-5 lg:grid-cols-2">
              <MLPredictionCard prediction={guess} />
              <XAIExplanation explanation={why} />
            </div>
          )}
          {tab === 'research' && (
            <div className="max-w-3xl"><LiteraturePanel literature={papers} query={`${compound?.name} research`} /></div>
          )}
        </div>
      )}

      <ResearchNote />
      <div className="flex flex-wrap gap-2">
        <Link to={`/compounds/${id}`} className="btn-secondary !text-xs">← Back to compound page</Link>
        <Link to="/ranking" className="btn-secondary !text-xs">See the full shortlist →</Link>
      </div>
    </Page>
  );
}
