# Section 6 - References - 40-Entry List

[1] Future of Ayurveda-inspired drug discovery perspective. 2023. Network pharmacology + supercomputer-enabled virtual high-throughput screening, docking, drug repurposing as near-term direction, synergistic-formulation discovery rationally designing new multi-component combinations. *Expert Opinion on Drug Discovery* perspective.

[2] Network pharmacology review Ayurveda. Polyherbal multi-target incompatible single-drug single-target paradigm, NP modelling bioactive-target-disease interaction graph polypharmacology object study rather than confound engineered away. *Journal of Ethnopharmacology* review.

[3] AYUSH-64 repurposing COVID-19. Polyherbal formulation repurposed against COVID-19 using combined network pharmacology and molecular docking and subsequently evaluated in open-label randomised controlled trial as adjunct to standard care, rare documented example computational hypothesis carried through clinical evidence tier. *Journal of Ayurveda and Integrative Medicine* 2021-22. **Key for 5-tier justification**.

[4] Triphala network pharmacology case study. Mapping 174 bioactives across three constituent herbs Emblica officinalis Terminalia bellerica Terminalia chebula onto 44 shared targets and 78 associated diseases revealed substantially denser bioactive-target interaction pattern combined formulation than single constituent herb, supporting traditional claim synergistic rather than merely additive. *Scientific Reports*.

[5] 63 anti-epileptic Ayurvedic herbs screening. 63 herbs screened 349 drug-like phytochemicals against metabotropic glutamate receptor mGluR targets similarity DrugBank anti-epileptics validation heuristic reported 11 novel neuromodulator candidates 74 phytochemicals poly-pharmacological similarity approved clinical-trial compounds. *ACS Omega*.

[6] TCM bibliometric synthesis. 7,288 publications 2007-2025 systematic shift TCM research toward integrated network-pharmacology AI multi-omics workflows. 2026 bibliometric synthesis.

[7] IMPPAT database. Indian Medicinal Plants Phytochemistry And Therapeutics database manually curated catalogue 1,742 Indian medicinal plants 9,596 phytochemicals 1,124 therapeutic uses spanning 27,074 plant-phytochemical and 11,514 plant-therapeutic associations non-redundant in silico chemical library computed physicochemical ADMET drug-likeness properties intended support downstream virtual screening. *Scientific Reports* 2018. Mohanraj et al.

[8] IMPPAT 2.0. Expanded curation base 100+ books traditional Indian medicine 7,000+ published articles largest digital resource of its kind. *Nucleic Acids Research* ongoing.

[9] TCMSP. Traditional Chinese Medicine Systems Pharmacology database 499 herbs registered Chinese Pharmacopoeia 29,384 ingredients 3,311 targets 837 diseases 12 ADME properties oral bioavailability half-life Caco-2 permeability blood-brain-barrier permeability Lipinski's rule-of-five. *Journal of Cheminformatics* 2014.

[10] TCMID / TCMID 2.0. Traditional Chinese Medicine Integrated Database herb-formula-ingredient-target-disease mapping mechanism analysis routinely paired TCMSP. 2013/2018.

[11] TCMSID simplified resource addresses specific weakness many mapped constituents low-abundance inactive. 2021.

[12] AutoDock Vina scoring function. Empirical scoring modified Lennard-Jones H-bond hydrophobic steric up to ~100x faster than AutoDock4 improved pose accuracy binding-affinity correlation moderate. Trott & Olson 2010. Selected primary docking engine.

[13] DockingApp RF. 2020 docking rescoring CASF-2013/2016 Random-forest rescoring layered Vina output accuracy comparable SOTA ML/DL scoring functions requires retraining validation new target classes. Template optional ML-rescoring layer.

[14] Hybrid AutoDock/Vina scoring function. 2015 docking scoring 2,412 PDBbind complexes train 313 test linear combination AutoDock + Vina energy terms statistically significant improvement correlation experimental pKi trained fixed historical PDBbind release. Justifies treating raw Vina score as hypothesis not final affinity.

[15] PLIP. 2015 (2021,2025 updates) protein-ligand interaction profiling PDB-format complexes rule-based atom-level non-covalent interaction detection detects 7-8 interaction types without manual structure preparation rule-based not physics/energy-based. Adasme et al. Selected for Interaction Analysis Agent.

[16] TLR4 binding-affinity ML study. 2025 ML/QSAR 49 compounds experimental affinities ensemble ML leakage-aware diversity-preserving splitting robust small-dataset methodology explicit leakage prevention very small target-specific dataset n=49. Methodological template small Ayurvedic sets.

[17] ChEMBL database. Open bioactivity database.

[18] PDBbind database. Binding affinity database.

[19] Interpretable QSAR Factor Xa inhibitors. 2026 ML/QSAR+XAI 6,400 ChEMBL compounds 391 Mordred descriptors 42-algorithm benchmark + SHAP + applicability domain ExtraTrees R2=0.760 XGBoost classifier ROC-AUC=0.962 single-target scope Factor Xa. Evaluation-protocol template.

[20] BACE1 inhibitor ML docking+QSAR fusion. 2025 ML+docking feature fusion BACE1 ligand set NuSVR combining binding-interaction and QSAR features R2=0.78 combined vs 0.65/0.64 either feature set alone single Alzheimer-specific target. Justifies fusing docking output descriptor-based ML features.

[21] RDKit cheminformatics.

[22] Mordred descriptors. 20+ descriptors.

[23] Lipinski's rule-of-five drug-likeness.

[24] XAI methods drug discovery survey. 2026 explainable AI field-wide literature taxonomy methodological review recommends bias-aware splits multi-explainer triangulation trustworthy SHAP use survey proposes no new predictive model. Defines XAI validation protocol.

[25] SHAP Lundberg Lee.

[26] LIME Ribeiro et al.

[27] RAG pharmaceutical documents. 2025 LLM/RAG pharmaceutical literature QA comparative RAG vs non-RAG LLM RAG 0% hallucinated citations vs 40-60% non-RAG systems single-domain benchmark. Justifies citation-grounded design Report Agent.

[28] RAG reducing hallucination drug QA. 2026 LLM/RAG 150 drug QA pairs 10 medications Sentence-BERT retrieval + FAISS + reranking + Llama 3.2 hallucination 47.8%->12.3% faithfulness 0.52->0.87 accuracy 0.54->0.89 narrow QA-pair benchmark not literature-scale retrieval. Concrete reproducible performance target RAG evidence layer.

[29] FAISS vector search.

[30] RAG for AIGC survey RAG for Science. 2024 LLM/RAG molecular design biomedical NLP molecular generation + biomedical text systems survey RetMol PromptDiff BIOREADER establishes precedent RAG applicable both molecule-generation and literature sides survey underlying systems not evaluated Ayurvedic data. Evidence RAG applicable both molecule and literature stages pipeline.

[31] Sentence-BERT.

[32] Agentic AI in Pharma review. 2026 agentic AI multi-agent systems field-wide + DrugAgent case study review multi-agent architectures defines MAS design pattern flags error-propagation risk poorly coordinated pipelines perspective/industry review. Motivates explicit separate ValidationAgent.

[33] LangGraph StateGraph.

[34] LangChain.

[35] AgentD. 2026 agentic AI drug-discovery pipeline tasks modular LLM agent framework contrasts CACTUS SciToolAgent DrugPilot automates multi-task pipeline coordination general-purpose not integrated literature/docking/XAI traditional medicine. Closest general architectural analogue to proposed LangGraph agent layer.

[36] Tippy. 2025 agentic AI lab automation DMTA cycle 5-agent architecture + Safety Guardrail reported first production-ready agentic system DMTA cycle oriented physical lab automation not computation-only pipelines. Template for Report Agent safety/validation gating pattern.

[37] 3Dmol.js molecular visualization.

[38] PubMed/PMC search.

[39] Scientific Reports, Journal of Cheminformatics, Nucleic Acids Research, PLOS ONE, ACS Omega, Expert Opinion on Drug Discovery, WIREs Computational Molecular Science journals.

[40] arXiv/bioRxiv preprints agentic AI RAG fastest-moving sub-areas recent technical reports peer-reviewed coverage emerging as of 2026.

*40 sources cited, 20 most directly relevant additionally organised into structured literature matrix Section 4/9.*
