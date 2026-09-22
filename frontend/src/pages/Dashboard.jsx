
/**
 * Dashboard.jsx - Main dashboard with search, pipeline flow, ranking
 */
import { useEffect, useState } from 'react';
import SearchBar from '../components/SearchBar.jsx';
import PipelineFlow from '../components/PipelineFlow.jsx';
import CandidateRankingTable from '../components/CandidateRankingTable.jsx';
import NetworkGraph from '../components/NetworkGraph.jsx';
import CompoundCard from '../components/CompoundCard.jsx';
import { apiClient } from '../services/api.js';
import { EvidenceTierLegend } from '../components/EvidenceTierBadge.jsx';

export default function Dashboard() {
  const [searchResults, setSearchResults] = useState(null);
  const [searchLoading, setSearchLoading] = useState(false);
  const [selectedCompound, setSelectedCompound] = useState(null);
  const [ranking, setRanking] = useState(null);
  const [rankingLoading, setRankingLoading] = useState(true);
  const [network, setNetwork] = useState(null);
  const [networkLoading, setNetworkLoading] = useState(true);
  const [activeLayer, setActiveLayer] = useState(null);

  useEffect(()=> {
    // Load ranking and Triphala network on mount
    (async ()=>{
      setRankingLoading(true);
      const r = await apiClient.getRankedCandidates('6LU7', 6);
      setRanking(r);
      setRankingLoading(false);
    })();
    (async ()=>{
      setNetworkLoading(true);
      const n = await apiClient.getTriphalaNetwork();
      setNetwork(n);
      setNetworkLoading(false);
    })();
  }, []);

  const handleSearch = async (q, filters) => {
    setSearchLoading(true);
    const res = await apiClient.searchCompounds(q, filters);
    setSearchResults(res);
    setSearchLoading(false);
  };

  const compoundsToShow = searchResults?.data?.slice(0,3) || ranking?.candidates?.map(c=>c.compound).slice(0,3) || [];

  return (
    <div className="space-y-6">
      {/* Hero */}
      <div className="rounded-[24px] bg-white border border-slate-200 p-6 md:p-8 shadow-card overflow-hidden relative">
        <div className="absolute -top-24 -right-24 w-[320px] h-[320px] bg-gradient-to-br from-amber-100 to-emerald-100 rounded-full blur-3xl opacity-60" />
        <div className="relative">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-slate-900 text-white font-mono text-[11px] tracking-widest">EVIDENCE-TIERED • AYUSH-64 COMPLIANT • NON-CLINICAL</div>
          <h1 className="font-display font-bold text-[26px] md:text-[32px] leading-[1.1] mt-4 max-w-4xl">
            AI-Driven Computational Pipeline for Ayurvedic Drug Discovery —
            <span className="text-slate-500"> IMPPAT to Candidate Ranking with 3Dmol.js</span>
          </h1>
          <p className="font-mono text-[13px] text-slate-600 mt-3 max-w-3xl leading-relaxed">
            Six functional layers (i) curated phytochemical DB (IMPPAT primary), (ii) RDKit cheminformatics, (iii) Vina docking, (iv) ML affinity prediction, (v) SHAP XAI, (vi) RAG literature — orchestrated via LangGraph-style state graph, surfaced through interactive web interface with molecular visualisation. Every output maps to one of five evidentiary tiers, with explicit disclaimer that computational prediction is not clinical proof — following AYUSH-64 case study justification.
          </p>
          <div className="mt-4 flex flex-wrap gap-2">
            <EvidenceTierLegend />
          </div>
        </div>
      </div>

      {/* Search */}
      <SearchBar onSearch={handleSearch} loading={searchLoading} results={searchResults} onSelect={setSelectedCompound} />

      {/* Selected compound preview + quick cards */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-8 space-y-6">
          <PipelineFlow activeLayer={activeLayer} onSelectLayer={setActiveLayer} />

          {/* Compound grid */}
          {compoundsToShow.length>0 && (
            <div>
              <div className="flex items-center justify-between mb-3">
                <h2 className="font-display font-semibold text-[15px]">Featured Phytochemicals — DATABASE_DERIVED tier</h2>
                <span className="font-mono text-[11px] text-slate-500">IMPPAT primary • {compoundsToShow.length} shown</span>
              </div>
              <div className="grid md:grid-cols-3 gap-4">
                {compoundsToShow.map(c=>(
                  <CompoundCard key={c.id} compound={c} onSelect={setSelectedCompound} />
                ))}
              </div>
            </div>
          )}

          {/* Ranking */}
          <CandidateRankingTable ranking={ranking} loading={rankingLoading} onSelect={setSelectedCompound} />
        </div>

        <div className="lg:col-span-4 space-y-6">
          {/* Selected compound detail mini */}
          {selectedCompound && (
            <div className="rounded-2xl border-2 border-slate-900 bg-white p-1 shadow-lg">
              <div className="rounded-xl bg-[#f8faf6] p-1">
                <CompoundCard compound={selectedCompound} />
              </div>
              <div className="p-3 flex gap-2">
                <a href={`/compound/${selectedCompound.id}`} className="flex-1 text-center px-3 py-2 rounded-full bg-slate-900 text-white text-sm font-medium">Open full detail →</a>
                <button onClick={()=>setSelectedCompound(null)} className="px-3 py-2 rounded-full border border-slate-200 bg-white text-sm">Close</button>
              </div>
            </div>
          )}

          {/* Quick stats */}
          <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-card">
            <div className="font-display font-semibold text-sm">Pipeline Status</div>
            <div className="mt-3 space-y-2">
              {[
                { l: 'IMPPAT DB', v: '4100+ phytochems', tier: 'DB', ok: true },
                { l: 'RDKit Service', v: 'ECFP4 2048-bit', tier: 'DB', ok: true },
                { l: 'Vina Docking', v: 'Mock physics fallback ready', tier: 'DOCK', ok: true },
                { l: 'ML Model', v: 'RF affinity-v1.2', tier: 'ML', ok: true },
                { l: 'SHAP XAI', v: 'TreeSHAP', tier: 'XAI', ok: true },
                { l: 'RAG / FAISS', v: 'TF-IDF fallback ok', tier: 'LIT', ok: true },
              ].map(row=>(
                <div key={row.l} className="flex items-center justify-between py-2 border-b last:border-0 border-slate-100">
                  <span className="font-mono text-xs text-slate-700">{row.l}</span>
                  <span className="flex items-center gap-2">
                    <span className="font-mono text-[11px] text-slate-500">{row.v}</span>
                    <span className={`w-2 h-2 rounded-full ${row.ok ? 'bg-green-500' : 'bg-amber-500'}`} />
                  </span>
                </div>
              ))}
            </div>
            <div className="mt-3 rounded-xl bg-amber-50 border border-amber-200 p-2.5 font-mono text-[10px] text-amber-800">
              Frontend runs fully without backend via realistic mock fallback that preserves evidence tier separation — backend FastAPI expected at /api but not required.
            </div>
          </div>

          {/* Triphala spotlight */}
          <div className="rounded-2xl border border-green-200 bg-green-50/40 p-4">
            <div className="font-display font-semibold text-sm">Case Study: Triphala — 174 Bioactives</div>
            <div className="font-mono text-[11px] text-green-800 mt-1 leading-relaxed">
              Triphala (Amalaki, Bibhitaki, Haritaki) network pharmacology demonstrates polyherbal synergy hypothesis. Graph below shows botanical co-occurrence vs predicted target edges. Follows AYUSH-64 style multi-component justification but does not constitute clinical proof of synergy.
            </div>
            <div className="mt-2 flex flex-wrap gap-1.5">
              <span className="px-2 py-1 rounded-full bg-white border border-green-200 text-[11px] font-mono">Amalaki 68 bioactives</span>
              <span className="px-2 py-1 rounded-full bg-white border border-green-200 text-[11px] font-mono">Bibhitaki 52</span>
              <span className="px-2 py-1 rounded-full bg-white border border-green-200 text-[11px] font-mono">Haritaki 54</span>
            </div>
          </div>
        </div>
      </div>

      {/* Network full width */}
      <NetworkGraph networkData={network} loading={networkLoading} />
    </div>
  );
}
