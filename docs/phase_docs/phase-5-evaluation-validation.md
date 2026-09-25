# Phase 5 — Evaluation Metrics & Validation

**Status: Complete.** Planned and executed independently from implementation, per
the client's requirement.

## 5.1 ML Metrics

Regression task (binding-affinity, `pKd`) — all five required metrics computed on
the held-out test set: MAE, RMSE, R², Pearson correlation, Spearman correlation.
Classification metrics were not introduced, since the deployed task is regression
only — using only metrics appropriate to the actual prediction task, per the
client's instruction. Full real results: `phase-3-training-benchmarking.md` §3.4.

## 5.2 Docking Evaluation

- **Docking score**: real AutoDock Vina energy, or an honestly-labelled empirical
  fallback (never presented as a real Vina score when it isn't one).
- **Pose consistency**: multiple poses (up to 5 per run) are returned with mode
  number, affinity, and RMSD bounds, letting a reviewer see how much the top poses
  agree or disagree — confirmed live returning real, distinct RMSD values per pose.
- **Interaction quality**: real hydrogen-bond/hydrophobic/contact counts from the
  interaction-analysis layer (Phase 4 §4.5).
- **Reproducibility**: the docking pipeline is deterministic given the same
  ligand/target/Vina-availability state; the empirical fallback path documents its
  own scoring formula in the response (`scoring_breakdown`).
- **Recognized validation strategy**: the training-time feature pipeline was
  benchmarked against real PDBBind data (Phase 3), which is the standard recognized
  docking-scoring validation set used throughout the literature reviewed in
  `docs/LITERATURE_REVIEW_COMBINED.md` §3.2.C — rather than relying on raw docking
  scores alone as a validation signal.

## 5.3 Literature/RAG Evaluation

- **Retrieval relevance**: TF-IDF retrieval with reranking; per-query retrieval
  scores are returned and inspectable in the API response.
- **Evidence coverage / citation correctness / groundedness**: every citation the
  LLM generates is checked against the actually-retrieved corpus text before being
  returned — confirmed live rejecting ungrounded citations.
- **Hallucination rate**: computed per response (`hallucination_rate` field); a real
  live observation during this project's testing showed the system scoring 0.0 and
  correctly refusing to answer rather than fabricate a response, when the corpus
  genuinely had nothing on a queried compound (Gallic acid was queried against a
  corpus that only discusses IMPPAT-database-level facts, not that specific
  compound — the model said so plainly instead of hallucinating).
- **Answer faithfulness**: reported as `faithfulness = 1 − hallucination_rate` in
  the frontend, sourced from the same real per-response metric.

## 5.4 Agent Evaluation

- **Task completion rate**: the full 9-node pipeline has been run live multiple
  times through the deployed frontend and reached `completed` status with zero
  failed nodes each time (confirmed via live HF Space logs during this project's
  development).
- **Tool-call correctness**: the specific "API route calls a nonexistent agent
  method and silently falls back to fabricated data" bug pattern was found and
  fixed in five separate locations during this project's development (literature,
  docking, ML predict, ML explain, pipeline run) — each found only by exercising the
  live endpoint and reading real logs, not by static review alone. All five are
  fixed and re-verified live.
- **Workflow success / failure recovery**: the orchestrator supports per-node retry
  and checkpointing; a real timeout bug (the frontend's request timeout was shorter
  than the real ~70-second full-pipeline runtime, causing every real analysis to
  abort) was found via live timing and fixed by raising the timeout for that
  specific call — confirmed live afterward completing successfully.
- **Validation accuracy**: `ValidationAgent`'s overclaim-blocking has been confirmed
  live firing on real pipeline output (sanitizing "clinical proof"-type phrasing).
- **Reproducibility**: every agent's output is deterministic given the same real
  inputs and the same Vina/LLM-availability state at request time.

## 5.5 End-to-End Scientific Validation

```
ML Prediction
      ↕
Docking
      ↕
Protein-Ligand Interactions
      ↕
Published Literature
```

For any given compound/target pair, the system's four evidentiary layers (excluding
the database layer, which is definitional rather than a claim) can be read together
and classified as:

- **Strongly supported** — docking and ML predictions agree in direction, real
  interaction contacts are present at expected binding-site residues, and the
  literature layer retrieves genuinely relevant, grounded citations.
- **Partially supported** — some layers agree, others are silent (e.g. literature
  has no coverage of the specific compound, as observed live for several test
  compounds against the 40-reference corpus).
- **Computationally predicted only** — docking/ML/XAI produce a result with no
  literature corroboration; the default state for most compounds given the
  corpus's necessarily limited 40-reference scope.
- **Conflicting evidence** — docking and ML disagree materially, or literature
  contradicts a computational prediction; the system does not currently
  auto-flag this classification, it is a manual read of the four layers'
  independent output (a scoped future-work item, see
  `phase-7-discussion-limitations.md`).
- **Insufficient evidence** — one or more layers fail (e.g. Vina genuinely
  unavailable and the empirical fallback used) or return a `not_computed` state.

This classification framework is applied qualitatively in
`phase-6-results-analysis.md` against real example output rather than automated
into a single composite score — consistent with the project's hard constraint that
no two evidentiary tiers may be collapsed into one undifferentiated claim.

---
*Previous: [Phase 4 — Scientific Implementation](phase-4-scientific-implementation.md) · Next: [Phase 6 — Results & Analysis](phase-6-results-analysis.md)*
