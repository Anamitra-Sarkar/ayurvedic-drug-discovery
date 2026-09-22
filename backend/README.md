# Backend - Ayurvedic Drug Discovery Pipeline

## Six Layers Implementation

See ARCHITECTURE.md for full.

### Quick Start

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Agents

- DatabaseAgent: IMPPAT sample 100, Triphala 174 bioactives 44 targets 78 diseases [4], 63 herbs 349 phytochemicals 11 candidates [5], IMPPAT 1742 9596 27074 associations [7]
- CheminformaticsAgent: RDKit descriptors fallback hash
- DockingAgent: Vina wrapper + mock physics-inspired -4 to -12 kcal/mol, Hybrid AutoDock+Vina [14], DockingApp RF [13]
- InteractionAnalysisAgent: PLIP mimic 8 types [15]
- MLAgent: Fusion R2 0.78 [20], 42-alg ExtraTrees R2 0.760 XGB ROC-AUC 0.962 [19], leakage-aware n=49 [16]
- XAIAgent: SHAP triangulation [24]
- LiteratureAgent: RAG 0% hallucinated vs 40-60% [27], 47.8%->12.3% faithful 0.52->0.87 acc 0.54->0.89 [28], both sides [30]
- ValidationAgent: Separate MAS error-propagation prevention [32], safety guardrail Tippy [36]
- ReportAgent: Ranking JSON+Markdown tier separation molecular viz data
- Orchestrator: LangGraph StateGraph checkpointing parallel AgentD [35] closest analogue

### Evidence Enforcement

backend/app/core/evidence/tiers.py + evidence.py central:
- EvidenceTier enum 5: DATABASE_DERIVED, DOCKING_RESULT, ML_PREDICTION, XAI_INTERPRETATION, LITERATURE_DERIVED
- TieredOutput wrapper
- @enforce_tier decorator
- validate_no_clinical_overclaim() blocks clinically proven etc
- CLINICAL_DISCLAIMER with AYUSH-64 note [3] computational -> RCT separate step rare documented example

Every API response includes evidence_tier.

### Data

- app/data/imppat_sample.json 100 phytochemicals: 20 Triphala (Emblica Terminalia bellerica Terminalia chebula gallic acid ellagic acid chebulagic acid chebulinic acid corilagin), 20 AYUSH-64 (Alstonia scholaris echitamine alstonine, Picrorhiza kurroa picroside I II kutkoside, Swertia chirata amarogentin mangiferin, Caesalpinia crista), 60 anti-epileptic (Bacopa bacoside A B, Withania withanolide A withaferin A, Nardostachys Valeriana Centella etc)
- app/data/proteins/targets.json 10 targets mGluR2 7E9G mGluR3 5CNK TLR4 3FXI Factor Xa 2BOH BACE1 2WJO Mpro 6LU7 AYUSH-64 etc
- app/data/literature_corpus/references.json 40 refs 7 areas A-G
- app/data/ml/training_data.csv 500 synthetic PDBBind-like physics-inspired pKd = -vina + MW LogP QED + privileged + hbond clipped [3,10.5]
- app/models/ml_rescorer.pkl DockingApp RF style RandomForest 1200 synthetic RMSE ~0.7

### Endpoints

See API_DOCUMENTATION.md

### Testing

pytest tests/ -v
