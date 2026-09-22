# Scientific Limitations

This document is updated at the end of every phase with what is honestly true
about the system at that point - not aspirational. See `docs/DATA_PROVENANCE.md`
and `docs/REPRODUCIBILITY.md` for the artifacts backing these statements.

## As of Phase A (agent pipeline wired and verified, no real training yet)

1. **No trained binding-affinity model.** `MLAgent` has no model in
   `backend/app/models/trained/`; every ML prediction request honestly returns
   `status: model_not_trained` rather than a fabricated number. This is the
   most significant limitation until Phase D (real Kaggle training on real
   binding-affinity data) is complete.
2. **Docking runs in mock mode.** AutoDock Vina is not installed in the current
   environment; `DockingAgent` transparently reports `mock_fallback: True` and
   uses an empirical, physics-inspired scoring heuristic instead of real
   docking. Scores from this path must not be interpreted as real docking
   results. Real Vina installation and verification is Phase C.
3. **Seed phytochemical data is a 100-record sample**, not the full IMPPAT
   database (~9,600 phytochemicals). Results are only as broad as this sample
   until Phase B's full-scale data acquisition.
4. **XAI (SHAP) explanations are unavailable** while there is no trained model
   to explain - `XAIAgent.run_node` honestly reports
   `status: no_trained_model`.
5. **RAG/literature grounding works against a 40-document corpus** matching the
   client-provided literature review, not a broader live PubMed/Europe PMC
   index. Citation grounding and hallucination-detection were verified working
   correctly against this corpus, but its scope is limited.
6. **No experimental validation of any kind has occurred** for any
   compound/target pair this pipeline has considered. Every output, at every
   tier, is a computational hypothesis only - consistent with the AYUSH-64
   precedent this project is built around (see `docs/RESEARCH_GAP.md`).

## Hard constraint (unconditional, applies at every phase)

This system must never present a computational output as clinical proof, as
confirmed efficacy, or as a completed drug discovery. `ValidationAgent`
actively scans for and sanitizes overclaim language (verified firing on real
pipeline runs, e.g. blocking "clinical proof" phrasing). Every output carries
an explicit evidentiary tier (1-5) and a disclaimer. See
`backend/app/agents/evidence_tiers.py` and `backend/app/core/evidence/`.
