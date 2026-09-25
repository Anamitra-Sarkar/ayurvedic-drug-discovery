# AI-Driven Computational Pipeline for Ayurvedic Drug Discovery
### Phytochemical Mining, Molecular Docking, and Explainable Binding Prediction
**Bhumika Tewari · RCC Institute of Information Technology (RCCIIT), MAKAUT · Winter Project, 2026**

> **⚠️ HARD CONSTRAINT: COMPUTATIONAL ONLY - MUST NOT PRESENT COMPUTATIONAL PREDICTION AS CLINICAL PROOF**

This platform implements an end-to-end computational pipeline for **computational candidate prioritization** - narrowing a large space of Ayurvedic phytochemicals down to a short, evidence-labelled list worth further wet-lab or clinical investigation. It is **not** a claim of experimental validation, and it is **not** a claim that any candidate is clinically effective.

The distinction is motivated by **AYUSH-64 case study [3]** where a polyherbal formulation was repurposed against COVID-19 using NP+docking and subsequently evaluated in an open-label RCT as adjunct to standard care - a rare documented example of computational hypothesis being carried to clinical tier as a **separate, subsequent step**. This is the concrete justification for the five-tier evidence taxonomy, not just an assertion.

---

## Live Deployment

This system is deployed and live, not a local-only prototype:

- **Frontend**: [ayurvedic-drug-discovery.vercel.app](https://ayurvedic-drug-discovery.vercel.app)
- **Backend API**: a public Hugging Face Space (Docker SDK) — API docs at `/docs`
- **Trained model + dataset**: published as public Hugging Face model and dataset
  repositories (real RandomForest binding-affinity model, real 181-row PDBBind
  training set — see `docs/REPRODUCIBILITY.md` and `docs/FINAL_REPORT.md`)

A real end-to-end pipeline run (all nine agent nodes) has been exercised through the
live deployed frontend and independently verified; see
`docs/DEPLOYMENT_VERIFICATION.md` for the dated verification log.

---

## 2. Project Overview - Six Functional Layers

1. **(i) Curated Phytochemical & Traditional-Medicine Databases**
   - Primary: IMPPAT (1,742 plants, 9,596 phytochemicals, 27,074 plant-phytochemical, 11,514 plant-therapeutic associations) [7][8]
   - IMPPAT 2.0: 100+ books, 7,000+ articles, largest digital resource [8]
   - Complementary: TCMSP (499 herbs, 29,384 ingredients, 3,311 targets, 12 ADME) [9], TCMID 2.0 [10]
   - Sample: 65 real, individually PubChem-verified phytochemicals covering Triphala, AYUSH-64, 63 anti-epileptic herbs (an original 100-record sample included 80 fabricated entries, found and removed — see `docs/DATA_PROVENANCE.md`)

2. **(ii) Cheminformatic Molecular-Structure Processing**
   - RDKit descriptors: MW, LogP, HBD, HBA, TPSA, rotatable bonds, QED, BertzCT, CSP3
   - Filters: Lipinski, Veber, PAINS, SA score, bioavailability
   - 3D conformer generation, SMILES validation

3. **(iii) Structure-Based Protein-Ligand Molecular Docking**
   - Engine: AutoDock Vina empirical scoring (modified Lennard-Jones + H-bond + hydrophobic + steric) [12] - up to 100× faster than AutoDock4
   - Rescoring: DockingApp RF [13] - Random Forest layered on Vina, SOTA comparable
   - Hybrid: AutoDock+Vina linear combination, significant pKi correlation improvement [14]
   - Interaction: PLIP [15] - 7-8 types without manual prep, selected for Interaction Analysis Agent

4. **(iv) Supervised ML for Binding-Affinity Prediction**
   - Fusion: Docking + QSAR features - BACE1 study R² 0.78 combined vs 0.65/0.64 alone [20]
   - Models compared, informed by benchmark literature [19][16][20]: RandomForest, GradientBoosting, Ridge, XGBoost - RandomForest selected as best on held-out test MAE (real result: MAE 1.35, R² 0.01 - honestly modest, see `docs/REPRODUCIBILITY.md`)
   - Splitting: Bemis-Murcko scaffold split with Tanimoto-similarity leakage check (real, not random)
   - Training: 181 real PDBBind v2013-core complexes (127 train / 18 val / 36 test), real AutoDock Vina `--score_only` + RDKit features - not synthetic

5. **(v) Explainable AI**
   - SHAP TreeSHAP + LIME + feature importance triangulation [24]
   - Bias-aware splits, applicability domain check [19][24]
   - Methodological template: small Ayurvedic sets

6. **(vi) Scientific-Literature Mining via RAG + Agentic Orchestration**
   - Retriever: Sentence-BERT + FAISS + reranking + Llama 3.2 style [28]
   - Performance: RAG 0% hallucinated citations vs 40-60% non-RAG [27]; hallucination 47.8%→12.3%, faithfulness 0.52→0.87, accuracy 0.54→0.89 [28]
   - Applicability: Both molecule-generation and literature sides - RetMol, PromptDiff, BIOREADER [30]
   - Agentic: MAS pattern, error-propagation risk flagged [32] -> separate ValidationAgent
   - Closest analogue: AgentD [35] modular LLM framework; Tippy [36] 5-agent + Safety Guardrail, first production-ready DMTA

Surfaced through interactive web interface with molecular visualization (3Dmol.js) and automated candidate ranking/reporting.

---

## Five Evidentiary Tiers - Hard Constraint

| Tier | Label | Source | Disclaimer | Color |
|------|-------|--------|------------|-------|
| 1 | DATABASE_DERIVED | IMPPAT, PubChem curated, literature-mined not experimentally validated | Verify provenance | Cyan |
| 2 | DOCKING_RESULT | Vina empirical scoring [12], moderate correlation [14] | Computational estimate, requires experimental validation | Violet |
| 3 | ML_PREDICTION | Ensemble ML fusion [20], leakage-aware split [16] | Prediction, applicability domain check | Pink |
| 4 | XAI_INTERPRETATION | SHAP triangulation [24] | Interpretation of model, not causal mechanism | Orange |
| 5 | LITERATURE_DERIVED | RAG citation-grounded [27][28] | RAG grounded, verify papers | Green |

**Explicit Rule:** No output may collapse two tiers into single undifferentiated claim. Must not present computational prediction as clinical proof. Every output traceable to one tier.

CompositeComputational = null principle: computational tiers do not sum to clinical.

---

## Pipeline Flow Diagram

```
[IMPPAT 65 real verified records] 
    |
    v
DatabaseAgent (TIER 1) -> 1,742 plants / 9,596 phytochemicals [7], Triphala 174 bioactives / 44 targets / 78 diseases [4], 63 herbs / 349 phytochemicals / 11 candidates [5]
    |
    v
CheminformaticsAgent (TIER 1 computed) -> RDKit descriptors, Lipinski, QED, PAINS
    |
    v
DockingAgent (TIER 2) -> Vina [12] 100x faster, Hybrid scoring [14], RF rescoring [13]
    |
    v
InteractionAnalysisAgent (TIER 2) -> PLIP [15] 7-8 types
    |
    v
MLAgent (TIER 3) -> Fusion R2 0.78 [20], 42-alg benchmark ExtraTrees R2 0.760 [19], leakage-aware split n=49 [16]
    |
    v
XAIAgent (TIER 4) -> SHAP triangulation [24], bias-aware
    |
    v
LiteratureAgent (TIER 5) -> RAG 0% hallucinated [27], 47.8%->12.3% [28], both sides [30]
    |
    v
ValidationAgent (Separate) -> MAS error-propagation prevention [32], checks tier compliance, no clinical overclaim, citation grounding, pose quality, applicability
    |
    v
ReportAgent -> JSON + Markdown ranking, molecular viz data, safety guardrail [36], Tippy pattern, explicit tier separation
```

Orchestrated by **LangGraph-style StateGraph** with checkpointing, parallel execution, error handling. Closest general analogue AgentD [35].

---

## Quick Start

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend
npm install
npm run dev  # -> http://localhost:5173

# Full pipeline example
python examples/sample_run.py --plant "Withania somnifera" --target 7E9G --top_n 10
```

See SETUP_GUIDE.md, USER_GUIDE.md, API_DOCUMENTATION.md for details.

---

## Project Structure

```
ayurvedic-drug-discovery-pipeline/
├── backend/
│   ├── app/
│   │   ├── main.py - FastAPI with 6 layers info
│   │   ├── config.py - Settings, 5 tiers
│   │   ├── models/schemas.py - Pydantic with evidence_tier field
│   │   ├── api/ - database, docking, ml, literature, pipeline endpoints
│   │   ├── agents/ - 7 agents + orchestrator
│   │   ├── core/
│   │   │   ├── evidence/ - tier enforcement, AYUSH-64 justification
│   │   │   ├── docking/ - vina_wrapper, scoring, interactions (PLIP mimic)
│   │   │   ├── ml/ - features (fusion), models (top5), training (leakage-aware)
│   │   │   ├── xai/ - shap, lime
│   │   │   ├── rag/ - retriever, generator, corpus (40 refs)
│   │   │   └── cheminformatics/ - descriptors, filters
│   │   └── data/
│   │       ├── imppat_sample.json (65 real, verified phytochemicals)
│   │       ├── proteins/targets.json (10 real targets)
│   │       ├── literature_corpus/references.json (40 refs)
│   │       └── trained/best_regressor.joblib (real RandomForest, trained on 181 real PDBBind complexes)
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/ - EvidenceTierBadge, MoleculeViewer (3Dmol), DockingResults, MLPredictionCard, XAIExplanation, LiteraturePanel, PipelineFlow, CandidateRankingTable, NetworkGraph (Triphala 174)
│   │   ├── pages/ - Landing, Compounds, CompoundDetail, Targets, PipelineRun, Results, Ranking, Network, Documentation
│   │   ├── services/api.js
│   │   └── utils/evidence.js - central 5-tier registry with AYUSH-64 note
│   └── package.json
├── docs/
│   ├── LITERATURE_REVIEW_COMBINED.md - Extended Section 2, 3.1, 3.2.A-G, 4 matrix 20 rows, 5 gap with flow diagram + taxonomy + must not statement, 6 references 40 entries
│   ├── FINAL_REPORT.md - capstone synthesis of the real, verified, deployed system
│   ├── SCIENTIFIC_LIMITATIONS.md, DATA_PROVENANCE.md, REPRODUCIBILITY.md, DEPLOYMENT_VERIFICATION.md
│   ├── PIPELINE_DIAGRAM.md
│   ├── EVIDENTIARY_TIERS.md
│   └── ...
├── examples/
│   ├── sample_run.py
│   └── sample_output.json
├── tests/
└── README.md etc
```

---

## Literature Review Summary - 7 Areas A-G

**A: Computational Ayurvedic/TM Drug Discovery**
- Polyherbal multi-target incompatible with single-drug/single-target [2]
- Network pharmacology as dominant lens [2][4]
- Triphala 174 bioactives, 44 targets, 78 diseases denser combined [4]
- 63 anti-epileptic herbs 349 phytochemicals 11 novel neuromodulators [5]
- AYUSH-64 NP+docking -> open-label RCT adjunct [3] -> cautionary template for tier labeling
- Future: NP + supercomputer VHTS + docking + repurposing [1]
- TCM 7,288 pubs 2007-2025 shift to NP-AI-multi-omics [6] -> gap evidence

**B: Phytochemical Databases**
- IMPPAT 1,742 plants 9,596 phytochemicals 27,074 associations [7], IMPPAT 2.0 100+ books 7,000+ articles [8]
- TCMSP 499 herbs 29,384 ingredients 3,311 targets 837 diseases 12 ADME [9]
- TCMID 2.0 herb-formula-ingredient-target-disease [10]

**C: Molecular Docking**
- Vina scoring modified Lennard-Jones + H-bond + hydrophobic + steric, 100x faster than AD4 [12]
- DockingApp RF RF rescoring comparable SOTA [13]
- Hybrid AutoDock/Vina significant pKi improvement [14]
- PLIP rule-based atom-level 7-8 types no manual prep [15]

**D: ML Bioactivity**
- TLR4 49 compounds ensemble leakage-aware diversity-preserving [16]
- Factor Xa 6,400 ChEMBL 391 Mordred 42-alg benchmark ExtraTrees R2 0.760 XGB ROC-AUC 0.962 [19]
- BACE1 docking+QSAR fusion NuSVR R2 0.78 vs 0.65/0.64 [20]

**E: XAI**
- Survey taxonomy, bias-aware splits multi-explainer triangulation [24]

**F: LLM RAG**
- RAG pharma 0% hallucinated vs 40-60% non-RAG [27]
- Drug QA 150 pairs hallucination 47.8%->12.3% faithfulness 0.52->0.87 accuracy 0.54->0.89 [28]
- RAG for AIGC survey RetMol PromptDiff BIOREADER [30]

**G: Agentic AI**
- Pharma review MAS pattern error-propagation risk [32] -> separate ValidationAgent
- AgentD modular LLM framework [35] closest analogue to LangGraph layer
- Tippy 5-agent + Safety Guardrail first production DMTA [36] template for Report Agent

---

## Research and Engineering Gap

Individual techniques (NP, docking, ML, XAI, agentic orchestration) well established, but systematic reproducible application to Ayurvedic phytochemical data specifically underexplored [6 vs sparse Ayurveda]. Existing closest precedent NP-plus-docking 63 herbs mGluR [5] confined to single target class, no downstream trained ML affinity model, no XAI layer, no automated literature-grounded validation. This pipeline fills gap by integrating six layers with explicit five-tier evidence taxonomy and LangGraph orchestration with ValidationAgent preventing error propagation [32] and safety guardrail [36].

**Pipeline Flow Diagram:** See docs/PIPELINE_DIAGRAM.md - Database -> Cheminformatics -> Docking -> Interaction -> ML -> XAI -> Literature -> Validation -> Report

**Five-Category Evidence Taxonomy:** See EVIDENTIARY_TIERS.md - DATABASE_DERIVED, DOCKING_RESULT, ML_PREDICTION, XAI_INTERPRETATION, LITERATURE_DERIVED

**Must Not Statement:** "Must not present computational prediction as clinical proof" - argued from AYUSH-64 [3] progression computational -> RCT as separate step, Vina moderate correlation [14], RAG hallucination reduction but narrow benchmark [28], error-propagation risk [32].

---

## References - 40 Entries

See docs/REFERENCES.md - 40 sources cited, 20 organized into structured literature matrix Section 4/9.

---

## Safety & Compliance

- Every API response includes evidence_tier field
- ValidationAgent blocks clinical overclaim patterns: "clinically proven", "effective treatment", "cures", etc.
- Frontend top warning banner: COMPUTATIONAL ONLY, NO output may collapse tiers
- ReportAgent includes safety guardrail pattern from Tippy [36]
- AYUSH-64 justification displayed on every tier badge tooltip

---

## Author

Bhumika Tewari, RCC Institute of Information Technology (RCCIIT), MAKAUT, Winter Project 2026
Extended document: Section 2 Project Overview (6 layers, 5-tier hard constraint AYUSH-64 justification), Section 3 Literature Review 3.1 Purpose/Scope 3.2.A-G 7 areas, Section 4 Matrix 20 rows, Section 5 Gap with flow diagram + taxonomy + must not statement, Section 6 References 40 entries - reads as one continuous properly cross-referenced document.

---

## License

MIT - For academic research only. Not for clinical use.
