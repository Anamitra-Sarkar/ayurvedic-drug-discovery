# Phase 7 — Discussion, Limitations & Future Work

**Status: Complete.**

## 7.1 Discussion

**Why the Phase 6 example candidates ranked as they did.** Glycyrrhizin ranking
above Asiaticoside and Bacoside A3 for GABRA1 reflects the docking layer's empirical
scoring of ligand size, hydrophobic contact potential, and hydrogen-bonding capacity
against this detector's generic GABA-A-family binding-site residue set (Phase 4
§4.5) — a real, computed difference between three real molecules, not an arbitrary
default order. It should be read as exactly what it is: a geometric-fit ranking
hypothesis, not a claim about actual receptor binding.

**Agreement between docking and ML.** For the Withaferin A / 6LU7 example in Phase
6, a moderate docking affinity coincided with an "active" ML classification — the
two independent evidentiary tiers point the same general direction here, which is a
mildly encouraging (not confirmatory) signal. The project's hard rule against
collapsing tiers into a single score means this agreement is reported as two
separate data points for a human reviewer to weigh, not auto-combined into a
composite "confidence".

**Literature support.** Coverage is real but necessarily narrow (a 40-reference
corpus, not a live literature index) — most individual compound/target pairs this
system considers will have no specific literature hit, and the system says so
honestly rather than manufacturing a citation. This is a deliberate, disclosed
scope choice, not a defect.

**Important molecular features.** Across the SHAP outputs observed live during this
project's testing, molecular weight and topological complexity (Bertz index)
recurred as dominant features across multiple different compounds, alongside the
real Vina/docking-derived terms — broadly consistent with the QSAR literature
reviewed in Phase 1 (`docs/LITERATURE_REVIEW_COMBINED.md` §3.2.D), where classical
physicochemical descriptors remain competitive predictors at small training-set
sizes.

**Unexpected findings.** The most scientifically important "finding" of this project
was not about any single compound — it was the repeated discovery, during
development, that naive code review was insufficient to catch a specific recurring
bug class (an API route calling a nonexistent agent method, silently falling back to
a fabricated result) — found five separate times, only by actually exercising live
endpoints and reading live logs. This shaped the project's own verification
methodology (see `phase-5-evaluation-validation.md` §5.4) as much as any chemistry result did, and is
reported here as a genuine methodological finding about building evidentiary-tiered
scientific software, not a footnote.

## 7.2 Limitations

### Dataset limitations

- The application's phytochemical seed library (65 real compounds, 41 plants) is a
  small fraction of full IMPPAT (~9,600 phytochemicals). No public bulk-download API
  was found for IMPPAT (researched directly, not assumed) — see `phase-2-data-collection.md` §2.6.
- Database coverage bias: the seed library concentrates on three named formulation
  contexts (Triphala, AYUSH-64, anti-epileptic herbs) rather than sampling IMPPAT's
  full breadth evenly.
- Metadata inconsistencies: 5 of 65 compounds still lack a PubChem-verified CID/SMILES
  pending further enrichment (honestly reported as pending, not filled with a guess).

### Docking limitations

- **Scoring-function limitations**: AutoDock Vina's scoring function trades physical
  accuracy for throughput; it correlates only moderately with experimentally
  measured binding affinity (a limitation inherent to the tool itself, not this
  project's use of it — documented directly in the literature reviewed, Phase 1
  §3.2.C).
- **Protein flexibility**: the receptor is treated as rigid; no induced-fit or
  side-chain flexibility is modelled.
- **Solvent effects**: only implicitly captured through the empirical scoring
  terms, not explicitly modelled (no explicit water molecules, no solvation free
  energy calculation beyond Vina's own desolvation term).
- **Conformational limitations**: a fixed exhaustiveness setting (8, reduced from
  Vina's default 16 to stay responsive on the CPU-only hosting tier) means the
  conformational search is real but not exhaustive.
- **Docking score interpretation**: a docking score is a geometric-fit hypothesis
  about pose plausibility, never a measured binding constant — restated here because
  it is the single most important thing for a reader of this report to internalize.
- **Interaction analysis is rule-based, not real PLIP** — the most significant
  disclosed gap in this layer (Phase 4 §4.5).

### ML limitations

- **Dataset size**: 127 real training examples is genuinely small; this is the
  dominant limiting factor behind the honestly modest R² (0.01) reported in Phase 3.
- **Distribution shift**: the model was trained on generic PDBBind complexes and is
  applied at inference time to Ayurvedic phytochemicals — a materially different
  chemical space. The applicability-domain check exists specifically to flag this,
  though its current implementation is itself limited (Phase 6 §6.4 — "no training
  data stored" for a full nearest-neighbour check).
- **Scaffold generalization**: tested via the leakage-aware scaffold split (Phase 3
  §3.2/§3.5), not assumed to generalize.
- **Feature limitations**: the fixed 39-feature schema does not capture 3-D shape
  information beyond what Vina's energy terms implicitly encode.
- **Uncertainty**: reported per-prediction (not just a point estimate), but the
  uncertainty estimate itself has not been independently calibration-checked against
  held-out data.

### RAG/LLM limitations

- **Retrieval errors / incomplete literature**: restricted to the 40-document
  corpus — a real, permanent scope decision, not a live PubMed index.
- **Hallucinations**: mitigated, not eliminated, by citation grounding and a
  per-response hallucination-rate check; the system has been observed live
  correctly refusing to answer rather than hallucinate, which is the desired
  behavior, but this was verified for the specific compounds tested during this
  project, not exhaustively for every possible query.
- **Citation errors**: grounding checks every generated citation against the
  retrieved corpus text, but cannot detect a citation that is technically present in
  the corpus yet misapplied to a claim it doesn't actually support.

### Agent limitations

- **Tool-call failures**: possible at any of the nine nodes (e.g. a third-party LLM
  API outage would affect the literature node); the orchestrator's retry/checkpoint
  design mitigates transient failures but cannot guarantee against a sustained
  external outage.
- **Workflow errors**: the specific "wrong method name → silent fabricated fallback"
  bug class was found and fixed in five locations (§7.1 above) — a real,
  now-resolved instance of exactly the risk this evaluation category is meant to
  catch.
- **Incorrect intermediate decisions**: not independently audited node-by-node
  beyond the live-testing already performed; a formal per-node unit-test suite
  beyond the current `tests/test_pipeline.py`/`tests/test_evidence.py` would
  strengthen this further (see Future Work).
- **Need for deterministic validation**: `ValidationAgent`'s overclaim-blocking is
  pattern-based (regex/keyword matching on forbidden phrasing), which is
  deterministic and has been confirmed live catching real overclaim text, but is not
  a semantic understanding of clinical-claim intent — a sufficiently creatively
  phrased overclaim could theoretically evade it (not observed in practice, but not
  formally proven impossible either).

### Scientific limitation (unconditional, applies at every phase)

Computational evidence — from any tier, docking, ML, XAI, or literature — does not
establish experimental efficacy, safety, pharmacokinetics, or clinical
effectiveness for any compound this system has considered.

## 7.3 Future Work

- Replace the rule-based interaction-analysis approximation with real PLIP
  (installable in this environment; not yet substituted in — see Phase 4 §4.5).
- Extend the bulk shortlist ranking endpoint to optionally run real ML/XAI/
  literature per candidate for a smaller candidate count, rather than deliberately
  omitting those tiers for performance (Phase 4 §4.10).
- Expand the phytochemical seed library beyond 65 records via further manual
  curation or, if IMPPAT ever exposes bulk access, direct integration.
- Implement a proper nearest-neighbour applicability-domain check against the
  stored training feature matrix, replacing the current honest-but-limited
  placeholder.
- Calibrate the ML model's per-prediction uncertainty estimate against held-out
  data.
- Add automated conflicting-evidence detection across the four evidentiary layers
  (Phase 5 §5.5's classification framework is currently applied qualitatively by a
  human reader, not automatically flagged).
- Grow the literature corpus beyond 40 references, or add a live PubMed/Europe PMC
  query path as a clearly-separated, differently-tiered evidence source.
- A live mobile-device re-check of this project's most recent CSS fixes (this
  development environment's own browser-automation tooling could not itself render
  at a genuine narrow viewport to confirm visually — see `docs/DEPLOYMENT_VERIFICATION.md`).

---
*Previous: [Phase 6 — Results & Analysis](phase-6-results-analysis.md) · Next: [Phase 8 — Final Report](phase-8-final-report.md)*
