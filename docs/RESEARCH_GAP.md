# Section 5 - Research and Engineering Gap

## Pipeline Flow Diagram, Five-Category Evidence Taxonomy, Must Not Statement Argued from Literature

### 5.1 Synthesis of Gap

The individual computational techniques required (network pharmacology [2][4], docking [12][13][14], PLIP interaction analysis [15], ML bioactivity [16][19][20], XAI triangulation [24], RAG literature mining [27][28][30], agentic orchestration [32][35][36]) are well established. Their systematic, reproducible application to Ayurvedic phytochemical data specifically remains underexplored.

Evidence:

- TCM bibliometric synthesis 7,288 publications 2007-2025 documents systematic shift toward integrated NP-AI-multi-omics workflows [6]. Scale and methodological maturity TCM literature relative to comparatively sparse Ayurveda-specific computational literature itself evidence of gap.
- Future perspective [1] frames NP + supercomputer-enabled VHTS + docking + repurposing as near-term direction Ayurveda-inspired drug discovery, argues synergistic-formulation discovery need not confined reformulating existing dosage forms but can extend rationally designing new multi-component combinations - direction not yet systematically implemented.
- IMPPAT [7][8] 1,742 plants 9,596 phytochemicals largest open resource with computed properties explicitly intended to support downstream virtual screening, yet downstream systematic pipeline integrating docking + ML + XAI + RAG + agentic orchestration not yet built.
- Closest existing precedent NP-plus-docking design 63 anti-epileptic Ayurvedic herbs screened 349 drug-like phytochemicals against mGluR targets similarity DrugBank anti-epileptics validation heuristic reported 11 novel neuromodulator candidates 74 phytochemicals poly-pharmacological similarity [5]. Confined single target class mGluR, does not incorporate downstream trained ML affinity model, explainability layer, automated literature-grounded validation.

Therefore gap is engineering integration + Ayurveda-specific application + evidence-tier explicitness.

### 5.2 Pipeline Flow Diagram

See PIPELINE_DIAGRAM.md for full textual and mermaid diagram.

Summary flow:

```
DatabaseAgent (IMPPAT 100 sample, Triphala 174 bioactives 44 targets 78 diseases [4], 63 herbs 349 phytochemicals 11 candidates [5]) TIER1
-> CheminformaticsAgent RDKit descriptors Lipinski QED TIER1 computed
-> DockingAgent Vina [12] 100x faster than AD4 Hybrid pKi improvement [14] RF rescoring [13] TIER2
-> InteractionAnalysisAgent PLIP [15] 7-8 types TIER2
-> MLAgent Fusion R2 0.78 vs 0.65/0.64 [20] 42-alg benchmark ExtraTrees R2 0.760 [19] leakage-aware diversity-preserving n=49 [16] TIER3
-> XAIAgent SHAP triangulation [24] bias-aware splits multi-explainer TIER4
-> LiteratureAgent RAG 0% hallucinated vs 40-60% non-RAG [27] 47.8%->12.3% faithful 0.52->0.87 acc 0.54->0.89 [28] both sides molecule+literature [30] TIER5
-> ValidationAgent Separate MAS error-propagation prevention [32] checks tier compliance no clinical overclaim citation grounding pose quality applicability Safety guardrail Tippy [36]
-> ReportAgent Ranking JSON+Markdown tier separation molecular viz 3Dmol Safety guardrail [36]
```

Orchestrated by LangGraph-style StateGraph checkpointing parallel execution error handling. Closest general architectural analogue AgentD [35] modular LLM agent framework automates multi-task pipeline coordination. Template for Report Agent safety/validation gating Tippy [36] 5-agent + Safety Guardrail first production-ready DMTA.

**Implementation:** backend/app/agents/orchestrator.py, frontend PipelineFlow.jsx visual matching required diagram.

### 5.3 Five-Category Evidence Taxonomy

See EVIDENTIARY_TIERS.md full.

Five explicit tiers:

1. DATABASE_DERIVED: IMPPAT [7][8] 27,074 associations literature-mined not experimentally validated, TCMSP [9] 29,384 ingredients, TCMID [10]. Content plant-phytochemical associations therapeutic uses physicochemical ADMET drug-likeness. Limitation literature-mined not experimentally validated [7].

2. DOCKING_RESULT: Vina [12] empirical modified Lennard-Jones H-bond hydrophobic steric up to 100x faster than AD4 improved pose accuracy, binding-affinity correlation moderate [14], DockingApp RF [13] comparable SOTA, Hybrid significant pKi improvement [14], PLIP [15] 7-8 types without manual prep. Content affinity -4 to -12 kcal/mol pose RMSD interactions. Limitation moderate correlation hypothesis not final [14] rule-based not physics [15] requires retraining new target classes [13].

3. ML_PREDICTION: TLR4 49 compounds ensemble leakage-aware diversity-preserving robust small-dataset [16] methodological template small Ayurvedic sets, Factor Xa 6,400 ChEMBL 391 Mordred 42-alg ExtraTrees R2 0.760 XGB ROC-AUC 0.962 [19] evaluation-protocol template, BACE1 docking+QSAR fusion NuSVR R2 0.78 combined vs 0.65/0.64 alone [20] justifies fusing docking output descriptor-based ML features. Content pKd nM applicability confidence. Limitation very small target-specific n=49 [16] single-target scope [19][20].

4. XAI_INTERPRETATION: XAI methods survey taxonomy bias-aware splits multi-explainer triangulation trustworthy SHAP [24] defines XAI validation protocol. Content SHAP values top features textual interpretation. Limitation survey proposes no new predictive model [24] interpretation not causal.

5. LITERATURE_DERIVED / LLM-synthesised evidence: RAG pharma 0% hallucinated vs 40-60% non-RAG [27] justifies citation-grounded Report Agent, RAG reducing hallucination 150 drug QA 10 meds Sentence-BERT FAISS reranking Llama 3.2 hallucination 47.8%->12.3% faithfulness 0.52->0.87 accuracy 0.54->0.89 narrow QA benchmark not literature-scale [28] concrete reproducible performance target, RAG for AIGC survey RetMol PromptDiff BIOREADER [30] establishes precedent RAG applicable both molecule-generation literature sides. Content citation-grounded answer retrieved passages faithfulness relevance. Limitation single-domain benchmark [27] narrow QA not literature-scale [28] not evaluated Ayurvedic data [30].

Every output must be traceable to one of five tiers, no output may collapse two tiers into single undifferentiated claim. CompositeComputational = null principle.

### 5.4 Must Not Present Computational Prediction as Clinical Proof - Argued from Literature

**Explicit statement:** Must not present computational prediction as clinical proof.

**Argued from literature rather than just copied from brief:**

- **AYUSH-64 [3] case study:** Polyherbal formulation repurposed against COVID-19 using combined NP and molecular docking and subsequently evaluated in open-label RCT as adjunct to standard care, giving rare documented example computational hypothesis being carried through to clinical evidence tier [3]. Progression instructive mainly as cautionary structural template: underscores why every output must be explicitly labelled by evidentiary tier rather than presented as single undifferentiated result. Computational (NP+docking Mpro 6LU7) -> Clinical (RCT) = separate subsequent steps, not same claim. Therefore must not collapse.

- **Vina scoring limitation [14]:** Hybrid AutoDock/Vina statistically significant improvement correlation experimental pKi, trained fixed historical PDBbind release, justifies treating raw Vina score as hypothesis not final affinity. Binding-affinity correlation with experiment only moderate [12][14]. Therefore Vina affinity -8.2 kcal/mol is computational estimate requiring experimental validation, not clinical efficacy.

- **RAG limitations [27][28][30]:** RAG 0% hallucinated citations vs 40-60% non-RAG [27] single-domain benchmark, RAG reducing hallucination 47.8%->12.3% narrow QA-pair benchmark not literature-scale retrieval [28] concrete performance target but not literature-scale, RAG for Science survey underlying systems not evaluated Ayurvedic data [30] evidence RAG applicable both stages but not evaluated Ayurvedic. Therefore RAG citation-grounded answer requires verification, narrow benchmark.

- **Agentic error-propagation risk [32]:** Agentic AI in Pharma review field-wide + DrugAgent case study review multi-agent architectures defines MAS design pattern flags error-propagation risk poorly coordinated pipelines [32] motivates explicit separate ValidationAgent. Without ValidationAgent, docking error could propagate to ML to report as clinical claim. Separate ValidationAgent prevents.

- **Triphala NP alone [4]:** Mapping 174 bioactives 44 shared targets 78 diseases revealed substantially denser bioactive-target interaction pattern combined formulation than single constituent herb supporting traditional claim synergistic rather than merely additive [4]. Illustrative what NP alone can show, but NP alone cannot show clinical efficacy. Supports synergy claim but not clinical.

- **63 herbs study [5]:** NP-plus-docking design closest existing precedent confined single target class mGluR, does not incorporate downstream trained ML affinity model, explainability layer, automated literature-grounded validation. Even this more computationally complete example stops at computational prioritization 11 novel neuromodulator candidates 74 phytochemicals similarity, not clinical proof.

- **TCM maturity gap [6]:** 7,288 publications systematic shift toward integrated NP-AI-multi-omics, scale maturity TCM relative sparse Ayurveda-specific underexplored. Individual techniques well established but systematic reproducible application Ayurvedic specifically underexplored - gap is not techniques but integration + evidence explicitness.

Therefore hard design constraint: every output traceable to one of five explicit evidentiary tiers database-derived, docking-result, ML-prediction, XAI-interpretation, literature-derived/LLM-synthesised, no output may collapse two tiers into single undifferentiated claim, must not present computational prediction as clinical proof.

**Implementation enforcement:**

- Central EvidenceValidator backend/app/core/evidence/tiers.py: EvidenceTier enum 5, TieredOutput wrapper, CLINICAL_DISCLAIMER with AYUSH-64 note, @enforce_tier decorator, validate_no_clinical_overclaim() blocks patterns clinically proven, effective treatment, cures, treats disease, clinical efficacy, patient outcome, global_registry
- Frontend evidence.js same registry, EvidenceTierBadge tooltip AYUSH-64 justification per tier, top warning banner COMPUTATIONAL ONLY NO tier collapse, containsClinicalClaim() banned-phrase blocker
- ValidationAgent checks tier compliance no clinical overclaim citation grounding pose quality applicability
- ReportAgent safety guardrail Tippy [36] validate sanitize enforce tier disclaimers separates sections by tier

**AYUSH-64 justification is concrete not assertion:** Computational NP+docking repurposing Mpro 6LU7 progressed to open-label RCT as separate subsequent step, rare documented example computational hypothesis carried through clinical tier. This progression is cautionary structural template for why every output must be labeled.

### 5.5 Engineering Gap Closed by This Pipeline

- Systematic reproducible application to Ayurvedic phytochemical data (IMPPAT primary) not just TCM
- Integration six layers + agentic orchestration LangGraph StateGraph checkpointing parallel
- Explicit five-tier evidence taxonomy with enforcement central module + frontend
- ValidationAgent separate to prevent error propagation [32]
- Safety guardrail pattern Tippy [36] for ReportAgent
- RAG citation-grounded 0% hallucinated [27] performance target 47.8%->12.3% [28] both sides [30]
- Fusion docking+QSAR R2 0.78 [20] leakage-aware n=49 template [16] 42-alg benchmark [19]
- Vina 100x faster [12] hybrid pKi improvement [14] RF rescoring [13] PLIP 7-8 types [15]
- Triphala 174 bioactives [4] 63 herbs 349 phytochemicals 11 candidates [5] as demonstration cases
- Web interface 3Dmol.js molecular visualization automated candidate ranking reporting

Reads as one continuous properly cross-referenced document rather than review bolted onto outline, with Section 2 Project Overview six layers hard constraint five tiers AYUSH-64 justification, Section 3 Literature Review 3.1 Purpose/Scope 3.2.A-G seven areas, Section 4 Matrix 20 rows, Section 5 Gap flow diagram taxonomy must not statement argued from literature, Section 6 References 40 entries.
