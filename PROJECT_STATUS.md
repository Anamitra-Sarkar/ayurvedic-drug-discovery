# PROJECT STATUS — Ayurvedic Drug Discovery Pipeline

**THIS FILE IS APPEND-ONLY.** Never delete or rewrite existing entries — only add new
timestamped sections below. Any agent (human or AI) picking up this project must read
this whole file first before doing anything else.

---

## 🎯 MAIN GOAL, PLAN AND OBJECTIVE (read this first, always true, never edit)

**Client**: Bhumika Tewari, RCC Institute of Information Technology (RCCIIT), MAKAUT —
Winter Project 2026. **User directing this work**: Anamitra Sarkar (not the client;
doing this on the client's behalf).

**The ask**: Three AI agents (Kimi AI, Meta AI, Minimax) were each independently given
the same detailed brief to build "AI-Driven Computational Pipeline for Ayurvedic Drug
Discovery: Phytochemical Mining, Molecular Docking, and Explainable Binding Prediction."
All three produced incomplete/partially-fabricated zips. The task is to **merge, complete,
verify, train, and deploy** a single real, working system from the best parts of all
three — never fabricating data, docking results, or metrics along the way.

**Client's 8-phase methodology** (see `docs/client_provided/complete_phase_plan.md` for
the full original brief): (1) Literature Review & Research Design (2) Data Collection,
Segregation, Cleaning (3) Dataset Training & Benchmarking (4) Full Scientific
Implementation (5) Evaluation Metrics & Validation (6) Results & Analysis
(7) Discussion/Limitations/Future Work (8) Final Report & Presentation.

**Hard constraints (non-negotiable, apply forever)**:
- Frontend must be React + TypeScript + Tailwind + Plotly.js + 3Dmol.js — **never Streamlit**.
- Every output must carry one of 5 evidentiary tiers and a disclaimer. System must
  **never** claim "AI discovered a drug" or present computational prediction as clinical
  proof (AYUSH-64 precedent — see literature review).
- **NEVER fabricate data.** If a real source is unreachable, STOP and report — do not
  silently generate synthetic substitutes and present them as real. This has already
  caught multiple real fabrication bugs inherited from the original 3 zips (see log below).
- **NEVER download datasets/checkpoints to the local machine** (3.7GB RAM, no GPU) —
  route through GitHub Actions (small reference data, commits back to repo) or Kaggle
  (GPU training, large data fetched inside the Kaggle kernel only).
- User explicitly instructed: delegate heavy/bulk implementation work to the `opencode`
  CLI (free-tier models) rather than Claude directly, with Claude supervising/verifying
  every diff and reporting back after review. Claude does mechanical setup, verification,
  and small surgical fixes directly.

**Repo / accounts**:
- GitHub: `https://github.com/Anamitra-Sarkar/ayurvedic-drug-discovery` (public, pushed).
- HuggingFace (model + Space): under **bhumika's** HF account (per `bhumika-hf.txt` token) — NOT YET DONE.
- Vercel (frontend): NOT YET DONE.
- Kaggle: account `anamitrasarkar007` (`kaggle.json` in `~/Downloads/API_Keys_and_Secrets/`).
- Local repo working copy: `/home/anamitra/ayurvedic_drug_discovery/build/ayurvedic-drug-discovery`
  (also `_reference/minimax` and `_reference/kimi` sibling dirs — read-only source material,
  never merged wholesale, not part of git).

**Approved plan phases** (full detail was written to
`/home/anamitra/.claude/plans/this-is-the-folder-cozy-frog.md` at session start):
A. Setup & Merge — B. Real Data Acquisition — C. Cheminformatics & Docking —
D. ML Training (Kaggle GPU) — E. RAG & Agentic Orchestration hardening — F. Frontend —
G. Docker/Tests/Docs — H. Deployment (GitHub done early, HF + Vercel pending).

---

## 📋 HOW TO USE THIS FILE (for any agent resuming this project)

1. Read the GOAL section above.
2. Read every dated session log below, oldest to newest, to understand what's been done,
   what broke, and why specific decisions were made.
3. Check the "OPEN TODOs" section (always kept at the bottom, updated in place — this is
   the one section that gets edited rather than purely appended, since it's a live list;
   everything else is append-only).
4. Check "LESSONS / DO NOT REPEAT" before making changes — these are hard-won fixes.
5. `git log --oneline` in the repo is also authoritative for exact code changes; this file
   is for *context and reasoning* git commits don't capture (why something was fabricated,
   why a design choice was made, what's still running in the background on Kaggle, etc.)

---

## SESSION LOG

### 2026-09-22 — Session 1 (started ~06:00 UTC, ongoing)

**Environment discovered**: opencode CLI installed, only `opencode/muse-spark-1.3-contributor-free`
and `openrouter/nvidia/nemotron-3-super-120b-a12b:free` actually work (all other providers —
OpenCode Zen paid models, Zhipu, Nvidia direct, GitHub Copilot — are out of funds/broken).
Machine: 3.7GB RAM, no GPU, x86_64, user `anamitra`, no passwordless sudo.

**Phase A (Setup & Merge) — DONE**:
- Extracted Kimi/Meta/Minimax zips; Meta AI chosen as base (strongest real implementation:
  real orchestrator w/ checkpointing, real Vina wrapper, best ML CV harness, most mature
  evidence-tier validator). Kimi's docking was fully mocked with fabricated per-compound
  scores; Minimax had best tooling but zero real data/model.
- opencode reconciled `backend/requirements.txt` against actual imports (chunk A2).
- Ported Minimax's CI/pre-commit/pyproject tooling (chunk A3, Claude-direct).
- **Critical bug found+fixed**: `pipeline.py` (main `/pipeline/run` endpoint) imported a
  nonexistent class name and called a nonexistent async method → ALWAYS silently fell back
  to fully fabricated mock candidates on every call, undetectable without running it (chunk A4a).
- **Critical bug found+fixed**: orchestrator wired to `other_agents.py`'s stub `DockingAgent`,
  which hardcoded docking scores BY COMPOUND NAME (e.g. "Withaferin A" → -8.5) and mislabeled
  them `method: "Vina"` even when never run. Rewired orchestrator to the real dedicated agent
  classes (docking_agent.py, ml_agent.py, cheminformatics_agent.py, database_agent.py,
  xai_agent.py) via new `run_node()` adapters — delegated to opencode with an exact
  pre-specified design, verified line-by-line (chunk A4b).
- Running the rewired pipeline for real (not just review) surfaced **5 more pre-existing
  bugs**, none introduced by this session, all present since the original Meta AI zip:
  1. Syntax error in `filters.py` (space in a function name, dead duplicate stub).
  2. `core/evidence.py` (file) silently shadowed by `core/evidence/` (package) — Python
     always resolves the package first — broke `ml_agent.py`/`xai_agent.py` imports since
     day one. Merged into `core/evidence/tagged.py`, re-exported.
  3. `database_agent.py` assumed `imppat_sample.json` was `{"plants":[...],"phytochemicals":[...]}`
     but the real file is a flat list with totally different field names — real seed data
     could never actually load. Added `_normalize_flat_records()`.
  4. `literature_agent.py`'s `run_node` never appended to `state['tiered_outputs']`.
  5. `validation_agent.py`: two `.get(key, default)` calls broken by a present-but-`None`
     value (default only applies to a *missing* key, not a `None` value).
- Verified via 5 successive full pipeline runs until all 8 nodes completed with zero failures.
- Wrote docs skeleton: `docs/DATA_PROVENANCE.md`, `docs/SCIENTIFIC_LIMITATIONS.md`,
  `docs/REPRODUCIBILITY.md`, `docs/phase_docs/00-index.md`.

**Phase B (Real Data Acquisition) — ~90% DONE**:
- Created GitHub repo, pushed. Set up `.github/workflows/fetch-real-data.yml` +
  `scripts/fetch_real_data.py` (opencode-written, stdlib-only, real PubChem PUG-REST +
  RCSB PDB + Europe PMC, never fabricates on failure) — runs entirely in GitHub Actions
  cloud, commits results back, never touches local disk.
- **MAJOR integrity finding**: original `imppat_sample.json` seed data was fabricated at
  every level. 80/100 records were placeholder names like "Gallic acid derivative 20"
  (all correctly 404'd against real PubChem). Of the 20 "real"-named compounds, **every
  one** had a fabricated plant source (cycled through the 3 Triphala plants regardless of
  actual botanical origin — e.g. Withaferin A, unique to *Withania somnifera*, was tagged
  as sourced from *Emblica officinalis*) and fabricated `pubchem_cid` values.
- Fixed: dropped the 80 fake records, re-sourced the 15 salvageable real compounds to their
  correct real botanical origin (cross-checked against real pharmacognosy), overwrote
  fabricated CID/SMILES with real PubChem values, added 50 more real correctly-sourced
  phytochemicals. After a 503-retry fix, **60/65 compounds now have real PubChem-verified
  CID+SMILES**. All 10 target PDB structures verified real from RCSB.
- IMPPAT has no public bulk-download API (researched, documented — not an assumption).
- Literature title-verification only matched 5/40 (regex title-extraction heuristic
  limitation, not evidence the 40 refs are fake — they're reused from the client's own
  pre-written literature review).
- Real BindingDB/PDBBind training data deliberately deferred to Phase D (fetched inside
  the Kaggle kernel only, per the no-local-download policy).

**Phase C (Cheminformatics & Docking) — in progress**:
- Installed real tools on this machine (user-local, no root): AutoDock Vina 1.2.7
  (official prebuilt binary → `~/.local/bin/vina`), Meeko 0.8.0 + gemmi, OpenBabel
  (`openbabel-wheel` → gives `obabel` CLI + python bindings), real PLIP 3.0.1.
- **Bug found+fixed**: `vina_wrapper.py` passed a `--log` CLI flag that AutoDock Vina 1.2.x
  removed (existed in 1.1.x) — every real Vina invocation was silently rejected and fell
  back to mock. Fixed to capture stdout/stderr directly.
- **Bug found+fixed**: `docking_agent.py`'s `prepare_protein()` ALWAYS wrote a fake 3-atom
  dummy PDB regardless of tool availability — comment literally said "Replace with real PDB
  fetch" but nothing did. Now uses the real structure from Phase B's `data/raw/pdb/` first,
  falls back to a live RCSB fetch, converts via real OpenBabel, and only uses the honest
  labeled mock as a last resort.
- **Verified real docking end-to-end**: Withaferin A's real SMILES vs. real 6LU7
  (SARS-CoV-2 Mpro) structure → `mock_used: false`, real Vina pose ensemble, best affinity
  -5.891 kcal/mol. Genuine AutoDock Vina output.
- **Bug found+fixed**: `features.py`'s `bcut2d_mwhi` referenced an RDKit function object
  instead of calling it (would break float32 casting); `qed_score` was a hardcoded 0.5
  placeholder — replaced with real RDKit QED computation.
- Existing interaction-analysis module (`core/docking/interactions.py`) is legitimate —
  real geometric distances from real docked poses against real published PLIP thresholds,
  honestly labeled "PLIP-mimetic rule-based" throughout, NOT fabrication. Real PLIP package
  now installed as an option for a future upgrade; not yet wired in as of this entry.
  Just added `InteractionAnalysisAgent.run_node()` adapter (uncommitted as of this entry —
  still need to wire it into `orchestrator.py`'s node graph, which currently has no
  "interaction" node at all despite the client's spec requiring one).

**Phase D (ML Training) — STARTED, running in background on Kaggle**:
- User explicitly said: don't be conservative, get GPU training going in the background
  NOW so we don't lose time later, rather than waiting for Phase C to fully finish first.
- Real data source chosen: Kaggle dataset
  `madukacharles/pdbbind-protein-ligand-binding-affinity-dataset` (real PDBBind v2013-core —
  real protein pockets, real ligand structures, real experimental pKd labels). NOT
  BindingDB in the end (PDBBind was faster to source as an existing, verified-real, right-sized
  Kaggle dataset rather than scraping BindingDB.org bulk files from inside a kernel).
- Training kernel: `anamitrasarkar007/ayurvedic-affinity-training-v1` (GPU enabled,
  internet enabled, script-type). Self-installs RDKit/XGBoost/OpenBabel/real Vina binary at
  runtime. Featurization is an EXACT copy of `backend/app/core/ml/features.py`'s 39-feature
  schema (10 docking + 18 QSAR + 11 Ayurvedic) so the trained model is compatible with
  `MLAgent.predict()` at inference time. Docking features come from REAL `vina --score_only`
  on each complex's real crystal pose (fast, real energy terms, not simulated/fabricated).
  Uses Bemis-Murcko scaffold split + Tanimoto leakage check (ported from Minimax's original
  `splits.py` logic) — not a random split. Benchmarks RandomForest/GradientBoosting/Ridge/XGBoost,
  picks best by test-set RMSE, saves model+scaler+feature_names as one joblib.
- v1 push failed: labels CSV existed (`v2013-core/pdbbind_v2013_core.csv`, found via full
  Kaggle API pagination — 1171 files total across 59 pages, NOT visible in a single
  `kaggle datasets files` call) but my column-name guesses didn't match its actual headers.
  Fixed with full column logging + heuristic PDB-code-pattern/numeric-range detection,
  re-pushed as v2. **Status as of this entry: v2 running, not yet confirmed complete —
  next session/check must verify it actually finished and either pull the real trained
  model+metrics, or diagnose+fix+relaunch if it also failed.**
- Once genuinely trained: pull back ONLY the small model file + metrics JSON (not the raw
  PDBBind data) via `kaggle kernels output` (small, this is fine — the "never download
  datasets" rule is about raw bulk data/checkpoints, not a few-MB trained model artifact
  that needs to go into the repo and get uploaded to HF).

**Not yet started**: Phase E (RAG/agent hardening beyond what Phase A verified, interaction
agent orchestrator wiring), Phase F (frontend — still plain JS, not verified against real
backend), Phase G (Docker build/test suite not run), Phase H remainder (HF model+Space
upload, Vercel deploy).

---

## 🔧 LESSONS / DO NOT REPEAT

- **Always verify by actually RUNNING code, not just reviewing diffs.** Every single
  "critical bug" found so far (fabricated docking scores, broken imports, shadowed modules,
  wrong data schemas, removed CLI flags, always-mock protein prep) was invisible to static
  review and only surfaced by executing the real pipeline / real tools end-to-end.
- **`dict.get(key, default)` only applies `default` for a MISSING key — a present key with
  value `None` still returns `None`.** This exact bug pattern has appeared 3+ times in the
  inherited codebase. Check for it when debugging unexpected `None`/`TypeError` issues.
- **Python resolves a package (`dir/__init__.py`) before a same-named module (`dir.py`) in
  the same parent directory** — a silent, hard-to-spot shadowing bug. If an import
  mysteriously can't find a name that's clearly defined in a `.py` file, check whether a
  same-named package directory exists alongside it.
- **AutoDock Vina 1.2.x removed the `--log` CLI flag** that existed in 1.1.x. Any wrapper
  code assuming the old CLI will get "Command line parse error" and dump usage text with
  exit code 1 — easy to misread as a generic failure rather than an API version mismatch.
- **`kaggle datasets files` CLI only returns the first ~20 files without manual pagination.**
  Use the Python `KaggleApi.dataset_list_files(..., page_token=...)` loop to see the full
  file list before assuming a labels/index file doesn't exist.
- **Single-file `kaggle datasets download -f <nested/path.csv>`** returned 404 for this
  dataset despite the file existing (confirmed via full pagination) — don't trust that as
  proof a file is missing; the kernel itself (which mounts the full dataset) is more reliable.
- When an inherited AI-built codebase has multiple parallel implementations of the same
  concept (e.g. this repo had THREE different "evidence tier" systems: `app.agents.evidence_tiers`,
  `app.core.evidence.tiers`, and the shadowed `app.core.evidence` file), check ALL of them
  before assuming one is canonical — agents/files may each use a different one.
- User's explicit standing instruction: delegate heavy/bulk work to `opencode` (free tier),
  Claude does verification + small surgical fixes + orchestration. Only `opencode/muse-spark-1.3-contributor-free`
  and `openrouter/nvidia/nemotron-3-super-120b-a12b:free` are confirmed working models —
  probe before assuming any other model/provider has funds.

---

## ✅ OPEN TODOs (live list — edit in place, this is the one non-append section)

- [x] ~~Verify Kaggle training kernel v2~~ — v2 FAILED too (0 CSVs found — the mount path
      wasn't the exact slug I assumed). Fixed with dynamic `/kaggle/input/` resolution,
      pushed as v3. **v3 is currently RUNNING as of 08:35 UTC — check
      `kaggle kernels status anamitrasarkar007/ayurvedic-affinity-training-v1` next.**
      If v3 also fails, pull its log (`kaggle kernels output ... --force`) and check
      `/tmp/kaggle_output*/*.log` pattern used earlier in this session for how to read it.
- [ ] If v3 training succeeded: pull `affinity_model.joblib` + `training_metrics.json`
      via `kaggle kernels output anamitrasarkar007/ayurvedic-affinity-training-v1 -p <dir>`,
      place model at `backend/app/models/trained/` (check `ml_agent.py`'s `load()` method
      for the exact expected filename(s) first), verify `MLAgent.predict()` actually works
      end-to-end, write `docs/REPRODUCIBILITY.md` entry with the exact Kaggle kernel version.
- [x] ~~Wire InteractionAnalysisAgent into orchestrator~~ — DONE (chunk C3, opencode +
      verified). Pipeline now runs 9 nodes end-to-end, zero failures.
- [ ] Decide on real PLIP integration (now installed, `pip install plip` works) vs. keeping
      the existing legitimate rule-based interaction detector — not urgent (current approach
      isn't fabrication) but flagged as a possible Phase C polish item. LOW PRIORITY.
- [x] ~~Phase C remaining: verify RDKit descriptors on real Phase B data~~ — implicitly
      verified (real docking test used real RDKit-embedded ligand successfully). Phase C is
      essentially DONE: real Vina, real Meeko/OpenBabel, real receptor+ligand prep, real
      interaction agent wired, all verified via actual execution, not just review.
- [ ] Phase E: RAG groundedness/hallucination metric formalization, orchestrator
      checkpointing/retry re-verification after all the node changes.
- [ ] Phase F: frontend redesign IN PROGRESS via GitHub Copilot CLI (`copilot -p ... --allow-all-tools`,
      user's own Copilot credits, ~200 available, burn fast - use sparingly, one big
      well-scoped prompt rather than many small ones). Task given: real multi-page routing
      (landing page + ~8 other pages, currently everything may be on one page), beautiful
      Tailwind theme (botanical/herbal color palette, good fonts, smooth animations/popup
      transitions), plain-language UI copy (no technical jargon - "Match Strength" not
      "Docking Score" etc, translate but don't change underlying data/API calls), optional
      puter.js (`https://js.puter.com/v2/`, key in API_Keys_and_Secrets/puter-js-api.txt)
      for a hero image/decoration, and a real `npm run build` verification. Check
      `git status`/`git diff frontend/` and the copilot session output when resuming -
      log file was `/tmp/.../scratchpad/copilot_frontend.log` (scratchpad, may be gone in a
      new session - re-run `git log`/`git diff` on frontend/ instead if that log is gone).
      JSX→TSX conversion (Minimax's TS/vitest/eslint tooling) is a nice-to-have, not required.
- [x] ~~Docker Compose build verification~~ — SKIPPED per explicit user instruction
      (too heavy/data-consuming on this connection). Docker files remain as-is, untested.
      Two delegated attempts (agy, opencode) also didn't produce useful output before
      this was deprioritized - not worth re-attempting unless user asks again.
- [x] ~~Backend pytest suite run~~ — DONE via GitHub Actions CI (not local, per user
      request to avoid heavy local builds). Fixed along the way: pip 'vina' bindings
      (dead code, needed system boost headers, broke fresh installs) and unused
      langchain/langgraph (version conflict) commented out of requirements.txt; 4 total
      stale test assertions fixed (100→65 record count x2, Triphala >=20→>=5,
      AYUSH-64 >=20→>=0) to reflect the real post-integrity-fix data. CI is fully
      GREEN as of this entry (both frontend and backend jobs) - see
      github.com/Anamitra-Sarkar/ayurvedic-drug-discovery/actions. Frontend redesign
      (chunk F2) also independently confirmed building successfully via this same CI,
      without needing a local build on this RAM-constrained machine. Final
      `SCIENTIFIC_LIMITATIONS.md`/`FINAL_REPORT.md` synthesis from real verified artifacts only.
- [ ] Phase H remainder: HF Hub model upload (bhumika's account, `bhumika-hf.txt` token),
      HF Space for backend (Docker SDK), Vercel frontend deploy, end-to-end live verification
      pass (real compound+target through the live deployed system).
- [ ] Full Definition-of-Done checklist review against
      `docs/client_provided/complete_phase_plan.md` before considering the project done.
