
/**
 * App.jsx - Main application with routing, evidence tier enforcement shell
 * AI-Driven Computational Pipeline for Ayurvedic Drug Discovery
 * Evidence tiers + AYUSH-64 justification + non-clinical disclaimer
 */
import { BrowserRouter, Routes, Route, NavLink, Link } from 'react-router-dom';
import { useState } from 'react';
import Dashboard from './pages/Dashboard.jsx';
import CompoundDetail from './pages/CompoundDetail.jsx';
import PipelineRun from './pages/PipelineRun.jsx';
import Documentation from './pages/Documentation.jsx';
import { EvidenceTierLegend } from './components/EvidenceTierBadge.jsx';

function Layout({ children }) {
  const [showTierInfo, setShowTierInfo] = useState(false);

  return (
    <div className="min-h-screen bg-[#f8faf6] text-slate-900">
      {/* Top Warning Banner - HARD REQUIREMENT */}
      <div className="sticky top-0 z-40 bg-gradient-to-r from-amber-100 via-orange-50 to-amber-100 border-b-2 border-amber-300">
        <div className="max-w-[1600px] mx-auto px-4 md:px-6 py-2.5 flex flex-wrap items-center gap-3">
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-amber-600 text-white text-[11px] font-mono font-bold tracking-widest">⚠️ COMPUTATIONAL ONLY</span>
          <span className="font-mono text-[11px] md:text-xs text-amber-900 leading-snug">
            This platform outputs <span className="font-bold">computational predictions</span> tiered by evidence provenance. <span className="font-bold">NOT clinical proof</span> of efficacy/safety. All results require experimental validation per AYUSH-64 precedent.
          </span>
          <button onClick={()=>setShowTierInfo(!showTierInfo)} className="ml-auto text-[11px] font-mono px-2.5 py-1 rounded-full bg-white border border-amber-200 text-amber-800 hover:bg-amber-50">Evidence Tiers {showTierInfo ? '▲' : '▼'}</button>
        </div>
        {showTierInfo && (
          <div className="max-w-[1600px] mx-auto px-4 md:px-6 pb-3">
            <div className="rounded-xl bg-white border border-amber-200 p-3 flex flex-wrap gap-2">
              <EvidenceTierLegend />
              <span className="font-mono text-[11px] text-slate-600 ml-2">AYUSH-64: computational hypothesis → traditional use documentation → preclinical → RCT → regulatory review. This UI enforces same tier separation.</span>
            </div>
          </div>
        )}
      </div>

      {/* Navigation */}
      <header className="sticky top-[44px] md:top-[38px] z-30 bg-white/90 backdrop-blur border-b border-slate-200">
        <div className="max-w-[1600px] mx-auto px-4 md:px-6 h-[64px] flex items-center justify-between gap-4">
          <Link to="/" className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-slate-900 text-white flex items-center justify-center font-display font-bold">A</div>
            <div>
              <div className="font-display font-bold text-[15px] leading-none">AyurDiscovery</div>
              <div className="font-mono text-[10px] text-slate-500 tracking-widest mt-0.5">6-LAYER PIPELINE • EVIDENCE-TIERED</div>
            </div>
          </Link>

          <nav className="flex items-center gap-1">
            {[
              { to: '/', label: 'Dashboard' },
              { to: '/pipeline', label: 'Pipeline Run' },
              { to: '/docs', label: 'Docs & AYUSH-64' },
            ].map(link=>(
              <NavLink
                key={link.to}
                to={link.to}
                className={({isActive})=> `px-3.5 py-2 rounded-full text-sm font-medium transition ${isActive ? 'bg-slate-900 text-white' : 'text-slate-700 hover:bg-slate-100'}`}
              >
                {link.label}
              </NavLink>
            ))}
          </nav>

          <div className="hidden lg:flex items-center gap-2">
            <span className="font-mono text-[10px] px-2 py-1 rounded-full bg-[#f6f7f0] border border-[#e8e9d8] text-[#5f5f40]">FastAPI: /api • RDKit • Vina</span>
            <span className="font-mono text-[10px] px-2 py-1 rounded-full bg-slate-900 text-white">LangGraph Orchestrator</span>
          </div>
        </div>
      </header>

      <main className="max-w-[1600px] mx-auto px-4 md:px-6 py-6">
        {children}
      </main>

      <footer className="border-t border-slate-200 bg-white mt-12">
        <div className="max-w-[1600px] mx-auto px-4 md:px-6 py-6 flex flex-col md:flex-row items-start md:items-center justify-between gap-3">
          <div className="font-mono text-[11px] text-slate-500 leading-relaxed">
            <div>© AyurDiscovery — AI-Driven Computational Pipeline for Ayurvedic Drug Discovery</div>
            <div className="mt-1">Layers: (i) IMPPAT DB, (ii) RDKit, (iii) Vina docking, (iv) ML affinity, (v) SHAP XAI, (vi) RAG literature • LangGraph orchestration • 3Dmol.js visualization</div>
          </div>
          <div className="flex items-center gap-2">
            <span className="font-mono text-[10px] px-2 py-1 rounded-full bg-amber-50 border border-amber-200 text-amber-800">NO CLINICAL CLAIMS — COMPUTATIONAL ONLY</span>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/compound/:id" element={<CompoundDetail />} />
          <Route path="/pipeline" element={<PipelineRun />} />
          <Route path="/docs" element={<Documentation />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
}
