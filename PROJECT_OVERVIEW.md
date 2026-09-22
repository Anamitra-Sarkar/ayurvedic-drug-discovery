# Section 2 - Project Overview

## Six Functional Layers + Hard Constraint

This project develops an end-to-end computational platform for identifying and prioritising candidate therapeutic compounds from Ayurvedic and other traditional-medicine phytochemical sources.

### Layers:

**(i) Curated Phytochemical and Traditional-Medicine Databases**
- IMPPAT primary: 1,742 plants, 9,596 phytochemicals, 1,124 therapeutic uses, 27,074 plant-phytochemical, 11,514 plant-therapeutic associations, non-redundant in silico chemical library with computed physicochemical, ADMET, drug-likeness [7]
- IMPPAT 2.0: 100+ books, 7,000+ articles, largest digital resource [8]
- Complementary: TCMSP 499 herbs 29,384 ingredients 3,311 targets 837 diseases 12 ADME [9], TCMID 2.0 [10]
- Implementation: backend/app/agents/database_agent.py, data/imppat_sample.json 100 sample covering Triphala, AYUSH-64, 63 anti-epileptic herbs

**(ii) Cheminformatic Molecular-Structure Processing**
- RDKit descriptors, Mordred-like 20, Lipinski, Veber, PAINS, QED, SA
- SMILES validation, 3D conformer generation
- Implementation: backend/app/agents/cheminformatics_agent.py, core/cheminformatics/descriptors.py, filters.py
- Evidence: DATABASE_DERIVED + COMPUTED

**(iii) Structure-Based Protein-Ligand Molecular Docking**
- Vina empirical scoring modified Lennard-Jones + H-bond + hydrophobic + steric [12] up to 100x faster than AutoDock4 improved pose accuracy
- Rescoring: DockingApp RF Random Forest layered on Vina comparable SOTA ML/DL [13] template for optional ML-rescoring layer
- Hybrid AutoDock/Vina linear combination 2,412 PDBbind train 313 test statistically significant improvement correlation experimental pKi [14] justifies treating raw Vina score as hypothesis not final affinity
- Interaction: PLIP [15] 2015 (2021,2025 updates) rule-based atom-level 7-8 types without manual structure prep selected for Interaction Analysis Agent
- Implementation: backend/app/agents/docking_agent.py, interaction_agent.py, core/docking/vina_wrapper.py, scoring.py, interactions.py
- Evidence: DOCKING_RESULT

**(iv) Supervised ML for Binding-Affinity Prediction**
- TLR4 binding-affinity ML 49 compounds ensemble leakage-aware diversity-preserving splitting robust small-dataset methodology explicit leakage prevention [16] methodological template given similarly small Ayurvedic training sets
- Factor Xa 6,400 ChEMBL 391 Mordred 42-algorithm benchmark + SHAP + applicability domain ExtraTrees R2 0.760 XGBoost ROC-AUC 0.962 single-target scope [19] evaluation-protocol template
- BACE1 inhibitor ML docking+QSAR fusion NuSVR combining binding-interaction and QSAR features R2 0.78 combined vs 0.65/0.64 either alone [20] justifies fusing docking output with descriptor-based ML features
- Implementation: backend/app/agents/ml_agent.py, core/ml/features.py (fusing), models.py (top5), training.py (leakage-aware GroupKFold + KMeans)
- Evidence: ML_PREDICTION

**(v) Explainable AI**
- XAI methods survey taxonomy bias-aware splits multi-explainer triangulation for trustworthy SHAP use [24] defines XAI validation protocol
- Implementation: backend/app/agents/xai_agent.py, core/xai/shap_explainer.py, lime_explainer.py
- Evidence: XAI_INTERPRETATION

**(vi) Scientific-Literature Mining via RAG + Agentic Orchestration + Web Interface**
- RAG pharma 0% hallucinated citations vs 40-60% non-RAG [27] justifies citation-grounded Report Agent
- RAG reducing hallucination drug QA 150 pairs 10 meds Sentence-BERT retrieval + FAISS + reranking + Llama 3.2 hallucination 47.8%->12.3% faithfulness 0.52->0.87 accuracy 0.54->0.89 narrow benchmark [28] concrete reproducible performance target for RAG evidence layer
- RAG for AIGC survey RetMol PromptDiff BIOREADER [30] establishes precedent RAG applicable both molecule and literature stages
- Agentic AI in Pharma review field-wide + DrugAgent case study review multi-agent architectures defines MAS design pattern flags error-propagation risk poorly coordinated pipelines [32] motivates separate ValidationAgent
- AgentD 2026 agentic AI drug-discovery pipeline modular LLM agent framework contrasts CACTUS SciToolAgent DrugPilot automates multi-task coordination general-purpose not integrated with literature/docking/XAI for traditional medicine [35] closest general architectural analogue to proposed LangGraph agent layer
- Tippy 2025 agentic AI lab automation DMTA cycle 5-agent architecture + Safety Guardrail first production-ready agentic system DMTA cycle oriented physical lab automation not computation-only [36] template for Report Agent and safety/validation gating pattern
- Implementation: backend/app/agents/literature_agent.py, validation_agent.py, report_agent.py, orchestrator.py (LangGraph StateGraph checkpointing parallel), frontend/src/components/* with 3Dmol.js
- Evidence: LITERATURE_DERIVED for literature agent, all tiers enforced

### Hard Constraint:

Explicit objective computational candidate prioritisation narrowing large space down to short evidence-labelled list worth further (wet-lab or clinical) investigation. Not claim experimental validation, not claim clinically effective. Distinction motivated directly by literature AYUSH-64 case study [3] where computational prediction later carried to RCT as separate subsequent step, treated as hard design constraint rather than caveat appended after fact: every output must be traceable to one of five explicit evidentiary tiers database-derived, docking-result, ML-prediction, XAI-interpretation, literature-derived/LLM-synthesised and no output may collapse two tiers into single undifferentiated claim.

### AYUSH-64 Justification:

AYUSH-64 polyherbal formulation repurposed against COVID-19 using combined network pharmacology and molecular docking and subsequently evaluated in open-label RCT as adjunct to standard care, giving rare documented example computational hypothesis carried through to clinical evidence tier [3]. Progression instructive mainly as cautionary structural template: underscores why every output must be explicitly labelled by evidentiary tier rather than presented as single undifferentiated result.

Computational (NP+docking Mpro 6LU7) -> Clinical (RCT) = separate steps, not same claim. Therefore CompositeComputational = null, computational tiers do not sum to clinical.
