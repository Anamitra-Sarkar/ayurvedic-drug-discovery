# Phase 4 — Full Scientific Implementation

**Status: Complete and live**, with two honestly-scoped gaps (§4.5, §4.9).

Only after Phase 1 (research design) and Phase 3 (benchmarking) established the
scientific approach was the complete application implemented.

## 4.0 Scientific Pipeline

Nine agent nodes, orchestrated by a hand-rolled, checkpointed state-machine
orchestrator (`backend/app/agents/orchestrator.py`):

```
Database → Cheminformatics → Docking → Interaction (parallel with ML) → ML →
XAI → Literature → Validation → Report
```

## 4.1 Cheminformatics Pipeline

`CheminformaticsAgent` / `backend/app/core/ml/features.py`. Real RDKit-based
molecular processing: SMILES parsing and validation, 3-D conformer generation
(ETKDG embedding + MMFF force-field optimization — confirmed live producing real,
distinct 3-D geometry per compound, not a placeholder), Lipinski/Veber/QED
drug-likeness filtering, and the 18-descriptor QSAR feature set used by the ML
layer (Phase 3).

## 4.2 Protein Pipeline

`DockingAgent.prepare_protein()`. Resolves a target PDB ID to a real structure: first
checks for a CI-cached local copy (`data/raw/pdb/`), then falls back to a live RCSB
fetch (`files.rcsb.org`), and only uses an honestly-labelled minimal mock structure
as a last resort if both real sources are genuinely unavailable — never silently.
Confirmed live: real crystal structures (e.g. the COVID-19 main protease, PDB 6LU7,
239KB of real PDB records) are fetched and used.

## 4.3 Ligand Pipeline

`DockingAgent.prepare_ligand()`. SMILES → RDKit `Mol` → 3-D embedding (ETKDG) → MMFF
optimization → PDB → PDBQT (via OpenBabel). Confirmed live producing real 3-D ligand
geometry (e.g. a real 6.6KB PDB structure with explicit hydrogens for Withaferin A) —
this is what powers the 3-D viewer's real ligand rendering.

## 4.4 Molecular Docking

`DockingAgent.run_docking()`, `backend/app/core/docking/vina_wrapper.py`. Real
AutoDock Vina (v1.2.7) where the binary is available at runtime, invoked via
subprocess with the prepared ligand/receptor PDBQT files. Every response includes an
honest `execution.mock_used` flag; when Vina genuinely isn't available, an empirical,
physics-inspired scoring heuristic is used instead and clearly labelled as such in
the same response field — never silently substituted for a real score. An optional
ML-based rescoring layer (a small RandomForest rescorer trained separately) refines
the raw score when enabled.

## 4.5 Interaction Analysis

`InteractionAnalysisAgent`, `backend/app/core/docking/interactions.py`. A rule-based
detector implementing PLIP-style geometric thresholds (hydrogen bonds 2.0–4.1Å,
hydrophobic contacts <4.0Å, π-stacking 3.0–5.5Å, salt bridges, water bridges, halogen
bonds — thresholds sourced from Adasme et al., NAR 2021, the real PLIP publication).
**Honest gap**: this is a **PLIP-mimetic rule-based approximation**, not the real
PLIP tool — explicitly self-labelled as such in its own API output
(`evaluation.method: "PLIP-mimetic rule-based"`), not presented as real PLIP.
Real PLIP is installable in this environment but has not yet been substituted in.
As of this phase, the agent is wired into both the full 9-node pipeline and the
single-compound docking endpoint used by the Results page, so its output — real
type/residue/distance/strength records, generated from real docking-derived ligand
features — is visible end-to-end in the live application.

## 4.6 Machine Learning

`MLAgent`, `backend/app/agents/ml_agent.py`. Loads the real trained RandomForest
(Phase 3) and produces `pKd` predictions with an applicability-domain check (is this
compound similar enough to the training distribution for the prediction to be
trustworthy) and an uncertainty estimate. See `phase-3-training-benchmarking.md` for
training detail and honest metrics.

## 4.7 Explainable AI

`XAIAgent`, wired to the real trained `MLAgent` model (not a standalone/untrained
explainer). Real SHAP-based feature attribution, with a textual plain-language
interpretation of which chemical features pushed a prediction up or down. Confirmed
live producing real, per-compound-distinct SHAP values.

## 4.8 Literature Retrieval + RAG

`LiteratureAgent`, `backend/app/core/rag/`. TF-IDF retrieval over the 40-reference
corpus, reranking, and generation via the Groq LLM API (OpenAI-compatible endpoint,
model `openai/gpt-oss-120b`) with citation grounding — every generated citation is
checked against the actually-retrieved corpus text, and a hallucination-rate is
computed per response. Confirmed live: the system correctly refuses to answer
("the provided literature does not contain any information on...") rather than
hallucinate, when the corpus genuinely has nothing on a queried compound.

## 4.9 Agentic AI Workflow

`AyurvedicDiscoveryOrchestrator` — a hand-rolled, checkpointed state-machine (not the
`langgraph` library itself, despite early drafts of this project referencing that
framework by name; an equivalent state-graph pattern was implemented directly).
Supports parallel node execution (interaction analysis runs alongside ML), retry on
transient node failure, and per-node checkpointing to disk. A separate
`ValidationAgent` node runs after all data-producing nodes and actively scans every
output for clinical-overclaim language — confirmed live blocking "clinical proof"
phrasing during a real pipeline run — before a `ReportAgent` node produces the final
JSON + Markdown ranking report.

## 4.10 Candidate Ranking

`GET /api/candidates/rank` (`backend/app/api/docking.py`). Batch-docks a curated
library of real candidate compounds against a chosen target and ranks by docking
affinity. **Honest scope decision**: this bulk endpoint deliberately only computes
the database and docking evidentiary tiers per candidate (not ML/XAI/literature —
running a real ML+XAI+literature pass, including a real LLM call, for up to 11
candidates on every shortlist view would be too slow). The frontend honestly labels
the tiers that weren't run as "not computed for this shortlist" rather than showing
a fabricated-looking result — the full single-compound Results view still runs and
shows all five tiers for real.

## 4.11 Frontend

React + Vite + Tailwind, 9 pages (Landing, Compounds, Compound Detail, Protein
Shapes, Run Analysis, Results, Shortlist, Plant Map, Documentation), using
Plotly.js for the SHAP feature-attribution chart and 3Dmol.js for real 3-D
protein/ligand visualization (four interchangeable render styles — sticks, balls,
lines, ribbons — all confirmed live changing what's actually rendered, both for the
protein and the ligand). Written in deliberately plain, jargon-free language
throughout per the client's requirement, with every result carrying a visible
evidentiary-tier badge and a "research preview, not medical advice" disclaimer.

## Backend

FastAPI (`backend/app/main.py`), with route modules for database, docking, ML,
literature, and pipeline endpoints (`backend/app/api/`), each calling the real
agents above directly — verified, over the course of this project's live-testing
history, to be free of the "endpoint calls a method that doesn't exist and silently
falls back to fabricated data" bug pattern that was found and fixed in five separate
locations during development (see `PROJECT_STATUS.md`'s session log for the full
history of that specific bug class).

---
*Previous: [Phase 3 — Training & Benchmarking](phase-3-training-benchmarking.md) · Next: [Phase 5 — Evaluation & Validation](phase-5-evaluation-validation.md)*
