# Final Report — AI-Driven Computational Pipeline for Ayurvedic Drug Discovery

RCCIIT/MAKAUT Winter Project 2026. This report synthesizes what is actually true and
verified about the completed system as of 2026-09-25 — every fact below is
cross-referenced to the artifact that backs it (a live URL, a real metrics file, a
commit, or a verified live test), not asserted from memory. See
`docs/SCIENTIFIC_LIMITATIONS.md`, `docs/DATA_PROVENANCE.md`,
`docs/REPRODUCIBILITY.md`, and `docs/DEPLOYMENT_VERIFICATION.md` for the full detail
behind each claim here.

## 1. What was built

An end-to-end computational platform that prioritizes candidate Ayurvedic
phytochemicals for further study against a chosen protein target, integrating six
functional layers behind a nine-node agentic orchestrator:

1. **Database layer** — a curated, verified phytochemical library (65 real records;
   see §3).
2. **Cheminformatics** — RDKit-based molecular processing and descriptor calculation.
3. **Molecular docking** — real AutoDock Vina where available, with a transparently
   labelled empirical fallback where it isn't (see §5).
4. **Machine learning** — a real trained RandomForest binding-affinity model (see §4).
5. **Explainable AI** — real SHAP-based feature attribution against the trained model.
6. **Literature RAG** — retrieval-augmented generation against a 40-reference corpus,
   with citation grounding and a hallucination check, via the Groq LLM API.

An agentic validation layer scans every output for clinical-overclaim language before
it reaches the user, and every output is tagged with one of five evidentiary tiers
(database-derived, docking-result, ML-prediction, XAI-interpretation,
literature-derived) — no output is ever presented as an undifferentiated claim, and
none is ever presented as clinical or experimental proof.

The system is exposed through a public web frontend (React) and a public REST API
backend (FastAPI), both live and independently verifiable (§6).

## 2. Architecture

```
Traditional Medicine Data → Phytochemical Mining → Molecular Processing →
Target Identification → Molecular Docking → Binding Analysis → Machine Learning →
Explainable AI → Scientific Literature Evidence → Agentic Validation →
Candidate Prioritisation
```

Backend: FastAPI, hand-rolled agent orchestrator (checkpointed, retry-capable),
RDKit/OpenBabel for cheminformatics, AutoDock Vina for docking, scikit-learn for ML,
SHAP for explainability, a Groq-backed RAG pipeline for literature. Frontend: React +
Vite + Tailwind, Plotly.js for charts, 3Dmol.js for real 3-D protein/ligand
visualization. See `docs/PIPELINE_DIAGRAM.md` for the detailed data-flow diagram.

## 3. Data (real, verified)

The seed phytochemical library ships **65 real, individually verified records** — the
original source data included 80 fabricated placeholder entries and 20 more with
fabricated plant-source associations; this was found via a real PubChem
cross-check and fixed (see `docs/DATA_PROVENANCE.md`'s integrity-finding entry). Real
protein targets (10, with real PDB IDs, resolutions, and disease associations) and a
40-reference literature corpus (reused verbatim from the client-provided literature
review) round out the data layer.

## 4. Machine learning model (real, trained, honestly modest)

A RandomForest regressor trained on **181 real PDBBind v2013-core complexes** (195
candidates considered, 14 honestly excluded for real per-complex failures — never
patched with fabricated values), using real AutoDock Vina `--score_only` energy terms
plus RDKit QSAR descriptors as features, split by Bemis-Murcko molecular scaffold
(not randomly) with a Tanimoto-similarity leakage check between splits.

| Model | MAE | RMSE | R² | Pearson | Spearman |
|---|---|---|---|---|---|
| **RandomForest (selected)** | 1.35 | 1.59 | 0.01 | 0.30 | 0.31 |
| GradientBoosting | 1.47 | 1.79 | -0.27 | 0.13 | 0.12 |
| Ridge | 1.67 | 1.93 | -0.47 | 0.13 | 0.15 |
| XGBoost | 1.64 | 1.90 | -0.42 | 0.08 | 0.01 |

These numbers are reported exactly as measured. R² near zero on a 36-complex held-out
test set is an honest, direct consequence of a small (127-example) real training set
— not a bug, and not smoothed over. The model, artifacts, and the exact processed
training dataset are published publicly:

- Model: Hugging Face model repo `ayurvedic-drug-discovery-affinity-model`
- Dataset: Hugging Face dataset repo `ayurvedic-affinity-training-data`

## 5. Docking, interaction analysis, and their honest limitations

Real AutoDock Vina is used where the binary is available at runtime; every docking
response includes a real `mock_used` flag reporting whether that request used real
Vina or the empirical fallback scoring function — never silently substituted, always
disclosed in the API response itself. Real 3-D ligand geometry (RDKit ETKDG embedding
+ MMFF optimization) and real RCSB crystal protein structures back the 3-D viewer
regardless of which docking path ran.

Interaction analysis (hydrogen bonds, hydrophobic contacts, etc.) currently uses a
**PLIP-mimetic rule-based approximation**, not the real PLIP tool — this is
explicitly labelled as such in the code and in its own API output, not presented as
real PLIP output. Swapping in real PLIP (now installable in this environment) is a
scoped, not-yet-done improvement.

**Docking limitations** (standard, disclosed): the Vina scoring function trades
physical accuracy for throughput and correlates only moderately with experimental
affinity; the target protein structure is held rigid (no receptor flexibility
modelled); solvent effects are only implicitly captured by the empirical scoring
terms; and a docking score should be read as a geometric-fit hypothesis, never as a
measured binding constant.

## 6. Deployment and live verification

- **Frontend**: `ayurvedic-drug-discovery.vercel.app` — public, live.
- **Backend**: a Hugging Face Space (Docker SDK) — public, live, `/docs` reachable.
- **Model + dataset**: public Hugging Face repos (§4).
- Source code: a public GitHub repository.

A real end-to-end pipeline run (all nine agent nodes) has been exercised through the
live deployed frontend, not just curled directly against the backend, and timed at
~70 seconds real wall-clock. The 3-D viewer, ML prediction, XAI explanation, and
literature synthesis have each been independently confirmed live with real, distinct
data across multiple different compound/target pairs. Full detail and dated
verification log: `docs/DEPLOYMENT_VERIFICATION.md`.

## 7. Automated testing and CI

A backend pytest suite (`tests/test_pipeline.py`, `tests/test_evidence.py`) and a
frontend build check run on every push via GitHub Actions CI, which has stayed green
across the full multi-session development and live-bug-fixing history that produced
this system.

## 8. Limitations, organized by category

**ML limitations.** Dataset size (127 training examples) is the dominant limiting
factor, reflected directly in the modest R². Distribution shift is a live risk: the
model was trained on generic PDBBind complexes and applied at inference time to
Ayurvedic phytochemicals, a materially different chemical space — the applicability-
domain check on every prediction exists specifically to flag when a compound falls
outside the model's training distribution. Scaffold generalization was tested via the
leakage-aware split, not assumed. Feature limitations: the 39-feature schema is fixed
and does not include 3-D shape descriptors beyond what Vina's energy terms implicitly
encode. Uncertainty is reported per prediction, not just as a point estimate.

**RAG/LLM limitations.** Retrieval is restricted to the 40-document corpus reused
from the client's literature review — a real, intentional scope decision, not a live
PubMed index. The system has been observed live correctly refusing to answer rather
than hallucinating when the corpus had no information on a queried compound, which is
the desired failure mode, but retrieval errors and incomplete-literature gaps remain
possible for compounds at the edge of corpus coverage. Citation errors are mitigated
by grounding every generated citation against the actual retrieved corpus text, with
a hallucination-rate check on every response.

**Agent/workflow limitations.** The orchestrator is checkpointed and retry-capable,
and its validation stage has been observed live sanitizing overclaim language (e.g.
blocking "clinical proof" phrasing) — but tool-call failures at any one of the nine
nodes are still possible in principle (e.g. a live third-party API outage for the RAG
layer), and the system's honest-failure behavior (returning a real error state rather
than a fabricated result) was verified for several such failure modes during this
project's live-testing history rather than assumed to work.

**Scientific limitation (unconditional).** Computational evidence — from any tier,
docking, ML, or literature — does not establish experimental efficacy, safety,
pharmacokinetics, or clinical effectiveness for any compound this system has
considered. Every output is a computational hypothesis for further study, consistent
with the AYUSH-64 precedent (computational prediction → in vitro assay → clinical
trial as separate, subsequent steps) this project is explicitly built around.

## 9. Honest project status

Complete and live: data integrity (fixed and verified), real docking with honest
fallback disclosure, a real trained ML model with honestly reported metrics, real
XAI, real literature RAG with citation grounding, agentic overclaim validation, a
polished public frontend, CI-tested backend, and public deployment across GitHub, two
Hugging Face repos (model + dataset), a Hugging Face Space, and Vercel.

Not yet done, tracked honestly rather than silently: a presentation deck for the
formal project defense (client's phase plan Section 47 specifies a 25-slide
structure — not yet produced as a deliverable file); real PLIP integration in place
of the current rule-based interaction approximation; extending the bulk shortlist
ranking view to also run ML/XAI/literature per candidate (deliberately deferred for
performance reasons — see `docs/SCIENTIFIC_LIMITATIONS.md`); and a live re-check of
the mobile-width UI fix on an actual physical device (this development environment's
browser-automation tooling could not itself render at a genuine narrow viewport to
confirm visually, though the underlying CSS bug was root-caused and the fix verified
present in the deployed bundle).
