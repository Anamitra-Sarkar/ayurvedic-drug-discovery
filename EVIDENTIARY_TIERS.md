# Evidentiary Tiers - Five-Category Taxonomy + Hard Constraint

## Five Tiers:

### Tier 1: DATABASE_DERIVED
- **Source:** IMPPAT [7][8] 1,742 plants 9,596 phytochemicals 27,074 associations, TCMSP [9], TCMID [10], PubChem, ChEMBL, PDB
- **Content:** Plant-phytochemical associations, therapeutic uses, physicochemical ADMET drug-likeness computed properties, literature-mined not experimentally validated
- **Limitation:** Associations are literature-mined not experimentally validated [7]
- **Implementation:** DatabaseAgent, CheminformaticsAgent computed descriptors
- **Disclaimer:** Curated database entry, verify provenance and version, literature-mined not experimentally validated
- **Example:** Withania somnifera contains withaferin A, SMILES ..., therapeutic uses: anti-epileptic, MW 470.6, LogP 3.2
- **Color:** Cyan 🗄️

### Tier 2: DOCKING_RESULT
- **Source:** AutoDock Vina [12] empirical scoring modified Lennard-Jones + H-bond + hydrophobic + steric, up to 100x faster than AutoDock4 improved pose accuracy, binding-affinity correlation moderate [14]
- **Rescoring:** DockingApp RF [13] Random Forest rescoring layered on Vina comparable SOTA, Hybrid AutoDock/Vina [14] significant pKi improvement
- **Interaction:** PLIP [15] rule-based atom-level 7-8 types without manual prep
- **Content:** Binding affinity kcal/mol, pose, RMSD, interaction profile
- **Limitation:** Binding-affinity correlation with experiment only moderate, trained on fixed historical PDBbind release [14], rule-based not physics/energy-based [15]
- **Implementation:** DockingAgent, InteractionAnalysisAgent, vina_wrapper.py, scoring.py, interactions.py
- **Disclaimer:** Computational docking estimate, requires experimental validation, NOT clinical proof, treat raw Vina score as hypothesis not final affinity
- **Example:** Withaferin A docks to mGluR2 7E9G with -8.2 kcal/mol, 2 H-bonds TYR58 HIS102, hydrophobic PHE77
- **Color:** Violet 🧬

### Tier 3: ML_PREDICTION
- **Source:** Ensemble ML leakage-aware diversity-preserving splitting robust small-dataset n=49 [16], 42-algorithm benchmark ExtraTrees R2 0.760 XGBoost ROC-AUC 0.962 [19], BACE1 fusion R2 0.78 combined vs 0.65/0.64 alone [20]
- **Content:** Predicted pKd, affinity nM, classification active/inactive, applicability domain inside/outside, confidence
- **Limitation:** Very small target-specific dataset [16], single-target scope [19][20], requires retraining for new target classes [13]
- **Implementation:** MLAgent, core/ml/features.py fusing docking+QSAR, models.py top5, training.py leakage-aware GroupKFold
- **Disclaimer:** ML prediction, small dataset methodology, applicability domain check, requires wet-lab validation
- **Example:** Withaferin A predicted pKd 6.8 (157 nM), confidence 0.82, inside applicability domain
- **Color:** Pink 🤖

### Tier 4: XAI_INTERPRETATION
- **Source:** XAI methods survey taxonomy bias-aware splits multi-explainer triangulation [24]
- **Content:** SHAP values, top features, textual interpretation, LIME, feature importance
- **Limitation:** Survey proposes no new predictive model [24], interpretation of model not causal biological mechanism
- **Implementation:** XAIAgent, shap_explainer.py, lime_explainer.py
- **Disclaimer:** Interpretation of ML model, not causal mechanism, bias-aware splits, triangulation recommended
- **Example:** vina_affinity +0.45, LogP +0.32 drive predicted activity, consistent hydrophobic pocket occupation
- **Color:** Orange 🔍

### Tier 5: LITERATURE_DERIVED
- **Source:** RAG pharma 0% hallucinated vs 40-60% non-RAG [27], RAG reducing hallucination 47.8%->12.3% faithfulness 0.52->0.87 accuracy 0.54->0.89 Sentence-BERT + FAISS + reranking + Llama 3.2 [28], RAG for Science RetMol PromptDiff BIOREADER [30]
- **Content:** Citation-grounded answer, retrieved passages, faithfulness score, relevance
- **Limitation:** Single-domain benchmark [27], narrow QA-pair benchmark not literature-scale retrieval [28], underlying systems not evaluated on Ayurvedic data [30]
- **Implementation:** LiteratureAgent, retriever.py, generator.py, corpus.py 40 refs
- **Disclaimer:** RAG citation-grounded, requires verification of retrieved papers, narrow benchmark
- **Example:** Withania somnifera reported anti-epileptic in 63 herbs study 349 phytochemicals [5], Triphala synergy 174 bioactives [4]
- **Color:** Green 📚

## Hard Constraint Enforcement:

**Rule:** Every output must be traceable to one of five tiers, no output may collapse two tiers into single undifferentiated claim.

**Central Enforcement Module:** backend/app/core/evidence/tiers.py, evidence.py, frontend/src/utils/evidence.js

- EvidenceTier enum 5 values
- TieredOutput wrapper with tier, disclaimer, citation, timestamp, hash
- @enforce_tier decorator
- validate_no_clinical_overclaim() blocks patterns: "clinically proven", "effective treatment", "cures", "treats disease", "clinical efficacy", "patient outcome"
- global_registry logs all outputs with tier

**Frontend Enforcement:**
- EvidenceTierBadge.jsx shows color/icon/tooltip with AYUSH-64 note per tier
- Top warning banner: COMPUTATIONAL ONLY, NO tier collapse
- getDisclaimerForTiers() generates combined disclaimer
- containsClinicalClaim() blocks banned phrases
- compositeComputational = null principle

**AYUSH-64 Justification:**
AYUSH-64 [3] repurposed via NP+docking Mpro 6LU7, then open-label RCT adjunct standard care. Computational hypothesis carried to clinical evidence tier as separate subsequent step. Therefore computational prediction ≠ clinical proof. This progression is cautionary structural template.

**Must Not Statement:**
Must not present computational prediction as clinical proof - argued from literature rather than just copied from brief:
- AYUSH-64 [3] shows computational -> RCT as separate steps, rare documented example
- Vina moderate correlation [14] justifies treating raw Vina score as hypothesis not final affinity
- RAG hallucination reduction but narrow benchmark [28] not literature-scale retrieval, requires verification
- Agentic Pharma review error-propagation risk poorly coordinated pipelines [32] motivates separate ValidationAgent
- Triphala NP alone can show synergy but not clinical efficacy [4]

**CompositeComputational = null:** DOCKING_RESULT + ML_PREDICTION + XAI + LITERATURE ≠ CLINICAL_PROOF. No sum of computational tiers equals clinical tier. Clinical tier only via separate RCT [3].

## Implementation Checklist:

- [x] backend/app/core/evidence/tiers.py defines 5 tiers, disclaimers, @enforce_tier, validate_no_clinical_overclaim, CLINICAL_DISCLAIMER with AYUSH-64 note
- [x] Every agent returns TieredOutput with evidence_tier
- [x] ValidationAgent checks tier compliance, no clinical overclaim, citation grounding
- [x] Frontend evidence.js central registry same 5 tiers
- [x] EvidenceTierBadge tooltip includes AYUSH-64 justification per tier
- [x] API responses include evidence_tier field
- [x] ReportAgent separates sections by tier, no collapse
- [x] Warning banner COMPUTATIONAL ONLY on all pages
