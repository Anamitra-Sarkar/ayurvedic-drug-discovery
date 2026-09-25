# Phase 1 — Literature Review & Research Design

**Status: Complete.**

## Goal

Establish the scientific and engineering foundation for the project by surveying the
relevant literature across all required areas, identifying the concrete research gap
this project fills, and formalizing research questions before any implementation
begins.

## 1.1 Literature Review

A full literature review covering all seven required areas — (A) computational
Ayurvedic/traditional-medicine drug discovery, (B) phytochemical and
traditional-medicine databases, (C) molecular docking and protein–ligand interaction
analysis, (D) machine learning for bioactivity and binding-affinity prediction, (E)
explainable AI in drug discovery, (F) large language models and retrieval-augmented
generation for scientific literature, and (G) agentic AI for computational
drug-discovery workflows — was conducted and is published in full at
`docs/LITERATURE_REVIEW_COMBINED.md`. It reuses and extends the client's own
pre-written literature review (`docs/client_provided/`), reading as one continuous,
cross-referenced document rather than a review bolted onto an outline, structured as:

- **Section 2 — Project Overview**: the six functional layers this project
  implements, and the hard evidentiary-tier constraint (every output traceable to one
  of five tiers, never collapsed into an undifferentiated claim), justified concretely
  by the AYUSH-64 case study (a computational hypothesis carried to a randomised
  controlled trial as a separate, subsequent step) rather than asserted.
- **Section 3 — Literature Review**: 3.1 states purpose and scope; 3.2.A through 3.2.G
  cover all seven required areas in full, sourced from peer-reviewed journals
  (Scientific Reports, Journal of Cheminformatics, Nucleic Acids Research, PLOS ONE,
  ACS Omega, Expert Opinion on Drug Discovery, WIREs Computational Molecular Science,
  among others), PubMed/PMC, and — for the fastest-moving sub-areas (agentic AI, RAG),
  where peer-reviewed coverage is still emerging as of 2026 — recent arXiv/bioRxiv
  preprints and industry technical reports.

## 1.2 Literature Matrix

Twenty of the most directly relevant sources are organised into a structured
literature matrix at `docs/LITERATURE_MATRIX.md` (Section 4/9 of the combined
review), covering method, dataset, key finding, and relevance-to-this-project for
each entry.

## 1.3 Research Gap

Formalised at `docs/RESEARCH_GAP.md` and Section 5 of the combined review. In
summary: every individual computational stage this project requires — network
pharmacology and docking for Ayurvedic/TCM formulations, curated phytochemical
databases, docking engines with quantified accuracy trade-offs, automated
protein–ligand interaction profiling, tree-ensemble ML for binding-affinity
prediction with rigorous small-dataset methodology, SHAP-based explainability,
retrieval-augmented generation with measured hallucination reduction, and multi-agent
orchestration — is independently well-precedented and validated in the literature.
What the literature does not yet show is a single reproducible pipeline that chains
all of these stages together **specifically for Ayurvedic phytochemicals**, with
every output explicitly labelled by evidentiary tier rather than presented as an
undifferentiated result. This is the concrete gap this project addresses, expressed
as a real pipeline-flow diagram, a five-category evidence taxonomy, and an explicit
"must not present a computational prediction as clinical proof" constraint — all
argued from the literature reviewed, not copied from the original brief.

## 1.4 Research Questions

Derived directly from the identified gap:

1. Can the six functional layers (database, cheminformatics, docking, ML, XAI,
   literature RAG) be integrated into a single reproducible, agent-orchestrated
   pipeline for Ayurvedic phytochemical candidate prioritisation?
2. Can every output of such a pipeline be reliably tagged with an explicit
   evidentiary tier, with an automated validation layer that actively prevents any
   output from being presented as clinical or experimental proof?
3. Given the real, structurally small labeled binding-affinity data available for
   this domain, what is the honestly achievable predictive performance of a
   supervised ML model trained with leakage-aware, scaffold-based splitting — and how
   should that performance be reported without overstating it? (Answered concretely
   in Phase 3/6: MAE 1.35, R² 0.01 on 181 real training complexes — see
   `phase-3-training-benchmarking.md`.)
4. Can retrieval-augmented generation against a fixed literature corpus be made to
   correctly refuse to answer, rather than hallucinate, when the corpus genuinely has
   no information on a queried compound? (Answered concretely in Phase 5/6 — observed
   live in production.)

## 1.5 Phase 1 Deliverables

| Deliverable | Location | Status |
|---|---|---|
| Full literature review, all 7 areas | `docs/LITERATURE_REVIEW_COMBINED.md` | Done |
| Literature matrix (20 rows) | `docs/LITERATURE_MATRIX.md` | Done |
| Research gap statement | `docs/RESEARCH_GAP.md` | Done |
| Research questions | This document, §1.4 | Done |
| Reference list (40 entries) | `docs/REFERENCES.md` | Done |
| Pipeline-flow diagram | `docs/PIPELINE_DIAGRAM.md` | Done |

---
*Next: [Phase 2 — Data Collection, Segregation & Cleaning](phase-2-data-collection.md)*
