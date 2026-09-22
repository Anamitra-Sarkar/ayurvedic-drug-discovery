
/**
 * Documentation.jsx
 * Evidence tiers, AYUSH-64 justification, non-clinical disclaimer, pipeline spec
 */
import { EVIDENCE_TIERS } from '../utils/evidence.js';
import EvidenceTierBadge, { EvidenceTierLegend } from '../components/EvidenceTierBadge.jsx';
import PipelineFlow from '../components/PipelineFlow.jsx';

export default function Documentation() {
  return (
    <div className="space-y-6 max-w-[1200px]">
      <div className="rounded-[20px] bg-white border border-slate-200 p-6 shadow-card">
        <h1 className="font-display font-bold text-2xl">Documentation — 5 Evidence Tiers & AYUSH-64 Compliance</h1>
        <p className="font-mono text-[13px] text-slate-600 mt-2 leading-relaxed">Every output must map to one of five tiers. Computational prediction must never be presented as clinical proof. This mirrors AYUSH-64 development: repurposed Ayurvedic formulation where computational screening was only initial hypothesis generation, followed by literature validation, in vitro, and RCTs.</p>
        <div className="mt-4"><EvidenceTierLegend /></div>
      </div>

      <div className="grid md:grid-cols-2 gap-4">
        {Object.values(EVIDENCE_TIERS).map(t=>(
          <div key={t.id} className={`rounded-2xl border-2 p-5 ${t.bg} ${t.border}`}>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-white border border-slate-200 flex items-center justify-center text-lg">{t.icon}</div>
              <div>
                <div className="font-display font-bold text-[14px]">{t.label} — {t.id}</div>
                <div className="font-mono text-[11px] text-slate-600">{t.layer}</div>
              </div>
              <div className="ml-auto"><EvidenceTierBadge tier={t.id} size="sm" /></div>
            </div>
            <div className="mt-3 text-sm leading-relaxed text-slate-800">{t.description}</div>
            <div className="mt-3 rounded-xl bg-white border border-slate-200 p-3">
              <div className="font-mono text-[10px] tracking-widest font-bold text-amber-900">AYUSH-64 JUSTIFICATION</div>
              <div className="text-[12px] text-slate-700 mt-1 leading-relaxed">{t.ayush64Note}</div>
            </div>
            <div className="mt-2 flex items-center justify-between">
              <span className="font-mono text-[10px] text-slate-500">Confidence basis:</span>
              <span className="font-mono text-[11px] text-slate-700 font-medium">{t.confidenceBasis}</span>
            </div>
          </div>
        ))}
      </div>

      <PipelineFlow />

      <div className="rounded-2xl border-2 border-red-300 bg-red-50 p-5">
        <div className="font-display font-bold text-red-900">⚠️ HARD CONSTRAINT — MUST NOT PRESENT AS CLINICAL PROOF</div>
        <div className="mt-2 grid md:grid-cols-2 gap-4 font-mono text-[12px] text-red-800 leading-relaxed">
          <div>
            <div className="font-bold tracking-widest">BANNED PHRASES (blocked by containsClinicalClaim())</div>
            <ul className="list-disc ml-4 mt-2 space-y-1">
              <li>"clinically proven", "proves efficacy"</li>
              <li>"cures", "treats disease", "therapeutic effect demonstrated"</li>
              <li>"effective treatment for", "approved drug"</li>
              <li>"clinical efficacy confirmed"</li>
            </ul>
          </div>
          <div>
            <div className="font-bold tracking-widest">REQUIRED DISCLAIMERS</div>
            <ul className="list-disc ml-4 mt-2 space-y-1">
              <li>Every card: "COMPUTATIONAL PREDICTION ONLY — NOT CLINICAL PROOF"</li>
              <li>Ranking table: top banner "COMPUTATIONAL RANKING ONLY — NOT CLINICAL PRIORITY"</li>
              <li>Docking: "binding hypothesis, not in vitro activity"</li>
              <li>ML: "statistical inference, requires IC50/Kd"</li>
              <li>Literature: "RAG synthesis, not new clinical finding"</li>
            </ul>
          </div>
        </div>
        <div className="mt-4 rounded-xl bg-white border border-red-200 p-3 font-mono text-[11px] text-slate-700 leading-relaxed">
          AYUSH-64 Case Study: Original work (Thakar et al., J Res Ayurvedic Sci 2021) repurposed existing Ayurvedic antimalarial formulation AYUSH-64 for COVID-19 based on computational target mapping + traditional use literature, then conducted prospective observational study and RCT. Computational layer alone would have been insufficient. Our pipeline encodes same pathway: computational = tier 2-4, literature = tier 5, database = tier 1 — ALL explicitly non-clinical. Any claim of therapeutic effect requires independent experimental validation per Ayurvedic pharmacology standards (Ayurveda Biology, Pharmacovigilance for ASU drugs).
        </div>
      </div>

      <div className="rounded-2xl bg-slate-900 text-slate-100 p-6 font-mono text-[12px] leading-relaxed">
        <div className="font-bold tracking-widest text-white">MOCK FALLBACK ARCHITECTURE — REALISTIC BUT SAFE</div>
        <div className="mt-3 grid md:grid-cols-2 gap-4">
          <div>
            <div className="text-violet-300 font-semibold">Docking: Vina wrapper + mock</div>
            <div className="text-slate-300 mt-1">Attempts real AutoDock Vina binary via subprocess if present (checks `vina --help`). If absent, uses physics-inspired scoring: weighted vdW (Lennard-Jones approximated from RDKit distance matrix) + H-bond heuristic (donor/acceptor count) + hydrophobic contact (logP) + desolvation (TPSA) + torsional penalty (rotatable bonds). Produces plausible ΔG range -4 to -9 kcal/mol, RMSD, pose clustering, PLIP-style interaction list. API shape identical so frontend unaffected.</div>
          </div>
          <div>
            <div className="text-green-300 font-semibold">RAG: sentence-transformers + FAISS / TF-IDF fallback</div>
            <div className="text-slate-300 mt-1">Tries sentence-transformers (all-MiniLM-L6-v2) for embeddings + FAISS for ANN. If libraries absent, falls back to TF-IDF vectorizer + cosine similarity over pre-bundled Ayurveda corpus (including Triphala, AYUSH-64 papers). Faithfulness scored via token overlap + citation verification. LLM synthesis mocked with template that always cites retrieved docs and includes non-clinical disclaimer.</div>
          </div>
        </div>
        <div className="mt-4 pt-4 border-t border-white/10">
          <div className="text-amber-200 font-semibold">Evidence Enforcement Via Central Module</div>
          <div className="text-slate-300 mt-1">frontend/src/utils/evidence.js and backend/evidence/tiers.py (if present) enforce: withEvidence() wrappers, enforceEvidenceTier() throws if missing, containsClinicalClaim() blocks banned phrases at UI and API, getDisclaimerForTiers() auto-generates appropriate warning. CandidateRankingTable deliberately keeps compositeComputational = null — no merged clinical score.</div>
        </div>
      </div>

      <div className="rounded-2xl border border-slate-200 bg-white p-5">
        <div className="font-display font-semibold">Triphala Example — 174 Bioactives</div>
        <div className="font-mono text-[12px] text-slate-600 mt-2 leading-relaxed">
          Triphala = Emblica officinalis (Amalaki, 68 bioactives) + Terminalia bellirica (Bibhitaki, 52) + Terminalia chebula (Haritaki, 54) = 174 bioactives per IMPPAT. Network pharmacology: nodes = plants (type plant, DATABASE_DERIVED), compounds (DATABASE_DERIVED), targets (NF-kB, TNF-alpha, IL-6, COX-2, Mpro, ACE2 — LITERATURE_DERIVED predicted). Edges: plant-compound (botanical occurrence, DB), compound-target (predicted via ML/LIT). Canvas force layout visualizes polypharmacology hypothesis without implying clinical synergy — requires experimental validation.
        </div>
      </div>
    </div>
  );
}
