# Phase 3 — Dataset Training & Benchmarking

**Status: Complete.**

## Goal

Determine which computational model and feature representation performs best before
integrating the model into the final application.

## 3.1 Feature Engineering

39 features computed per compound, using RDKit and real docking output:

**Molecular descriptors (18, RDKit)**: molecular weight, LogP, hydrogen-bond donors,
hydrogen-bond acceptors, rotatable bonds, topological polar surface area (TPSA),
heavy-atom count, ring count, aromatic ring count, fraction CSP3, aliphatic/
heterocycle ring counts, formal charge, radical electron count, Bertz complexity
index (`bertz_ct`), Balaban topological index (`balaban_j`), a Burden eigenvalue
descriptor (`bcut2d_mwhi`), and QED drug-likeness score.

**Docking-derived features (10)**: real AutoDock Vina `--score_only` energy terms —
`vina_affinity`, ligand efficiency, intermolecular energy, torsional energy,
desolvation energy, hydrogen-bond count, hydrophobic-contact count, van der Waals
contact count, electrostatic score, and pocket occupancy.

**Ayurvedic heuristic features (11)**: phytochemical-class one-hot flags (flavonoid,
alkaloid, terpenoid, phenolic, saponin, tannin), a privileged-scaffold flag, a
traditional-use frequency score, and three Ayurvedic dosha-association scores.

Full exact schema and ordering: `backend/app/core/ml/features.py`. Morgan
fingerprints were evaluated during development but not included in the final
feature set — with a genuinely small (127-example) training set, a compact,
interpretable descriptor set was judged more appropriate than a high-dimensional
fingerprint representation, consistent with the literature reviewed in
`docs/LITERATURE_REVIEW_COMBINED.md` §3.2.D (classical descriptors remaining
competitive with learned representations under limited training data).

## 3.2 Dataset Splitting

**Bemis-Murcko scaffold split, not random**, with a Tanimoto-similarity leakage
check between splits:

| Split | Rows |
|---|---|
| Train | 127 |
| Validation | 18 |
| Test (held out) | 36 |

Max cross-split Tanimoto similarity found: 0.915 (one flagged pair, above the 0.9
threshold) — logged and accepted as a documented near-miss rather than silently
hidden or dropped.

## 3.3 Candidate Models

Four regressors benchmarked, deliberately excluding deep learning: with 127 training
examples, a neural network would not be justified by dataset size, consistent with
the client's own instruction not to include complex models merely for the sake of
using deep learning.

- Baseline / Ridge regression
- Random Forest
- Gradient Boosting
- XGBoost

## 3.4 Benchmarking — real results, not fabricated

Trained on a GPU-enabled Kaggle kernel (`anamitrasarkar007/ayurvedic-affinity-training-v1`,
version 3), evaluated on the held-out 36-complex test set:

| Model | MAE | RMSE | R² | Pearson | Spearman |
|---|---:|---:|---:|---:|---:|
| **RandomForest (selected)** | 1.35 | 1.59 | 0.01 | 0.30 | 0.31 |
| GradientBoosting | 1.47 | 1.79 | -0.27 | 0.13 | 0.12 |
| Ridge | 1.67 | 1.93 | -0.47 | 0.13 | 0.15 |
| XGBoost | 1.64 | 1.90 | -0.42 | 0.08 | 0.01 |

RandomForest was selected as the best model by held-out test MAE. **These values are
reported exactly as measured — not smoothed over.** R² near zero on a 36-complex test
set is an honest, direct consequence of a small real training set; see
`docs/SCIENTIFIC_LIMITATIONS.md` for full interpretation.

## 3.5 Data Leakage Prevention

Explicitly checked, not assumed:

- **Scaffold overlap**: the split is scaffold-based, not random, specifically to
  prevent near-identical molecules landing in both train and test.
- **Tanimoto similarity leakage**: computed pairwise across splits; one pair above
  the 0.9 threshold was found, logged, and reported (§3.2) rather than hidden.
- **Duplicate compounds across splits**: checked as part of the scaffold-split
  procedure.
- **Feature availability at prediction time**: all 39 features are computable from
  a ligand SMILES + a chosen target at real inference time (the same feature
  pipeline runs identically in production); no feature depends on information that
  would be unavailable when a real prediction is requested.
- **Real, honestly-excluded failures, not substituted data**: of 195 candidate
  complexes, 14 were excluded — 10 real RDKit ligand-SDF parse failures, 1 real Vina
  `--score_only` exit failure, 2 with no usable experimental label. None were
  replaced with fabricated or interpolated values.

## 3.6 Phase 3 Deliverables

| Deliverable | Location |
|---|---|
| Versioned training dataset (181 real rows) | Hugging Face dataset `ayurvedic-affinity-training-data` |
| Feature-generation pipeline | `backend/app/core/ml/features.py` |
| Train/validation/test splits (scaffold-based) | Documented above; reproducible via the Kaggle kernel |
| Benchmark experiments (4 models) | §3.4 above; raw metrics in `training_metrics.json` on the HF model/dataset repos |
| Best model selection | RandomForest, by held-out test MAE |
| Saved model artifact | `backend/app/models/trained/best_regressor.joblib`; also on Hugging Face (`ayurvedic-drug-discovery-affinity-model`) |
| Reproducible training code | Kaggle kernel `anamitrasarkar007/ayurvedic-affinity-training-v1` (v3) |
| Experiment logs | `training_metrics.json` — includes per-complex skip reasons, elapsed time, leakage-check output |

---
*Previous: [Phase 2 — Data Collection](phase-2-data-collection.md) · Next: [Phase 4 — Full Scientific Implementation](phase-4-scientific-implementation.md)*
