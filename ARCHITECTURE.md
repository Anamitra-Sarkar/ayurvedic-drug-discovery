# Architecture - Six Layers + Agentic Orchestration

## High-Level

Frontend (React Vite 3Dmol.js Plotly) <-> FastAPI Backend (6 layers agents) <-> Data (IMPPAT sample 100, proteins 10, literature 40, ML 500) <-> Models (ML rescorer.pkl)

## Backend Layers Detailed:

### 1. Database Layer
- **Agent:** DatabaseAgent
- **Core:** None, direct JSON load
- **Data:** imppat_sample.json 100 phytochemicals: 20 Triphala (Emblica, Terminalia bellerica, Terminalia chebula - gallic acid, ellagic acid, chebulagic acid, chebulinic acid, corilagin), 20 AYUSH-64 (Alstonia scholaris echitamine alstonine, Picrorhiza kurroa picroside I II kutkoside, Swertia chirata amarogentin mangiferin, Caesalpinia crista), 60 anti-epileptic (Bacopa bacoside A B, Withania withanolide A withaferin A, Nardostachys, Valeriana, Centella)
- **Each entry:** plant name botanical family phytochemical SMILES formula MW therapeutic uses Ayurvedic rasa guna virya vipaka dosha ADMET water sol caco2 BBB CYP Ames hepatotox drug-likeness Lipinski Veber QED bioavailability SA bioactivity predicted targets evidence_tier 1 disclaimer literature-mined not experimentally validated
- **Methods:** search_plants(), get_phytochemicals_for_plant(), search_by_property(), get_network_pharmacology_graph() Triphala 174 bioactives 44 targets [4]
- **API:** /api/database/search, /plants, /triphala, /ayush64

### 2. Cheminformatics Layer
- **Agent:** CheminformaticsAgent
- **Core:** descriptors.py (MW LogP HBD HBA TPSA rotatable rings CSP3 BertzCT QED RDKit if available else hash fallback), filters.py (Lipinski Veber PAINS SA)
- **Methods:** process_phytochemical(), batch_process(), SMILES validation, 3D conformer generation
- **Evidence:** DATABASE_DERIVED + COMPUTED

### 3. Docking Layer
- **Agent:** DockingAgent, InteractionAnalysisAgent
- **Core:** vina_wrapper.py (VinaBinaryDetector searches PATH conda, VinaConfig generates conf.txt, VinaResult parsing regex affinity table MODEL ENDMDL PDBQT, robust timeout subprocess, box estimation from PDB fallback, mock_used flag), scoring.py (LigandFeatures.from_smiles RDKit else heuristic, VinaScore AD4Score approximate Trott&Olson 2010 AutoDock4 formulas weights, HybridScorer 0.6/0.4, MLRescorer DockingApp RF style RandomForestRegressor trained 1200 synthetic PDBBind-like RMSE ~0.7 R2, pdbbind_evaluation_notes Vina top-1 ~70% R~0.58 hybrid improvement), interactions.py (PLIP-mimetic 8 types H-bond hydrophobic pi-stacking pi-cation salt bridge water bridge halogen bond metal-complex thresholds Adasme et al 2021, InteractionDetector.detect_from_features ligand HBD HBA aromatic + target-specific binding residues GABRA1 TYR58 PHE77 TYR157 HIS102 SCN1A GRIN2B seed-randomized geometry mock mode returns InteractionProfile)
- **Methods:** prepare_ligand(), prepare_protein(), run_docking(), batch docking, detect interactions
- **Evidence:** DOCKING_RESULT
- **Physics-inspired mock:** empirical formula using MW LogP H-bond counts hydrophobic contacts + random variation returning binding affinity -4 to -12 kcal/mol, pose, confidence

### 4. ML Layer
- **Agent:** MLAgent
- **Core:** features.py (AyurvedicFeatureEngineer fusing docking vina_affinity ligand_efficiency intermol hbonds hydrophobic pocket_occupancy QSAR MW LogP HBD HBA TPSA rotatable rings CSP3 BertzCT QED RDKit else pure-python hash fallback Ayurvedic phytochemical class one-hot flavonoid alkaloid terpenoid privileged scaffold dosha fit_scaler transform replicates BACE1 combined-feature improvement 0.59->0.78 R2), models.py (42-algorithm benchmark list documented top5 implemented RandomForest oob_score balanced, ExtraTrees low variance noisy docking, XGBoost -> HistGradientBoosting fallback, NuSVR NuSVC critical small n=49 TLR4 regime, StackingEnsemble RF+ET+XGB Ridge meta best generalization includes both regressors classifiers MODEL_METADATA), training.py (create_synthetic_pdbbind_dataset n=500 synthetic PDBBind-like curcumin withanolide seeds physics-inspired pKd = -vina + MW LogP QED + privileged + hbond clipped [3,10.5], leakage_aware_split GroupKFold scaffold hash KMeans cluster diversity TLR4 n=49 methodology, cross_validate_model benchmark_models metrics R2 RMSE MAE Pearson Spearman ROC-AUC PR-AUC)
- **Methods:** train(), predict(), batch_predict(), binding affinity classification + regression
- **Evidence:** ML_PREDICTION with applicability domain

### 5. XAI Layer
- **Agent:** XAIAgent
- **Core:** shap_explainer.py (tries shap TreeSHAP else feature importance fallback), lime_explainer.py LIME fallback
- **Methods:** explain_prediction() returning SHAP values top features textual interpretation
- **Evidence:** XAI_INTERPRETATION
- **Protocol:** bias-aware splits multi-explainer triangulation [24]

### 6. RAG Literature + Agentic Orchestration
- **Agent:** LiteratureAgent, ValidationAgent, ReportAgent, Orchestrator
- **Core RAG:** corpus.py (AyurvedicCorpusLoader 40 refs), retriever.py (Sentence-BERT all-MiniLM-L6-v2 FAISS TF-IDF fallback, retrieve reranking), generator.py (CitationGroundedGenerator citation-grounded synthesis mock LLM if no API key structured, 0% hallucinated citations [27] performance target hallucination 47.8%->12.3% faithfulness 0.52->0.87 accuracy 0.54->0.89 [28]), faiss_index placeholder
- **ValidationAgent:** Separate from others to prevent error propagation [32], validates every stage output evidence tier compliance, no clinical overclaim, applicability domain, hallucination citation grounding, docking pose quality, ML confidence, returns validation report, safety guardrail pattern Tippy validate sanitize enforce [36]
- **ReportAgent:** Generates final automated candidate ranking and reporting molecular visualization data evidence tiers clearly separated safety guardrail pattern Tippy, generates JSON + markdown report sections mapping to evidentiary tiers, ranking based on weighted multi-tier scoring but explicit disclaimer
- **Orchestrator:** LangGraph-style StateGraph state machine error handling checkpointing parallel execution where possible, provide run_pipeline() main entry point, design inspirations LangGraph StateGraph lightweight dependency-free checkpointing via JSON serialization supports both sequential parallel node execution evidence tier enforcement, inspirations AgentD [35] modular LLM agent framework closest analogue
- **API:** /api/literature/query, /rag-info, /references, /pipeline/run

## Frontend:

- **Stack:** React, Vite, axios, 3Dmol, plotly.js-dist, tailwind, react-router-dom
- **Config:** vite.config.js proxy /api -> localhost:8000 optimizeDeps 3dmol plotly, tailwind.config.js postcss
- **Core Enforcement:** src/utils/evidence.js central 5-tier registry DATABASE_DERIVED cyan, DOCKING_RESULT violet, ML_PREDICTION pink, XAI_INTERPRETATION orange, LITERATURE_DERIVED green, includes enforceEvidenceTier containsClinicalClaim banned-phrase blocker getDisclaimerForTiers AYUSH-64 justification per tier compositeComputational null principle
- **Services:** src/services/api.js FastAPI client realistic mock fallback Withaferin A Curcumin Berberine Emblicanin A Chebulagic acid Piperine preserving tiers endpoints search docking ML XAI literature ranking Triphala network 174 bioactives
- **Components:**
  - EvidenceTierBadge.jsx badge color icon tooltip showing AYUSH-64 note confidence basis NOT CLINICAL PROOF Legend TierSeparator
  - MoleculeViewer.jsx dynamic import 3dmol PDB protein + SDF ligand stick sphere wire cartoon zoom fit PNG interactions display watermark 3Dmol.js Computational Pose DOCKING_RESULT badge
  - CompoundCard.jsx IMPPAT info ADMET drug-likeness QED logP TPSA HBD HBA Ayurvedic name DATABASE_DERIVED
  - DockingResults.jsx ΔG table RMSD clusters poses PLIP-style interactions amber disclaimer Vina scoring explanation mock fallback noted
  - MLPredictionCard.jsx pKd nM applicability domain inside outside uncertainty
  - XAIExplanation.jsx SHAP waterfall plot plotly feature importance XAI_INTERPRETATION
  - LiteraturePanel.jsx RAG results citations faithfulness LITERATURE_DERIVED
  - PipelineFlow.jsx visual diagram 6 functional layers orchestrator data flow matching required pipeline flow diagram Section 5
  - CandidateRankingTable.jsx ranked list evidence tiers separated must not present as clinical proof warning banner
  - SearchBar.jsx IMPPAT search
  - NetworkGraph.jsx network pharmacology graph Triphala example 174 bioactives
- **Pages:** Dashboard.jsx (overview Triphala network AYUSH-64 case pipeline status), CompoundDetail.jsx (all tiers for single compound), PipelineRun.jsx (run full pipeline form plant target top_n include XAI literature), Documentation.jsx (literature review matrix gap references)
- **Enforcement:** Top warning banner sticky COMPUTATIONAL ONLY NO tier collapse, EvidenceTierLegend

## Evidence Enforcement Across Stack:

Backend core/evidence/tiers.py + evidence.py central, EvidenceTier enum 5, TieredEvidence wrapper, CLINICAL_DISCLAIMER AYUSH-64 precedent, @enforce_tier decorator, validate_no_clinical_claim() blocks clinical-proof language, global_registry.

Frontend evidence.js same registry.

Every API response includes evidence_tier.

ValidationAgent final gate.

ReportAgent separates sections by tier.

## Data Flow:

User query plant (e.g., Withania somnifera) + target (7E9G mGluR2) -> DatabaseAgent searches IMPPAT sample returns phytochemicals (withaferin A etc) tier1 -> CheminformaticsAgent computes descriptors filters drug-like tier1 computed -> DockingAgent docks to target Vina empirical or mock physics-inspired returns affinity pose tier2 -> InteractionAgent PLIP-mimetic 8 types tier2 -> MLAgent fuses docking + QSAR predicts pKd applicability domain tier3 -> XAIAgent SHAP triangulation explains tier4 -> LiteratureAgent RAG retrieves 40 refs citations grounded answer tier5 -> ValidationAgent checks tier compliance no clinical overclaim citation grounding pose quality applicability -> ReportAgent generates ranking JSON markdown molecular viz data safety guardrail tier separation warning -> Frontend displays CandidateRankingTable with tier badges MoleculeViewer 3Dmol SHAP plot LiteraturePanel NetworkGraph.

## Deployment:

- Backend Dockerfile, requirements.txt fastapi uvicorn pydantic rdkit-pypi scikit-learn shap numpy pandas sentence-transformers faiss-cpu langgraph langchain etc fallback notes
- Frontend npm build -> dist
- Docker-compose optional
