# Pipeline Flow Diagram - Section 5 Required

## Textual Flow Diagram (Must include in Section 5)

```
[Input: Plant List e.g., Withania somnifera, Bacopa monnieri, Triphala constituents 
        or Phytochemical List e.g., withaferin A, bacoside A
        + Protein Target e.g., 7E9G mGluR2 [5], 6LU7 Mpro AYUSH-64 [3]]
                            |
                            v
            ┌─────────────────────────────────────┐
            │ DatabaseAgent (TIER 1)              │
            │ IMPPAT 1,742 plants 9,596 compounds │
            │ 27,074 associations [7][8]          │
            │ Triphala 174 bioactives 44 targets   │
            │ 78 diseases [4]                     │
            │ 63 herbs 349 phytochemicals 11 cand │
            │ 11 novel neuromodulators [5]        │
            └──────────────┬──────────────────────┘
                           v
            ┌─────────────────────────────────────┐
            │ CheminformaticsAgent (TIER 1 comp)  │
            │ RDKit descriptors MW LogP HBD HBA   │
            │ TPSA rotatable QED BertzCT CSP3     │
            │ Lipinski Veber PAINS SA filters     │
            │ SMILES validation 3D conformer      │
            └──────────────┬──────────────────────┘
                           v
            ┌─────────────────────────────────────┐
            │ DockingAgent (TIER 2)               │
            │ Vina empirical Lennard-Jones H-bond │
            │ hydrophobic steric [12] 100x faster │
            │ than AD4, Hybrid AutoDock+Vina pKi  │
            │ improvement [14], DockingApp RF     │
            │ rescoring SOTA comparable [13]      │
            │ Returns: affinity -4 to -12 kcal/mol│
            │ pose RMSD confidence                │
            └──────────────┬──────────────────────┘
                           v
            ┌─────────────────────────────────────┐
            │ InteractionAnalysisAgent (TIER 2)   │
            │ PLIP [15] 7-8 types no manual prep  │
            │ H-bond hydrophobic pi-stacking pi-  │
            │ cation salt bridge water bridge     │
            │ halogen metal-complex               │
            │ Target residues: GABRA1 TYR58 PHE77 │
            │ TYR157 HIS102 etc                   │
            └──────────────┬──────────────────────┘
                           v
            ┌─────────────────────────────────────┐
            │ MLAgent (TIER 3)                    │
            │ Fusion docking+QSAR R2 0.78 vs 0.65 │
            │ 0.64 alone [20]                     │
            │ 42-alg benchmark ExtraTrees R2      │
            │ 0.760 XGB ROC-AUC 0.962 [19]        │
            │ Leakage-aware diversity-preserving  │
            │ GroupKFold scaffold hash KMeans [16]│
            │ n=49 methodology template           │
            │ Models: RF oob, ExtraTrees low var  │
            │ XGB/HistGradientBoosting, NuSVR     │
            │ small regime [16], StackingEnsemble │
            │ Returns: pKd, nM, applicability, conf│
            └──────────────┬──────────────────────┘
                           v
            ┌─────────────────────────────────────┐
            │ XAIAgent (TIER 4)                   │
            │ SHAP TreeSHAP + LIME + feature imp  │
            │ triangulation bias-aware splits [24]│
            │ Returns: SHAP values top features   │
            │ textual interpretation              │
            └──────────────┬──────────────────────┘
                           v
            ┌─────────────────────────────────────┐
            │ LiteratureAgent (TIER 5)            │
            │ RAG Sentence-BERT FAISS reranking   │
            │ Llama 3.2 style [28]                │
            │ 0% hallucinated vs 40-60% non-RAG   │
            │ [27], 47.8%->12.3% faithful 0.52-> │
            │ 0.87 acc 0.54->0.89 [28]            │
            │ Both sides molecule+literature [30] │
            │ RetMol PromptDiff BIOREADER         │
            │ Corpus 40 refs 7 areas A-G          │
            │ Returns: citation-grounded answer   │
            └──────────────┬──────────────────────┘
                           v
            ┌─────────────────────────────────────┐
            │ ValidationAgent (Separate)          │
            │ MAS error-propagation risk [32]     │
            │ Prevents propagation                │
            │ Checks: tier compliance, no clinical│
            │ overclaim, applicability, halluc,   │
            │ pose quality, ML confidence         │
            │ Safety guardrail Tippy validate     │
            │ sanitize enforce [36]               │
            └──────────────┬──────────────────────┘
                           v
            ┌─────────────────────────────────────┐
            │ ReportAgent                         │
            │ Ranking weighted multi-tier but     │
            │ explicit disclaimer                 │
            │ JSON + Markdown tier separation     │
            │ Molecular viz data 3Dmol            │
            │ Safety guardrail [36]               │
            │ Must not present as clinical proof  │
            └──────────────┬──────────────────────┘
                           v
        [Output: Ranked Candidate List
         Each candidate has 5 tier badges:
         DATABASE_DERIVED, DOCKING_RESULT, ML_PREDICTION, XAI_INTERPRETATION, LITERATURE_DERIVED
         With disclaimers, citations, validation report, warning banner]
```

## Mermaid Diagram (for frontend PipelineFlow.jsx)

```mermaid
graph TD
    A[IMPPAT 100 sample<br/>1,742 plants 9,596 compounds [7]] --> B[DatabaseAgent<br/>TIER1 DATABASE_DERIVED<br/>Triphala 174/44/78 [4]<br/>63 herbs 349 [5]]
    B --> C[CheminformaticsAgent<br/>TIER1 computed<br/>RDKit descriptors<br/>Lipinski QED]
    C --> D[DockingAgent<br/>TIER2 DOCKING_RESULT<br/>Vina 100x faster [12]<br/>Hybrid pKi [14]<br/>RF rescoring [13]]
    D --> E[InteractionAnalysis<br/>TIER2 DOCKING_RESULT<br/>PLIP 7-8 types [15]]
    E --> F[MLAgent<br/>TIER3 ML_PREDICTION<br/>Fusion R2 0.78 [20]<br/>42-alg ExtraTrees R2 0.760 [19]<br/>Leakage-aware n=49 [16]]
    F --> G[XAIAgent<br/>TIER4 XAI_INTERP<br/>SHAP triangulation [24]]
    G --> H[LiteratureAgent<br/>TIER5 LITERATURE<br/>RAG 0% halluc [27]<br/>47.8->12.3% [28]<br/>Both sides [30]]
    H --> I[ValidationAgent<br/>Separate<br/>MAS error-prop [32]<br/>No clinical overclaim<br/>AYUSH-64 [3] check]
    I --> J[ReportAgent<br/>Ranking JSON+MD<br/>Tier separation<br/>Safety guardrail [36]<br/>3Dmol viz]
    J --> K[Frontend<br/>CandidateRankingTable<br/>5 tier badges<br/>Warning COMPUTATIONAL ONLY]
    
    style A fill:#e0f2fe
    style B fill:#a5f3fc
    style C fill:#a5f3fc
    style D fill:#ddd6fe
    style E fill:#ddd6fe
    style F fill:#fbcfe8
    style G fill:#fed7aa
    style H fill:#bbf7d0
    style I fill:#fef3c7
    style J fill:#fecaca
    style K fill:#f8faf6
```

## LangGraph Orchestration

- StateGraph with checkpointing via JSON serialization
- Parallel execution where possible (cheminformatics batch, docking batch)
- Error handling per node, fallback to mock with tier preserved
- Closest analogue AgentD [35] modular LLM framework automates multi-task pipeline coordination
- Tippy [36] 5-agent + Safety Guardrail first production-ready DMTA template for ReportAgent gating

## Evidence Flow

Every edge carries evidence_tier metadata, validated by ValidationAgent, enforced by central evidence.py and frontend evidence.js.

## Implementation Files

- backend/app/agents/orchestrator.py - LangGraph-style StateGraph run_pipeline() async
- frontend/src/components/PipelineFlow.jsx - Visual diagram component matching this flow
- backend/app/core/evidence/tiers.py - @enforce_tier decorator

## Hard Constraint Integration

Flow diagram explicitly shows ValidationAgent as separate node after LiteratureAgent before ReportAgent to prevent error propagation [32] and enforce must not present computational prediction as clinical proof via AYUSH-64 justification [3].
