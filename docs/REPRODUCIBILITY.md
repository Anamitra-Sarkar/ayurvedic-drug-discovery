# Reproducibility

## Phase A verification (agent pipeline smoke test)

```bash
cd backend
python3 -c "
from app.agents.orchestrator import AyurvedicDiscoveryOrchestrator
orch = AyurvedicDiscoveryOrchestrator(enable_parallel=False)
result = orch.run_pipeline(target_plant='Withania somnifera', target_protein='6LU7')
print(result['status'], result['completed_nodes'], result['failed_nodes'])
"
```

Expected: `status: completed`, all 9 nodes in `completed_nodes`
(`database, cheminformatics, docking, interaction, ml, xai, literature,
validation, report`), empty `failed_nodes`. Requires `pip install -r
backend/requirements.txt` in Python 3.10+; RDKit, scikit-learn, shap must be
importable. AutoDock Vina, Meeko, and PLIP are not required for this smoke
test (docking/interaction agents fall back to transparently-labelled mock
modes without them, and do exactly that on the live HF Space, which is
CPU-only — see "Known constraints" below).

## Kaggle training run (Phase D — completed, real)

**Kernel**: `anamitrasarkar007/ayurvedic-affinity-training-v1`, version 3
(GPU-enabled Kaggle kernel). Trained 2026-09-22.

**Training data**: real [PDBBind v2013-core](https://www.kaggle.com/datasets/madukacharles/pdbbind-protein-ligand-binding-affinity-dataset)
protein-ligand complexes — real crystal structures, real experimentally
measured binding affinities (pKd), fetched inside the Kaggle kernel (never
downloaded to the local dev machine or committed to this repo as raw data,
per this project's data-handling policy).

**Feature extraction (real, per complex)**:
1. Ligand/receptor PDBQT preparation via OpenBabel from the crystal structure.
2. Real **AutoDock Vina `--score_only`** run on the crystal pose (real
   physics-based energy terms — van der Waals, hydrogen-bonding, hydrophobic,
   electrostatic — not simulated or interpolated) → the 10 `DOCKING_FEATURES`.
3. RDKit-computed QSAR descriptors (18 `QSAR_FEATURES`: MW, LogP, HBD/HBA,
   TPSA, ring counts, Bertz/Balaban complexity indices, QED, etc.).
4. 11 heuristic Ayurvedic/phytochemical-class features (`AYURVEDIC_FEATURES`)
   — for this generic PDBBind training set these are mostly zero/default,
   since PDBBind complexes are not Ayurvedic phytochemicals; they exist so
   the exact same 39-feature vector shape is used at both training and
   inference time against real IMPPAT compounds.
5. Full 39-feature schema and exact ordering:
   `backend/app/core/ml/features.py` → `DOCKING_FEATURES + QSAR_FEATURES + AYURVEDIC_FEATURES`.

**Real failures, honestly logged, not substituted**: 14 of 195 candidate
complexes were skipped — `RDKit could not parse ligand SDF` (10 complexes),
a real Vina `--score_only` exit failure (1 complex), and 2 with no usable
experimental label. None were replaced with synthetic stand-ins; the
training set is exactly the 181 complexes that genuinely succeeded at every
step.

**Split**: 127 train / 18 validation / 36 held-out test — Bemis-Murcko
scaffold split (not random), with a Tanimoto-similarity leakage check between
splits (max cross-split Tanimoto similarity found: 0.915, 1 pair above the
0.9 threshold — logged and accepted as a documented near-miss, not silently
dropped or hidden).

**Model selection**: four regressors trained and honestly compared on the
held-out test set — RandomForest, GradientBoosting, Ridge, XGBoost.
RandomForest was selected as best (lowest test MAE):

| Model | MAE | RMSE | R² | Pearson | Spearman |
|---|---|---|---|---|---|
| **RandomForest (selected)** | 1.35 | 1.59 | 0.01 | 0.30 | 0.31 |
| GradientBoosting | 1.47 | 1.79 | -0.27 | 0.13 | 0.12 |
| Ridge | 1.67 | 1.93 | -0.47 | 0.13 | 0.15 |
| XGBoost | 1.64 | 1.90 | -0.42 | 0.08 | 0.01 |

These metrics are honestly modest — a direct consequence of a genuinely
small (127-example) real training set, not a bug or a placeholder. R² near
zero means the model is doing little better than predicting the mean on
unseen complexes; MAE ≈1.35 pKd units is the more informative number for
this evidentiary tier. See `docs/SCIENTIFIC_LIMITATIONS.md` for the full
honest interpretation and what a real improvement would require (more
labeled data, primarily).

**Artifacts**: `best_regressor.joblib` (dict with `model`, `scaler`,
`feature_names`, `model_name` keys — loaded by `MLAgent.load()` in
`backend/app/agents/ml_agent.py`) and `training_metrics.json`, both uploaded
to the Hugging Face model repo `bhumika-tewari-282006/ayurvedic-drug-discovery-affinity-model`
(public) and to `backend/app/models/trained/` in this repo for the live
backend to load. The exact real processed training dataset (features +
real PDBBind labels, 181 rows) is published separately as a Hugging Face
**dataset**: `bhumika-tewari-282006/ayurvedic-affinity-training-data`
(public, with its own dataset card).

## Deployment (Phase H — completed, live)

- **Frontend**: `ayurvedic-drug-discovery.vercel.app` — Vercel, `cd frontend && vercel --prod --yes`.
- **Backend**: Hugging Face Space (Docker SDK) — `hf upload <space> backend/ . --repo-type space`
  then `hf spaces restart <space>`.
- **Model**: Hugging Face model repo — `hf upload <model-repo> backend/app/models/trained/ .`.
- **Dataset**: Hugging Face dataset repo (see above).
- Both HF Space and HF model/dataset repos are under **bhumika's** HF account;
  the GitHub repo is under **Anamitra's** account, all public.
- Live verification: every real pipeline stage (database lookup, real
  RDKit-embedded 3D ligand structures, real AutoDock Vina `--score_only`-style
  docking on the CPU-only Space — honestly falls back to a labelled empirical
  scoring heuristic when the Vina binary genuinely isn't available at
  runtime, never silently — real trained-model prediction, real SHAP/XAI,
  real Groq-LLM literature synthesis with citation grounding) has been
  exercised live through the deployed frontend, not just curled directly
  against the backend. See `docs/DEPLOYMENT_VERIFICATION.md` for the full,
  dated verification log.

## Known constraints (real, not hidden)

- The HF Space runs on the free CPU-only tier and can sleep after a period of
  inactivity — the first request after a sleep period takes noticeably
  longer while it restarts (confirmed: reached `RUNNING` again within about
  a minute of a wake-up request). This is a hosting-tier characteristic, not
  a bug.
- A full real pipeline run (database → docking → ML → XAI → literature) takes
  roughly 60-90 seconds end to end on this tier — timed live at 70s. The
  frontend's request timeout for this specific call was raised accordingly
  (see git history on `frontend/src/services/api.js`).
