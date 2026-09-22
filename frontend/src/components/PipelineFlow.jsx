
/**
 * PipelineFlow.jsx
 * Visual diagram of 6 functional layers + orchestrator
 * Matching required pipeline flow diagram from Section 5
 * 
 * Layers:
 * i   curated phytochemical DB (IMPPAT primary)
 * ii  cheminformatic molecular-structure processing (RDKit)
 * iii structure-based protein-ligand docking (Vina style)
 * iv  supervised ML for binding-affinity prediction
 * v   explainable AI (SHAP)
 * vi  scientific literature mining via RAG
 * Coordinated by agentic orchestration layer (LangGraph-style)
 * Surfaced through interactive web interface with molecular visualisation and automated candidate ranking and reporting
 */
import { EVIDENCE_TIERS } from '../utils/evidence.js';

const LAYERS = [
  {
    id: 'i',
    name: 'Curated Phytochem DB',
    full: 'Layer i: IMPPAT, PubChem, Traditional Medicine DBs',
    color: '#0e7490',
    bg: 'bg-cyan-50',
    border: 'border-cyan-200',
    icon: '🗄️',
    inputs: ['IMPPAT 1740 plants', '4100+ phytochemicals', 'Ayurvedic formulations'],
    outputs: ['SMILES, SDF', 'DATABASE_DERIVED'],
    tier: 'DATABASE_DERIVED',
    tech: 'IMPPAT • PubChem • PostgreSQL',
  },
  {
    id: 'ii',
    name: 'Cheminformatics',
    full: 'Layer ii: RDKit Molecular Processing',
    color: '#334155',
    bg: 'bg-slate-50',
    border: 'border-slate-200',
    icon: '⬡',
    inputs: ['SMILES strings', 'SDF mol files'],
    outputs: ['ECFP4 2048-bit', 'RDKit descriptors', 'Drug-likeness'],
    tier: 'DATABASE_DERIVED',
    tech: 'RDKit • PaDEL • QED scorer',
  },
  {
    id: 'iii',
    name: 'Docking',
    full: 'Layer iii: Protein-Ligand Docking (Vina)',
    color: '#7c3aed',
    bg: 'bg-violet-50',
    border: 'border-violet-200',
    icon: '🧬',
    inputs: ['Protein PDB (6LU7)', 'Ligand SDF', 'Grid box'],
    outputs: ['ΔG kcal/mol', 'Pose + RMSD', 'DOCKING_RESULT'],
    tier: 'DOCKING_RESULT',
    tech: 'AutoDock Vina • mock physics fallback',
  },
  {
    id: 'iv',
    name: 'ML Affinity',
    full: 'Layer iv: Supervised ML',
    color: '#db2777',
    bg: 'bg-pink-50',
    border: 'border-pink-200',
    icon: '🤖',
    inputs: ['ECFP4 fingerprints', 'Descriptor matrix'],
    outputs: ['pKd pred', 'Applicability Domain', 'ML_PREDICTION'],
    tier: 'ML_PREDICTION',
    tech: 'RF • XGBoost • GNN • ECFP4',
  },
  {
    id: 'v',
    name: 'Explainable AI',
    full: 'Layer v: SHAP Explainability',
    color: '#ea580c',
    bg: 'bg-orange-50',
    border: 'border-orange-200',
    icon: '🔍',
    inputs: ['ML model', 'Feature matrix'],
    outputs: ['SHAP values', 'Feature attribution', 'XAI_INTERPRETATION'],
    tier: 'XAI_INTERPRETATION',
    tech: 'SHAP • TreeSHAP • Plotly',
  },
  {
    id: 'vi',
    name: 'RAG Literature',
    full: 'Layer vi: Literature Mining',
    color: '#15803d',
    bg: 'bg-green-50',
    border: 'border-green-200',
    icon: '📚',
    inputs: ['PubMed, Ayurveda papers', 'AYUSH-64 docs'],
    outputs: ['Retrieved citations', 'Faithfulness score', 'LITERATURE_DERIVED'],
    tier: 'LITERATURE_DERIVED',
    tech: 'sentence-transformers • FAISS • TF-IDF fallback',
  },
];

export default function PipelineFlow({ activeLayer = null, onSelectLayer }) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white shadow-card overflow-hidden">
      {/* Header */}
      <div className="px-5 py-4 border-b border-slate-100 bg-gradient-to-r from-slate-50 to-[#f8faf6] flex items-center justify-between">
        <div>
          <div className="font-display font-bold text-[15px] text-slate-900">AI-Driven Ayurvedic Drug Discovery — 6-Layer Pipeline</div>
          <div className="font-mono text-[11px] text-slate-500 mt-0.5">Section 5 flow diagram • LangGraph orchestrator • Evidence-tiered outputs • AYUSH-64 justification</div>
        </div>
        <div className="hidden md:flex items-center gap-2">
          <span className="font-mono text-[10px] px-2 py-1 rounded-full bg-amber-50 border border-amber-200 text-amber-800">Non-clinical computational pipeline</span>
        </div>
      </div>

      {/* Orchestrator */}
      <div className="px-5 py-4 bg-[#f6f7f0] border-b border-[#e8e9d8]">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-slate-900 text-white flex items-center justify-center">🕸️</div>
          <div className="flex-1">
            <div className="font-display font-semibold text-sm">Agentic Orchestration Layer (LangGraph-style)</div>
            <div className="font-mono text-[11px] text-slate-600 mt-0.5">StateGraph: db_query → rdkit_process → docking → ml_predict → xai_explain → rag_synthesis → rank_report • Central evidence tier enforcement</div>
          </div>
          <div className="hidden md:block font-mono text-[10px] px-2 py-1 rounded-full bg-slate-900 text-white">STATEFUL • TIER-CHECKED</div>
        </div>
        <div className="mt-3 grid grid-cols-3 md:grid-cols-6 gap-2">
          {['State', 'Tool Nodes', 'Evidence Guard', 'Retry/ fallback', 'Report Gen', 'Web Surface'].map(t=>(
            <div key={t} className="rounded-lg bg-white border border-[#e8e9d8] px-2.5 py-1.5 text-center">
              <div className="font-mono text-[10px] tracking-widest text-[#5f5f40]">{t}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Layers flow - horizontal on desktop, vertical on mobile */}
      <div className="p-5">
        {/* Flow arrows */}
        <div className="hidden lg:flex items-center gap-0 mb-4">
          {LAYERS.map((l, idx)=>(
            <div key={l.id} className="flex items-center flex-1">
              <div className="flex-1 h-px bg-slate-200" />
              {idx < LAYERS.length -1 && <span className="font-mono text-[10px] text-slate-400 px-1">→</span>}
            </div>
          ))}
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-3">
          {LAYERS.map((layer)=> {
            const isActive = activeLayer === layer.id || activeLayer === layer.tier;
            return (
              <button
                key={layer.id}
                onClick={()=>onSelectLayer?.(layer.id)}
                className={`text-left rounded-2xl border-2 p-3 transition-all ${layer.bg} ${layer.border} ${isActive ? 'ring-2 ring-slate-900 ring-offset-2 shadow-lg scale-[1.02]' : 'hover:shadow-card-hover hover:scale-[1.01]'} `}
                style={{ borderColor: isActive ? '#0f172a' : undefined }}
              >
                <div className="flex items-start justify-between">
                  <div className="w-9 h-9 rounded-xl flex items-center justify-center text-lg bg-white border border-slate-200 shadow-sm">{layer.icon}</div>
                  <span className="font-mono text-[10px] px-1.5 py-0.5 rounded bg-white border border-slate-200">{layer.id}</span>
                </div>
                <div className="mt-2.5 font-display font-semibold text-[13px] leading-tight">{layer.name}</div>
                <div className="font-mono text-[10px] text-slate-600 mt-1 leading-tight">{layer.full}</div>

                <div className="mt-2.5 space-y-1">
                  <div className="font-mono text-[9px] tracking-widest text-slate-500">INPUTS</div>
                  <div className="flex flex-wrap gap-1">
                    {layer.inputs.slice(0,2).map(inp=>(
                      <span key={inp} className="px-1.5 py-0.5 rounded-full bg-white border border-slate-200 text-[10px] font-mono text-slate-600">{inp}</span>
                    ))}
                  </div>
                </div>

                <div className="mt-2 space-y-1">
                  <div className="font-mono text-[9px] tracking-widest text-slate-500">OUTPUTS / TIER</div>
                  <div className="flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full" style={{background: layer.color}} />
                    <span className="font-mono text-[10px] font-semibold" style={{color: layer.color}}>{layer.tier}</span>
                  </div>
                  <div className="font-mono text-[10px] text-slate-600">{layer.outputs[0]}</div>
                </div>

                <div className="mt-2.5 pt-2 border-t border-slate-200/60">
                  <div className="font-mono text-[9px] text-slate-500 truncate">{layer.tech}</div>
                </div>
              </button>
            );
          })}
        </div>

        {/* Data flow details */}
        <div className="mt-5 rounded-xl bg-slate-900 text-slate-100 p-4 font-mono text-[11px] leading-relaxed">
          <div className="font-semibold text-white tracking-wide mb-2">DATA FLOW (LangGraph StateGraph) — evidence tier enforced at each transition</div>
          <div className="grid md:grid-cols-2 gap-3">
            <div className="space-y-1">
              <div><span className="text-cyan-300">1.</span> IMPPAT query → DATABASE_DERIVED (SMILES, plant metadata) — guarded by containsClinicalClaim()</div>
              <div><span className="text-slate-400">2.</span> RDKit: SMILES → ECFP4 2048 + 200 descriptors (MolLogP, TPSA...) — still DATABASE_DERIVED</div>
              <div><span className="text-violet-300">3.</span> Vina docking: PDB + SDF → ΔG, pose, RMSD → DOCKING_RESULT (mock physics fallback if binary absent)</div>
            </div>
            <div className="space-y-1">
              <div><span className="text-pink-300">4.</span> ML: features → pKd pred + applicability domain → ML_PREDICTION (uncertainty quantified)</div>
              <div><span className="text-orange-300">5.</span> XAI: TreeSHAP → feature attributions → XAI_INTERPRETATION (not causality)</div>
              <div><span className="text-green-300">6.</span> RAG: query → FAISS/TF-IDF → citations + faithfulness → LITERATURE_DERIVED (AYUSH-64 precedent)</div>
              <div><span className="text-amber-200">7.</span> Ranking: tier-separated table • <span className="font-bold">NO merged clinical score</span> • warnings emitted</div>
            </div>
          </div>
        </div>

        <div className="mt-4 flex flex-wrap gap-2">
          {Object.values(EVIDENCE_TIERS).map(t=>(
            <span key={t.id} className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full border text-[11px] font-mono" style={{background: t.color+'12', borderColor: t.color+'30', color: t.color}}>
              <span>{t.icon}</span>{t.id}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}
