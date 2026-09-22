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

**Update (~14:00 UTC, same session)**: Phase D model trained for real on Kaggle
(RandomForest, real PDBBind data, modest honest metrics - MAE 1.35, R² 0.01, see the
HF model card), interaction agent wired (9 nodes, zero failures), Phase F/G/H all
substantially completed:
- Full frontend redesign shipped (landing page, botanical theme, plain-language copy,
  animations) via opencode - real `npm run build` success confirmed via GitHub Actions CI
  (not local, per user's low-RAM-machine constraint).
- Deployed live: GitHub Actions CI green, HF model uploaded (bhumika's account), HF Space
  backend live (Docker SDK), Vercel frontend live. See `docs/DEPLOYMENT_VERIFICATION.md`.
- User did a live walkthrough via Claude-in-Chrome and found REAL bugs static review
  missed: (1) Vercel SPA routing 404'd on direct URL nav (missing `vercel.json` rewrite -
  fixed), (2) puter.js consent popup was intrusive - user asked for full removal, done
  (HeroArt now always uses the hand-crafted gradient, no runtime AI image call), (3) a
  **serious fabrication bug**: `/api/literature/query`'s real backend route called a
  method that doesn't exist on `LiteratureAgent` (`agent.query(...)` - real method is
  `answer_question(...)`), so it silently fell into a hardcoded except-block returning
  FAKE citations (REF_004/007/012) and a templated fake answer for every single query,
  regardless of content - found via live testing (identical response to different
  queries), fixed to call the real method.
- Comprehensive audit + fix pass (delegated to opencode/agy per explicit user
  instruction to conserve Claude usage): mobile/device responsiveness across every page
  (real card-based mobile table layout, clamped 3D-viewer sizing, scrollable nav, etc.),
  and a "dummyness" audit of `frontend/src/services/api.js` that found it had a
  MOCK_*-presented-as-real fallback for EVERY API function, tagged with real-looking
  evidence tiers - fixed by gating all mock data behind `import.meta.env.DEV` (never
  served in production) and re-throwing real errors instead. Also found and fixed 4 more
  real frontend↔backend endpoint mismatches (`/compounds/:id` route didn't exist -
  added a real one; `/xai/explain`→`/ml/explain`; `/network/triphala`→`/database/triphala`;
  `/literature/query` POST→GET) plus a genuinely-wired real `/candidates/rank` endpoint
  built on `DockingAgent.rank_eleven_candidates()`.
- **Groq LLM wiring for RAG** (user requested, since credits are tight everywhere):
  `CitationGroundedGenerator` now supports Groq's OpenAI-compatible API via
  `GROQ_API_KEY`. First deploy attempt silently kept using the honest mock because the
  hardcoded model name `llama-3.3-70b-versatile` 404'd (Groq deprecated/renamed it) -
  found via reading live HF Space container logs (`hf spaces logs <space> -n 200`, NOT
  the `--type` flag which doesn't exist), fixed by querying Groq's real live model list
  (`GET https://api.groq.com/openai/v1/models`) and switching to `openai/gpt-oss-120b`
  (verified with a real completion call before deploying). **Confirmed live**: real,
  natural-language, markdown-formatted LLM answers now returned by
  `/api/literature/query`, not the mock template.
- **agy CLI note**: `--dangerously-skip-permissions` / `--mode accept-edits` are both
  blocked by Claude Code's own harness-level "Create Unsafe Agents" classifier, separate
  from any user permission setting - user explicitly allowed it mid-session and it then
  worked. If a fresh session hits this same block, tell the user it needs their
  Claude Code permission settings (not just a spoken "yes") - Claude cannot self-grant it.
- **HF Space secrets note**: use `hf spaces secrets add/ls/delete <space> -s KEY=VALUE`
  (proper CLI) rather than the raw `/secrets` POST endpoint - both work, but the CLI is
  easier to verify with `hf spaces secrets ls`. A Space needs an explicit
  `restart` (`hf spaces restart` or the `/restart` API) after adding/changing a secret -
  don't assume the next natural rebuild alone picks it up promptly.
- Still open from this update: opencode's error-state UI task (making the 5 frontend
  pages handle a real API failure gracefully instead of an infinite spinner, now that
  fake fallback data is gone) was dispatched but not yet confirmed complete as of this
  entry - check git status/diff on `frontend/src/pages/*.jsx` and `ui.jsx` next.

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
- [x] ~~Phase H: HF model upload, HF Space backend, Vercel frontend deploy~~ — DONE.
      Live URLs: frontend https://ayurvedic-drug-discovery.vercel.app , backend
      https://bhumika-tewari-282006-ayurvedic-drug-discovery-backend.hf.space , model
      https://huggingface.co/bhumika-tewari-282006/ayurvedic-drug-discovery-affinity-model .
      See docs/DEPLOYMENT_VERIFICATION.md. Verified via direct curl: real target data
      returned, both frontend and backend /docs return HTTP 200. GitHub Actions CI is
      fully green (frontend+backend). **Not yet done**: exercising a full pipeline run
      (`POST /api/pipeline/run`) through the live frontend in an actual browser - the
      individual pieces are verified live but the full user journey isn't yet.
- [x] ~~Exercise the full pipeline run through the live frontend in an actual browser~~ —
      DONE this session (2026-09-22), see session log entry below. Found and fixed a long
      chain of real bugs the way live testing keeps finding them: wrong request-body field
      names, response-shape mismatches, a broken FastAPI JSON encoder path, a completely
      fake 3D viewer, and 3D style buttons that didn't do anything visible. All fixed,
      redeployed, and re-verified live via Claude-in-Chrome + direct curl.
- [ ] Full Definition-of-Done checklist review against
      `docs/client_provided/complete_phase_plan.md` before considering the project done.

---

## Session log — 2026-09-22 14:02 UTC

Continuing from a prior session that left backend/frontend fixes uncommitted in the
working tree (docking.py, ml.py, pipeline.py, Targets.jsx, PipelineRun.jsx ID fix).
User's ask this session: fix the sharp-edged protein-shape dropdown, check whether the
"3D thing" is dummy, and finish whatever's left.

**Committed/deployed in order (6 commits, each redeployed to HF Space + Vercel and
re-verified live before moving to the next):**

1. `71278f2` — pushed the prior session's uncommitted fixes: docking.py/ml.py/pipeline.py
   wrong-method-name fallbacks (agent.dock/predict/explain didn't exist → fell back to
   random.seed fake scores), Results.jsx was passing the compound ID as `smiles` to
   docking/ML/XAI instead of resolving the real SMILES first, Targets.jsx field-name
   mismatch, PipelineRun.jsx's fake setTimeout-only "6 steps" animation replaced with one
   that narrates while the REAL pipeline call runs in the background (caps at 92% until
   it actually resolves, shows a real error on failure), rounded-corner dropdown fix
   (native `<select>` needs `appearance-none` — `rounded-2xl` alone is ignored by most
   browsers) on both the pipeline page and SearchBar.
   - **Deploy hiccup found+fixed in the same pass**: `hf upload backend/ .` silently
     overwrote the HF Space's root `README.md` (which carries required
     `sdk: docker`/`app_port` YAML frontmatter) with `backend/README.md` (a plain doc,
     no frontmatter) → Space went to `CONFIG_ERROR`. Recovered the correct README from
     Space commit history, restored it, and **renamed `backend/README.md` →
     `backend/BACKEND_README.md`** in the repo so this can't happen again on future
     uploads. If you ever re-run `hf upload bhumika-tewari-282006/ayurvedic-drug-discovery-backend backend/ . --repo-type space`, this collision is now avoided.
2. `43afd05` — `/ml/explain` still 500'd after live testing: `expl.__dict__` (raw
   dataclass) left numpy arrays nested inside it, which FastAPI's `jsonable_encoder`
   cannot serialize. Fixed to use `explain_prediction(..., return_evidence_tagged=True)`
   + `.to_dict()`, same pattern the rest of the codebase already uses.
3. `6dd738e` — all 5 endpoints returned real 200s but the UI showed 0.00/NaN/empty
   everywhere because real backend field names don't match what the (already-built, not
   rewritten) display components expect: `best_affinity_kcal_mol`/`all_poses` vs.
   `affinity_kcal_mol`/`poses`; `predicted_pkd`/`applicability_domain.is_inside` (word
   confidence) vs. `pKd_pred`/`.inside` (numeric 0-1 confidence); nested
   `data.shap.top_features` ([name, shapValue] pairs) vs. a flat `topFeatures` array.
   Added `normalizeDocking`/`normalizeMLPrediction`/`normalizeExplanation` in `api.js`
   (same pattern as the pre-existing `normalizeCompound`) rather than rewriting the
   components. `affinity_nM` is a real pKd→nM conversion (`10^(9-pKd)`), not fabricated.
4. `15acc53` — **the actual "is the 3D thing dummy" answer: yes.**
   `MoleculeViewer.jsx`'s `defaultLigandSDF` was literally commented `Withaferin A mock`
   (8 fabricated atoms) and `defaultProteinPDB` was a fake 6-residue fragment — and
   `Results.jsx` never passed real `proteinPDB`/`ligandSDF` props at all, so EVERY
   result page showed the same fake molecule regardless of compound. Real structures
   already existed on disk mid-request (`prepare_ligand` does a real RDKit 3D
   embed+MMFF optimize; `prepare_protein` fetches the real RCSB crystal structure or the
   CI-cached one) but were never read back into the API response. Fixed:
   `docking_agent.py`'s `run_docking()` now reads both real PDB files and returns them
   as `data.structures.{ligand_pdb, protein_pdb}` (honest empty string if a file is
   genuinely missing, never fabricated); wired through `api.js` → `Results.jsx` →
   `MoleculeViewer`'s new `ligandPDB` prop. Verified live via curl: real 6613-byte
   RDKit-embedded Withaferin A ligand + the real 239KB RCSB 6LU7 (COVID-19 Mpro) crystal
   structure, confirmed rendering in the browser.
5. `ec3f8a5` — user immediately caught the follow-on bug: all 4 style buttons
   (Sticks/Balls/Lines/Ribbons) looked identical even with real data, because they only
   ever restyled the tiny ligand (model 1) — the protein (model 0, hundreds of residues,
   dominates the view) was hardcoded to cartoon+stick regardless of the selected button.
   Extracted `proteinStyleFor()`/`ligandStyleFor()`, applied both models' styles together
   on init and on every button change. Verified live: "Sticks" now shows the full
   all-atom protein, "Ribbons" shows a visibly distinct cartoon backbone with real
   helices/sheets.

**Lesson reinforced (again) this session**: every one of bugs 1-5 above passed a code
read and "looks right" review earlier — every single one was only found by actually
clicking through the live deployed app and reading real network responses / HF Space
logs. Static review does not substitute for exercising the real endpoints end-to-end.
**Deploy-tooling lesson (new)**: `hf upload <space> <local_dir> .` overwrites the
Space's ENTIRE root, including files that only exist on the Space (like its
YAML-frontmatter README) and were never part of the git repo being uploaded — always
check `hf spaces logs`/Space status after any such upload, not just after a code change.

**Not yet done**: full Definition-of-Done checklist pass against
`docs/client_provided/complete_phase_plan.md`; `/candidates/rank` (the Shortlist/ranking
page's batch docking) was not checked for the same real-3D-structure gap this session —
worth a quick live check next session since it shares `DockingAgent` but calls
`batch_docking()`, a separate method from the now-fixed `run_docking()`.

---

## Session log — 2026-09-22 14:47 UTC (continuation, same day)

User asked to verify the 3D viewer generalizes to other compounds/targets and to do a
full top-to-bottom dummy-data audit of the whole app (UI + backend), then give a
submission-readiness verdict. Found and fixed 8 more real issues via live testing +
targeted grep audits, all committed/pushed/redeployed (4 commits: `2b08b3f`, plus the
tooltip fix `b5ae873` and timeout fix `4fd64f3` landed in this same continuous session).

**3D viewer generalization**: confirmed live with a second, different compound+target
pair (Gallic acid / IMP000001 vs 3FXI/TLR4, not the Withaferin A/6LU7 pair used to build
the fix) — real, visibly different protein structure, real distinct docking numbers, all
4 style buttons work. The fix generalizes, not a one-compound coincidence.

**Grep-audit findings**:
- `backend/app/agents/__init__.py` imported `DatabaseAgent`/`CheminformaticsAgent`/
  `DockingAgent`/`MLAgent`/`XAIAgent` from `other_agents.py`, a leftover set of
  fabricated random.seed-based stub classes that predates this session's real-agent
  integration. Confirmed via grep that nothing in the live app imports the package root
  (every route imports real modules directly), so this was dead code today — but it
  silently shadowed the real names, a landmine for any future `from app.agents import X`.
  Fixed the `__init__.py` to import the real modules; **deleted `other_agents.py`
  entirely** (607 lines) since nothing referenced it anymore, both in git and on the live
  HF Space (`hf upload` does not delete stale remote files, had to `HfApi().delete_file`
  separately — worth remembering for any future file removal, not just additions).
- `database_agent.py`'s `get_network_pharmacology_graph()` (contains `is_mock`-labeled
  synthetic network-expansion nodes, gated behind `include_extended_mock=True` default)
  is defined but **never called by any live route** — confirmed via grep. `/database/triphala`
  (what the frontend's Plant map page actually calls) is a separate, hand-written, fully
  real endpoint using real cited literature figures. Left as unreachable dead code for
  now; flagging for a future cleanup pass, not urgent since it's genuinely unreachable.
- `NetworkGraph.jsx` hardcoded `"6 targets"` and `"Compounds (174)"` as literal text in
  the Plant map page header, ignoring the real `stats.targets`/`stats.bioactives` values
  the API actually returns (real number is 44 shared targets, a cited literature figure,
  not 6). Fixed both to read from real stats.

**User-reported bugs this round, all fixed+deployed+verified live**:
1. Compound descriptor tiles (oil-water mix, exposed surface, bonding spots, balance
   score) always showed "—" despite being real, already-computed RDKit values
   (`drug_likeness.logP/tpsa/num_hbd/num_hba/qed_score`) — `normalizeCompound()` just
   never mapped them. Confirmed live: IMP000013 now shows 2.28 / 63.47 / 3/6 / 0.37 and
   a "Passes 4/4 basic checks" chip.
2. Literature "sticks to sources" stuck at 0.00 / "source papers (0)" even on a real,
   already-correct backend answer. Root cause: the real endpoint's nested response
   shape (`content.answer`, top-level `citations` with real authors/doi/journal) never
   matched what `LiteraturePanel.jsx` reads (flat `synthesis`/`citations`/`faithfulness`).
   Added `normalizeLiterature()`. Confirmed live via curl that the backend was already
   honestly refusing to answer when its corpus had nothing on a given compound
   ("does not contain any information on gallic acid...") — that real, correct honesty
   just never reached the screen before.
3. Best Attempts table numbers overlapping across columns on mobile — real docking
   floats come back with 15+ significant digits (e.g. `-6.347847183429078`); added a
   display-only `fmt()` (2 decimals) in `DockingResults.jsx`. This is also the most
   likely cause of the reported "page suddenly zoomed out" (oversized unrounded content
   forcing horizontal overflow, which mobile browsers respond to by auto-zooming out) —
   added `overflow-x: hidden` on html/body as a defensive backstop either way.
4. Ugly scrollbar on horizontally-scrolling pill/tab nav strips (result tabs,
   compound-detail tabs, 3D style buttons) — added a `.scrollbar-hide` utility
   (still swipeable, no visible track).
5. **"Analysis failing continuously" / "backend down?"** — NOT a backend or mobile
   issue. Timed a real `POST /api/pipeline/run` live: **70 seconds** end to end (real
   Vina docking + real RandomForest predict + real XAI + several real Groq LLM calls for
   literature). The shared axios client has a hardcoded 30s timeout, so every single real
   pipeline run was guaranteed to abort before finishing, on any device. This was the
   most serious bug found this session - the core "run an analysis" feature was silently
   broken for every real user. Fixed: `runPipeline()` now overrides to a 150s timeout
   (confirmed every other endpoint completes in 3-4s live, so only this one call needed
   it). Also improved the wait UX so a 70-90s wait doesn't look frozen (real-elapsed-time
   heartbeat log after the 6 scripted narration steps exhaust) and fixed the "about a
   minute" intro copy to "usually one to two minutes". **Verified live end-to-end after
   the fix: a real run completed and reached "Done — your results are ready" at 100%.**

**Environment limitation hit this session**: `resize_window`/mobile-viewport emulation
did not actually change `window.innerWidth` in this Claude-in-Chrome session (stayed at
~1880px regardless of the requested 390x844) — could not get a true narrow-viewport
screenshot to visually confirm the mobile CSS fixes (scrollbar-hide, number formatting,
overflow-x). The underlying bugs were still root-caused precisely (oversized raw
floats, truthy-empty-array rendering, hardcoded scrollbar) and the fixes are structurally
correct CSS/logic, confirmed via DOM/data inspection at the current viewport - just not
visually re-confirmed at a literal 390px width. If mobile issues persist, a real device
or an actual mobile-emulation-capable environment is needed to visually re-check.

**Submission-readiness verdict**: CI green on every commit this session (confirmed via
`gh run list`). All 5 user-reported bugs this round fixed, deployed, and live-verified
(except the visual mobile-width re-check per the limitation above). Core "run a real
analysis" flow was silently broken until the timeout fix — now confirmed working
end-to-end live. Remaining before a confident "ready" call: the Definition-of-Done pass
against `docs/client_provided/complete_phase_plan.md` (still not done, tracked above),
and ideally a real mobile-device spot check given the emulation limitation.
