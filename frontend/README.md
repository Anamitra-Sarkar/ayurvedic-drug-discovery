# Frontend - Ayurvedic Drug Discovery Pipeline

## Stack

React 18, Vite 5, axios, 3Dmol 2.4.4, plotly.js-dist 2.33, tailwind 3.4.4, react-router-dom 6.23

## Features

- EvidenceTierBadge.jsx: 5 tiers colors icons tooltip AYUSH-64 note per tier, NOT CLINICAL PROOF Legend TierSeparator compositeComputational null principle
- MoleculeViewer.jsx: dynamic import 3dmol PDB protein + SDF ligand stick sphere wire cartoon zoom fit PNG interactions watermark 3Dmol.js Computational Pose DOCKING_RESULT badge
- CompoundCard.jsx: IMPPAT info ADMET drug-likeness QED logP TPSA HBD HBA Ayurvedic name DATABASE_DERIVED
- DockingResults.jsx: ΔG table RMSD clusters poses PLIP-style interactions amber disclaimer Vina scoring explanation mock fallback noted
- MLPredictionCard.jsx: pKd nM applicability domain inside outside uncertainty confidence
- XAIExplanation.jsx: SHAP waterfall plotly feature importance XAI_INTERPRETATION
- LiteraturePanel.jsx: RAG results citations faithfulness LITERATURE_DERIVED
- PipelineFlow.jsx: visual diagram 6 functional layers orchestrator data flow matching required pipeline flow diagram Section 5, mermaid
- CandidateRankingTable.jsx: ranked list evidence tiers separated must not present as clinical proof warning banner
- SearchBar.jsx: IMPPAT search
- NetworkGraph.jsx: network pharmacology graph Triphala example 174 bioactives 44 targets 78 diseases [4] denser combined

Pages:
- Dashboard.jsx: overview Triphala network AYUSH-64 case pipeline status EvidenceTierLegend
- CompoundDetail.jsx: all tiers single compound
- PipelineRun.jsx: run full pipeline form plant target top_n include XAI literature
- Documentation.jsx: literature review matrix gap references

Core Enforcement:
- src/utils/evidence.js central 5-tier registry DATABASE_DERIVED cyan IMPPAT curated, DOCKING_RESULT violet Vina physics-inspired mock fallback, ML_PREDICTION pink pKd applicability, XAI_INTERPRETATION orange SHAP TreeSHAP, LITERATURE_DERIVED green RAG FAISS TF-IDF fallback faithfulness, includes enforceEvidenceTier containsClinicalClaim banned-phrase blocker getDisclaimerForTiers AYUSH-64 justification per tier compositeComputational null
- src/services/api.js FastAPI client realistic mock fallback Withaferin A Curcumin Berberine Emblicanin A Chebulagic acid Piperine preserving tiers endpoints search docking ML XAI literature ranking Triphala network 174

Safety:
- Top warning banner sticky COMPUTATIONAL ONLY NO tier collapse
- Every card disclaimer per tier
- ValidationAgent checks no clinical overclaim
- ReportAgent safety guardrail Tippy [36]

## Setup

```bash
npm install
npm run dev # -> http://localhost:5173 vite proxy /api -> localhost:8000
npm run build # dist
```

## Integration

Backend at http://localhost:8000, docs at /docs

Search, docking, ML, XAI, literature, ranking, Triphala network 174 bioactives all connected.

## Evidence Enforcement

Every component shows EvidenceTierBadge with tooltip AYUSH-64 justification.

Top banner: COMPUTATIONAL ONLY, NO output may collapse tiers.

getDisclaimerForTiers() generates combined disclaimer.

containsClinicalClaim() blocks banned phrases.

CompositeComputational = null principle: computational tiers do not sum to clinical.
