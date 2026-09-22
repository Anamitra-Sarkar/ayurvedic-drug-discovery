# User Guide - Ayurvedic Drug Discovery Pipeline

## For Researchers, Students, Clinicians (Computational Only)

**⚠️ WARNING: This platform outputs computational predictions tiered by evidence provenance. NO output is clinical proof. Must not present computational prediction as clinical proof - AYUSH-64 [3] shows computational -> RCT as separate step.**

## Dashboard

- Overview of six layers, five tiers, AYUSH-64 case study
- Triphala network graph: 174 bioactives 44 targets 78 diseases [4] - denser combined vs single
- AYUSH-64 card: 4 plants, Mpro 6LU7 docking, open-label RCT adjunct - justification for tier separation
- Pipeline status, recent runs
- EvidenceTierLegend with colors and AYUSH-64 tooltip per tier

## Search

- SearchBar.jsx - search IMPPAT sample by plant, phytochemical, therapeutic use
- Example: "Withania" -> withaferin A, withanolide A, MW, LogP, Ayurvedic dosha
- Filter: drug_like_only (Lipinski)
- Results: CompoundCard with ADMET, drug-likeness QED, Ayurvedic properties, DATABASE_DERIVED badge

## Compound Detail Page

Shows all 5 tiers for single compound:

1. **DATABASE_DERIVED** (cyan): IMPPAT entry, plant, SMILES, formula, therapeutic uses, ADMET, Ayurvedic rasa guna virya vipaka dosha, disclaimer literature-mined not experimentally validated [7]
2. **DOCKING_RESULT** (violet): Vina affinity, poses, RMSD, interaction profile PLIP-style 7-8 types [15], scoring info Vina 100x faster [12] moderate correlation [14], disclaimer computational estimate requires experimental validation
3. **ML_PREDICTION** (pink): pKd, nM, model StackingEnsemble top5 of 42 [19], fusion R2 0.78 [20], applicability domain, confidence, disclaimer ML prediction leakage-aware [16]
4. **XAI_INTERPRETATION** (orange): SHAP waterfall plotly, top features vina_affinity LogP QED, interpretation, method SHAP triangulation [24], disclaimer interpretation not causal
5. **LITERATURE_DERIVED** (green): RAG answer citation-grounded, citations with relevance faithfulness, metrics 0% hallucinated vs 40-60% [27] hallucination 47.8%->12.3% [28], disclaimer verify papers

MoleculeViewer: 3Dmol.js viewer PDB protein + SDF ligand stick sphere cartoon zoom fit PNG, interactions, watermark Computational Pose.

## Pipeline Run Page

Form:

- Plant names: multiselect (Withania somnifera, Bacopa monnieri, Emblica officinalis etc)
- Phytochemical names: optional
- Protein target: dropdown 10 targets (7E9G mGluR2 epilepsy [5], 6LU7 Mpro COVID AYUSH-64 [3], 3FXI TLR4 inflammation [16], 2BOH Factor Xa [19], 2WJO BACE1 [20] etc)
- Top N: 5-50
- Include XAI: checkbox
- Include Literature: checkbox
- Therapeutic area: optional

Click Run Pipeline -> calls /api/pipeline/run -> orchestrator runs:

DatabaseAgent -> CheminformaticsAgent -> DockingAgent -> InteractionAnalysisAgent -> MLAgent -> XAIAgent -> LiteratureAgent -> ValidationAgent -> ReportAgent

Progress bar shows each agent, evidence tier badge per stage.

Result: CandidateRankingTable with ranked candidates, each row shows all 5 tiers separated, weighted score but explicit disclaimer, warning banner must not present as clinical proof.

## Candidate Ranking Table

- Rank, phytochemical, plant, SMILES, docking affinity, ML pKd, confidence, applicability, SHAP top feature, literature citation count, overall score
- Each cell has EvidenceTierBadge
- Sortable by docking, ML, literature relevance
- Export JSON + Markdown report with tier separation
- Example: Withaferin A rank1 -8.2 kcal/mol pKd6.8 confidence0.82 inside domain SHAP vina_affinity 2 citations [5][16]

## Documentation Page

- Full literature review combined: Section2 Project Overview 6 layers 5-tier hard constraint AYUSH-64 justification, Section3.1 Purpose Scope, 3.2.A-G 7 areas, Section4 Matrix 20 rows landscape table, Section5 Gap flow diagram taxonomy must not statement argued from literature, Section6 References 40 entries
- Pipeline flow diagram visual
- Evidence tiers detailed
- References list

## Evidence Tier Badges

Everywhere:

- 🗄️ DATABASE_DERIVED cyan tooltip: Curated IMPPAT [7] provenance verify, AYUSH-64 note
- 🧬 DOCKING_RESULT violet tooltip: Vina [12] moderate correlation [14] hypothesis not final
- 🤖 ML_PREDICTION pink tooltip: Fusion R2 0.78 [20] leakage-aware [16] small dataset
- 🔍 XAI_INTERPRETATION orange tooltip: Triangulation [24] not causal
- 📚 LITERATURE_DERIVED green tooltip: RAG 0% hallucinated [27] narrow benchmark [28] verify

Legend shows CompositeComputational = null principle.

## Safety & Compliance

- Top sticky banner: COMPUTATIONAL ONLY, NO tier collapse
- Every card has disclaimer per tier
- ValidationAgent checks no clinical overclaim patterns blocks "clinically proven", "cures" etc
- ReportAgent safety guardrail Tippy [36] pattern validate sanitize enforce tier disclaimers
- API responses include warning field

## Example Workflows

### Triphala Synergy Study

Search "Triphala" -> Triphala network 174 bioactives 44 targets 78 diseases [4] -> view NetworkGraph -> run pipeline with plants Emblica Terminalia bellerica Terminalia chebula target 7E9G -> ranking shows denser combined pattern supports synergy claim but NOT clinical efficacy.

### AYUSH-64 Repurposing

Search "AYUSH-64" -> 4 plants Alstonia Picrorhiza Swertia Caesalpinia -> target 6LU7 Mpro -> docking -> literature RAG retrieves AYUSH-64 repurposing [3] -> report shows computational hypothesis separate from RCT adjunct.

### 63 Anti-Epileptic Herbs

Search therapeutic_use "epilepsy" -> 63 herbs 349 phytochemicals [5] -> batch dock to mGluR2 7E9G -> 11 novel neuromodulators candidates -> ML predict -> XAI -> literature -> ranking.

## Interpretation Guidelines

- DATABASE_DERIVED: Check provenance, version, literature-mined not experimentally validated [7]
- DOCKING_RESULT: Hypothesis not final affinity [14], requires experimental validation, Vina moderate correlation
- ML_PREDICTION: Check applicability domain inside/outside, confidence, small dataset n=49 [16], fusion improvement [20]
- XAI_INTERPRETATION: Interpretation of model not causal mechanism [24], triangulation recommended
- LITERATURE_DERIVED: Verify retrieved papers, narrow QA benchmark [28], RAG reduces but not eliminates hallucination [27][28]

No combination equals clinical proof.

## Export

- JSON report with all tiers, validation report, evidence_summary count per tier
- Markdown report with sections per tier, molecular viz data, citations
- Sample output in examples/sample_output.json

## For Developers

See ARCHITECTURE.md, API_DOCUMENTATION.md, SETUP_GUIDE.md.
