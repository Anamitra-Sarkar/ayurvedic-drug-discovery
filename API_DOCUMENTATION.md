# API Documentation - Ayurvedic Drug Discovery Pipeline

Base URL: http://localhost:8000

## Root

`GET /` - Pipeline info, six layers, five tiers, AYUSH-64 note, warning

`GET /api/pipeline/info` - Flow diagram, orchestration LangGraph, literature grounding numbers Triphala 174 [4], 63 herbs 349 [5], IMPPAT 1742 9596 [7], TCM 7288 pubs [6], Vina 100x faster [12], hybrid pKi improvement [14], PLIP 7-8 types [15], TLR4 n=49 leakage-aware [16], Factor Xa 42-alg ExtraTrees R2 0.760 XGB ROC-AUC 0.962 [19], BACE1 R2 0.78 combined [20], XAI triangulation [24], RAG 0% hallucinated vs 40-60% [27], 47.8%->12.3% [28], both sides [30], MAS error-propagation [32], AgentD [35], Tippy 5-agent Safety Guardrail [36]

## Health

`GET /api/health` - from api/main.py

## Database

`GET /api/database/search?q=&plant=&therapeutic_use=&drug_like_only=bool` - Search IMPPAT sample, returns results evidence_tier DATABASE_DERIVED source IMPPAT 2.0 [7][8]

`GET /api/database/plants` - List plants

`GET /api/database/triphala` - Triphala case 174 bioactives 44 shared targets 78 diseases [4] denser combined than single

`GET /api/database/ayush64` - AYUSH-64 formulation plants repurposing Mpro 6LU7 open-label RCT adjunct [3] justification computational -> RCT separate step must not collapse

## Docking

`POST /api/docking/run` - Body: {smiles, protein_pdb_id="7E9G", phytochemical_name, num_poses=5} - Runs DockingAgent Vina empirical scoring Lennard-Jones H-bond hydrophobic steric [12] 100x faster than AutoDock4, hybrid [14], RF rescoring [13], PLIP [15] 7-8 types, returns binding_affinity_kcal_mol poses interactions evidence_tier DOCKING_RESULT disclaimer moderate correlation requires experimental validation mock_used flag

`GET /api/docking/scoring-info` - Primary engine Vina [12] speed 100x, scoring empirical, limitation moderate correlation hypothesis not final [14], rescoring DockingApp RF [13] comparable SOTA, hybrid significant pKi [14], interaction PLIP [15]

## ML

`POST /api/ml/predict` - Body: {smiles, docking_affinity, features} - MLAgent fusion docking+QSAR R2 0.78 combined vs 0.65/0.64 [20] StackingEnsemble top5 42 [19] leakage-aware diversity-preserving [16] returns predicted_pKd affinity_nM model features_used fusion_improvement applicability_domain confidence evidence_tier ML_PREDICTION disclaimer

`GET /api/ml/models` - Benchmark 42-alg ExtraTrees R2 0.760 XGB ROC-AUC 0.962 [19] implemented top5 RF ExtraTrees XGB HistGradientBoosting NuSVR small n=49 [16] StackingEnsemble, training_data synthetic PDBBind-like 500 physics-inspired pKd, splitting leakage-aware GroupKFold scaffold hash KMeans diversity [16], fusion docking+QSAR [20]

`POST /api/ml/explain` - Body: {smiles, docking_affinity} - XAIAgent SHAP triangulation [24] returns shap_values top_features interpretation method bias-aware

## Literature

`GET /api/literature/query?q=&top_k=5` - LiteratureAgent RAG Sentence-BERT FAISS reranking Llama3.2 style [28] returns answer citations retrieval_metrics hallucination_rate 0% vs 40-60% non-RAG [27] faithfulness 0.52->0.87 accuracy 0.54->0.89 47.8%->12.3% [28] evidence_tier LITERATURE_DERIVED disclaimer

`GET /api/literature/rag-info` - Retriever Sentence-BERT FAISS TF-IDF fallback, generator citation-grounded 0% hallucinated [27], performance target 47.8%->12.3% [28], applicability both sides RetMol PromptDiff BIOREADER [30], corpus 40 refs 7 areas

`GET /api/literature/references` - 40 refs

## Pipeline

`POST /api/pipeline/run` - Body: {plant_names, phytochemical_names, protein_target="7E9G", top_n=10, include_xai=True, include_literature=True, therapeutic_area} - Runs full 6-layer orchestrator Database -> Cheminformatics -> Docking -> Interaction -> ML -> XAI -> Literature -> Validation -> Report, every output tagged 5-tier, AYUSH-64 enforced, returns request_id status candidates evidence_summary validation_report report_path warning COMPUTATIONAL ONLY

`GET /api/pipeline/status/{request_id}` - Status

`GET /api/pipeline/targets` - 10 targets mGluR2 7E9G epilepsy [5], 6LU7 Mpro COVID AYUSH-64 [3], 3FXI TLR4 inflammation [16], 2BOH Factor Xa [19], 2WJO BACE1 [20] etc

## Schemas

All Pydantic models include evidence_tier field:

- Phytochemical: plant, phytochemical, SMILES, formula, MW, therapeutic uses, ADMET, drug-likeness, Ayurvedic properties, evidence_tier DATABASE_DERIVED
- ProteinTarget: pdb_id, name, disease, source literature
- DockingResult: smiles, protein, affinity, poses, interactions, evidence_tier DOCKING_RESULT, disclaimer moderate correlation, scoring_function Vina [12], mock_used, warning NOT clinical proof
- MLPrediction: smiles, predicted_pKd, affinity_nM, model StackingEnsemble top5 42 [19], features_used, fusion_improvement R2 0.78 [20], applicability_domain, confidence, evidence_tier ML_PREDICTION, disclaimer leakage-aware [16]
- XAIExplanation: shap_values, top_features, interpretation, method SHAP triangulation [24], evidence_tier XAI_INTERPRETATION
- LiteratureEvidence: query, answer, citations id title year relevance faithfulness, retrieval_metrics hallucination 0% vs 40-60% [27] 47.8%->12.3% [28], evidence_tier LITERATURE_DERIVED
- CandidateRanking: rank, phytochemical, plant, SMILES, docking affinity, ML pKd, confidence, applicability, SHAP top feature, literature citation count, overall score, all tiers separated
- PipelineRequest/Response: request_id, candidates, evidence_summary counts per tier, validation_report passed checks tier_compliance no_clinical_overclaim citation_grounding ayush64_compliant, warning

## Evidence Enforcement

Every response includes evidence_tier, disclaimer, warning field.

ValidationAgent checks: tier_compliance, no_clinical_overclaim (blocks clinically proven, effective treatment, cures, treats disease, clinical efficacy, patient outcome), citation_grounding, pose quality, applicability.

ReportAgent safety guardrail Tippy [36] validate sanitize enforce tier disclaimers.

## Errors

Global exception handler returns evidence_tier SYSTEM_ERROR disclaimer not scientific result must_not interpret as clinical.

## Frontend Integration

Frontend api.js client calls these endpoints, with realistic mock fallback preserving tiers: Withaferin A, Curcumin, Berberine, Emblicanin A, Chebulagic acid, Piperine etc.

Search, docking, ML, XAI, literature, ranking, Triphala network 174 bioactives.

## Docs

Swagger at /docs, ReDoc at /redoc
