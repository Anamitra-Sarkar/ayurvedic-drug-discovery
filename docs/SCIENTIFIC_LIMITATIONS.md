# Scientific Limitations

This document is updated at the end of every phase with what is honestly true
about the system at that point - not aspirational. See `docs/DATA_PROVENANCE.md`
and `docs/REPRODUCIBILITY.md` for the artifacts backing these statements.

## As of Phase A (agent pipeline wired and verified, no real training yet) — superseded, kept for history

1. ~~No trained binding-affinity model.~~ **Superseded — see "Current state" below.**
2. ~~Docking runs in mock mode.~~ **Superseded — Vina is deployed; see below.**
3. ~~Seed phytochemical data is a 100-record sample~~ **Superseded — the seed data
   integrity issue described in `docs/DATA_PROVENANCE.md` was found and fixed; the
   live dataset is 65 records, all real, none fabricated.**
4. ~~XAI (SHAP) explanations are unavailable~~ **Superseded — real SHAP explanations
   ship against the real trained model.**
5. RAG/literature grounding works against a 40-document corpus matching the
   client-provided literature review, not a broader live PubMed/Europe PMC
   index. **Still true** — this is a permanent scope decision, not a phase gap.
   Citation grounding and hallucination-detection are verified working
   correctly against this corpus live in production, including a live-observed
   case of the model correctly refusing to answer rather than hallucinating
   when the corpus had nothing on the queried compound.
6. No experimental validation of any kind has occurred for any compound/target
   pair this pipeline has considered. **Still true and permanent** — every
   output, at every tier, is a computational hypothesis only, consistent with
   the AYUSH-64 precedent this project is built around (see
   `docs/RESEARCH_GAP.md`).

## Current state (as of 2026-09-25, after Phases C/D/H + multiple live-testing rounds)

1. **A real binding-affinity model is trained and deployed.** RandomForest,
   trained on 127 real PDBBind complexes (181 total, 14 honestly excluded for
   real per-complex failures), held-out test MAE 1.35 / RMSE 1.59 / R² 0.01 /
   Pearson 0.30 / Spearman 0.31. **These numbers are genuinely modest and are
   reported as such, not smoothed over.** R² near zero means the model
   explains very little variance beyond the mean on unseen complexes at this
   training-set size; MAE (~1.35 pKd units, roughly half a log-unit of
   binding affinity) is the more informative number for ranking/triage use.
   A materially better model would need substantially more labeled real
   binding data — the honest limitation is data volume, not methodology (the
   same scaffold-split, leakage-checked, multi-model-compared protocol is
   standard practice in the literature reviewed in
   `docs/LITERATURE_REVIEW_COMBINED.md` Section 3.2.D). Every prediction is
   still tagged `ML_PREDICTION` tier with an applicability-domain check and an
   explicit disclaimer — the model existing and being real does not change
   the evidentiary-tier discipline.
2. **Docking is real where the Vina binary is available, and honestly falls
   back where it isn't — this is a live, observed, per-request condition, not
   a fixed phase state.** On the deployed HF Space (free CPU-only tier), Vina
   availability has been observed to vary; `DockingAgent` reports
   `execution.mock_used` truthfully on every response, and the empirical
   fallback scoring function is clearly labelled as such in the API response
   and never presented as a real Vina score. Real 3-D ligand geometry (RDKit
   ETKDG embedding + MMFF optimization) and real RCSB crystal protein
   structures are used for the 3-D viewer regardless of which docking path
   ran.
3. **Seed phytochemical library is 65 real, verified records** (down from an
   original 100 that included 80 fabricated placeholder entries and 20 more
   with fabricated plant-source associations — found and fixed; see
   `docs/DATA_PROVENANCE.md`'s integrity-finding entry). This remains a small
   sample relative to full IMPPAT (~9,600 phytochemicals); broader coverage
   would require either further manual curation or bulk access IMPPAT does
   not currently expose (also documented in `docs/DATA_PROVENANCE.md`).
4. **Real SHAP-based XAI explanations** run against the real trained model,
   confirmed live in the deployed UI with correctly rendered feature-
   attribution values and plain-language interpretation text.
5. RAG/literature grounding — unchanged from above, still a 40-document
   corpus by design.
6. No experimental validation — unchanged, permanent, by design.
7. **Bulk shortlist ranking (`/candidates/rank`) intentionally only computes
   the database and docking evidentiary tiers**, not ML/XAI/literature, for
   performance reasons (running a real ML+XAI+literature pass, including a
   real LLM call, for up to 11 candidates on every shortlist view would be
   too slow). The UI honestly shows "not computed for this shortlist" rather
   than a fabricated-looking result for the tiers that weren't run — the
   full single-compound Results view still runs and shows all five tiers for
   real.

## Hard constraint (unconditional, applies at every phase)

This system must never present a computational output as clinical proof, as
confirmed efficacy, or as a completed drug discovery. `ValidationAgent`
actively scans for and sanitizes overclaim language (verified firing on real
pipeline runs, e.g. blocking "clinical proof" phrasing). Every output carries
an explicit evidentiary tier (1-5) and a disclaimer. See
`backend/app/agents/evidence_tiers.py` and `backend/app/core/evidence/`.
