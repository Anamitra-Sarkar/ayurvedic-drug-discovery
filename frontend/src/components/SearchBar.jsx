
/**
 * SearchBar.jsx
 * IMPPAT search with evidence tier, plant filter
 */
import { useState, useEffect, useRef } from 'react';
import EvidenceTierBadge from './EvidenceTierBadge.jsx';

export default function SearchBar({ onSearch, loading, results, onSelect }) {
  const [q, setQ] = useState('');
  const [plantFilter, setPlantFilter] = useState('');
  const [showResults, setShowResults] = useState(false);
  const ref = useRef(null);

  useEffect(()=> {
    const handler = (e)=> {
      if (ref.current && !ref.current.contains(e.target)) setShowResults(false);
    };
    document.addEventListener('mousedown', handler);
    return ()=> document.removeEventListener('mousedown', handler);
  }, []);

  const handleSubmit = (e) => {
    e.preventDefault();
    setShowResults(true);
    onSearch?.(q, { plant: plantFilter });
  };

  const data = results?.data || [];

  return (
    <div ref={ref} className="relative">
      <form onSubmit={handleSubmit} className="rounded-2xl border border-slate-200 bg-white shadow-card p-3 flex flex-col md:flex-row gap-3 items-stretch">
        <div className="flex-1 relative">
          <span className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400">⌕</span>
          <input
            value={q}
            onChange={e=>setQ(e.target.value)}
            onFocus={()=> q && setShowResults(true)}
            placeholder="Search IMPPAT — e.g., Withaferin, Ashwagandha, Curcuma, IMPPAT ID..."
            className="w-full pl-9 pr-3 py-2.5 rounded-xl border border-slate-200 bg-slate-50 focus:bg-white focus:outline-none focus:ring-2 focus:ring-cyan-600/20 focus:border-cyan-600 font-mono text-sm"
          />
        </div>
        <div className="flex gap-2">
          <select value={plantFilter} onChange={e=>setPlantFilter(e.target.value)} className="px-3 py-2.5 rounded-xl border border-slate-200 bg-white text-sm font-mono">
            <option value="">All plants</option>
            <option>Withania somnifera</option>
            <option>Curcuma longa</option>
            <option>Phyllanthus emblica</option>
            <option>Terminalia chebula</option>
            <option>Terminalia bellirica</option>
            <option>Berberis aristata</option>
          </select>
          <button disabled={loading} type="submit" className="px-5 py-2.5 rounded-xl bg-slate-900 text-white text-sm font-medium hover:bg-black disabled:opacity-50 flex items-center gap-2">
            {loading ? <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" /> : 'Search'}
          </button>
        </div>
        <div className="hidden md:flex items-center gap-2 pl-2 border-l border-slate-100">
          <EvidenceTierBadge tier="DATABASE_DERIVED" size="sm" />
        </div>
      </form>

      {showResults && (
        <div className="absolute z-30 mt-2 w-full rounded-2xl border border-slate-200 bg-white shadow-xl overflow-hidden max-h-[420px] flex flex-col">
          <div className="px-4 py-2.5 border-b border-slate-100 bg-slate-50/70 flex items-center justify-between">
            <div className="font-mono text-[11px] tracking-widest text-slate-600">IMPPAT SEARCH — DATABASE_DERIVED • {results?.count ?? data.length} results {results?.source ? `• ${results.source}` : ''}</div>
            <button onClick={()=>setShowResults(false)} className="font-mono text-[11px] px-2 py-1 rounded-full bg-white border border-slate-200">✕ Close</button>
          </div>
          <div className="overflow-auto">
            {data.length===0 ? (
              <div className="p-8 text-center">
                <div className="font-mono text-sm text-slate-500">No compounds match "{q}". Try Ashwagandha, Turmeric, or partial IMPPAT ID.</div>
                <div className="font-mono text-[11px] text-slate-400 mt-2">Evidence tiers remain enforced even for empty results</div>
              </div>
            ) : data.map(c=>(
              <button key={c.id} onClick={()=>{onSelect?.(c); setShowResults(false);}} className="w-full text-left px-4 py-3 border-b last:border-0 border-slate-100 hover:bg-cyan-50/60 flex items-center justify-between gap-3 transition">
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <span className="font-display font-semibold text-sm text-slate-900 truncate">{c.name}</span>
                    <span className="font-mono text-[10px] px-1.5 py-0.5 rounded bg-slate-100 border border-slate-200">{c.id}</span>
                    {c.drugLikeness?.qed && <span className="font-mono text-[10px] px-1.5 py-0.5 rounded-full bg-green-50 border border-green-200 text-green-700">QED {c.drugLikeness.qed.toFixed(2)}</span>}
                  </div>
                  <div className="font-mono text-[11px] text-slate-500 truncate mt-0.5">{c.plant} • {c.formula} • {c.ayurvedicName}</div>
                </div>
                <span className="font-mono text-[11px] text-cyan-700">View →</span>
              </button>
            ))}
          </div>
          <div className="px-4 py-2 bg-amber-50 border-t border-amber-100 font-mono text-[10px] text-amber-800">DATABASE_DERIVED tier — botanical occurrence data, not efficacy. AYUSH-64 style: foundation only.</div>
        </div>
      )}
    </div>
  );
}
