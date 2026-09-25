# Phase 8 — Final Report & Live Demonstration

**Status: Complete** (final report). A slide presentation was scoped in the original
client brief but has been explicitly marked not needed for this delivery.

## 8.1 Final Report

The full final report — project overview, architecture, real training results, real
deployment record, and categorized limitations, every claim cross-referenced to the
artifact backing it — is published at `docs/FINAL_REPORT.md`. It is not duplicated
here; this document indexes it and maps it against the client's requested structure.

| Client-requested content | Where it lives |
|---|---|
| Project overview | `docs/FINAL_REPORT.md` §1–2; `docs/LITERATURE_REVIEW_COMBINED.md` §2 |
| Dataset summary | `phase-2-data-collection.md`; `docs/FINAL_REPORT.md` §3 |
| Scientific pipeline / methodology | `phase-4-scientific-implementation.md`; `docs/FINAL_REPORT.md` §2 |
| Benchmark / training results | `phase-3-training-benchmarking.md`; `docs/FINAL_REPORT.md` §4 |
| Docking / ML / XAI / literature results | `phase-6-results-analysis.md`; `docs/FINAL_REPORT.md` §5 |
| Evaluation methodology | `phase-5-evaluation-validation.md` |
| Discussion and limitations | `phase-7-discussion-limitations.md`; `docs/FINAL_REPORT.md` §8 |
| Deployment record | `docs/DEPLOYMENT_VERIFICATION.md`; `docs/FINAL_REPORT.md` §6 |
| Future work | `phase-7-discussion-limitations.md` §7.3 |

## 8.2 Live Demonstration

The client's recommended demonstration flow, mapped to the actual live, deployed
application (`ayurvedic-drug-discovery.vercel.app`) rather than a hypothetical script
— every step below is a real page and a real backend call, not a mockup:

| Recommended step | Live application equivalent |
|---|---|
| Select Disease / Target | **Protein Shapes** page — 10 real curated targets, or type a compound code directly on **Run Analysis** |
| Retrieve Ayurvedic Compounds | **Compounds** page — real library, real search |
| Clean + Validate | Already performed (Phase 2); every listed compound is a real, verified record |
| Filter Candidates | **Shortlist** page — filter/sort a real ranked candidate list by target |
| Prepare Protein + Ligands | Happens automatically server-side (real RDKit ligand embedding, real RCSB protein fetch) when an analysis is run |
| Run Docking | **Run Analysis** page → real `POST /api/docking/run`, or the full pipeline via `POST /api/pipeline/run` |
| Analyze Interactions | Real `InteractionAnalysisAgent` output, shown in the Results page's **3D Shape** tab ("Where it seems to touch") |
| Run ML Prediction | Results page **Overview** tab — real trained-model `pKd` prediction |
| Generate SHAP Explanation | Results page **Why this result?** tab — real per-compound SHAP chart |
| Retrieve Scientific Literature | Results page **Research** tab — real Groq-LLM RAG synthesis with real citations |
| Agentic Validation | Runs automatically server-side on every pipeline call; a blocked-overclaim case has been observed live |
| Rank Candidates | **Shortlist** page |
| Show 3D Molecular Interaction | Results page **3D Shape** tab — real 3Dmol.js viewer, real ligand + protein geometry, 4 real render styles |
| Generate Final Report | `ReportAgent` produces a real JSON + Markdown report per pipeline run (`backend/app/data/reports/`) |

This flow has been exercised live, end-to-end, through the deployed frontend during
this project's development and verification (see `docs/DEPLOYMENT_VERIFICATION.md`
for the dated record) — it is a description of what the system actually does when
used, not an aspirational script.

## 8.3 Presentation deck

The client's phase plan (§47) specifies a 25-slide structure for a formal defense
presentation. **This has been explicitly marked not needed for this delivery** and
was not produced. If required later, `docs/FINAL_REPORT.md` and this set of eight
phase documents already contain real, verified content mapped to every one of the 25
requested slide topics (problem statement → literature review → research gap →
dataset → pipeline → results → limitations → conclusion), so building the deck would
be an act of formatting existing real content into slides, not new research.

---
*Previous: [Phase 7 — Discussion & Limitations](phase-7-discussion-limitations.md) · Index: [Phase Documentation Index](00-index.md)*
