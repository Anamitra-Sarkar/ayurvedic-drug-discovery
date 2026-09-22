# Reproducibility

## Phase A verification (agent pipeline, no training)

Reproduce the Phase A end-to-end smoke test:

```bash
cd backend
python3 -c "
from app.agents.orchestrator import AyurvedicDiscoveryOrchestrator
orch = AyurvedicDiscoveryOrchestrator(enable_parallel=False)
result = orch.run_pipeline(target_plant='Withania somnifera', target_protein='6LU7')
print(result['status'], result['completed_nodes'], result['failed_nodes'])
"
```

Expected: `status: completed`, all 8 nodes in `completed_nodes`
(`database, cheminformatics, docking, ml, xai, literature, validation, report`),
empty `failed_nodes`. `validation_passed` is expected to be `False` at this
phase - that is correct, honest behavior (no trained ML model, docking in mock
mode), not a bug.

Requires: `pip install -r backend/requirements.txt` in a Python 3.10+
environment. RDKit, scikit-learn, shap must be importable; AutoDock Vina,
Meeko, and PLIP are NOT required for this smoke test (docking/interaction
agents fall back to transparently-labelled mock modes without them).

## Kaggle training run (Phase D)

To be filled in with the exact Kaggle kernel ID, dataset version, and command
once a real training run has actually executed - never filled in speculatively.

## Deployment (Phase H)

To be filled in with the live HF Space / Vercel URLs and the exact deploy
commands once deployment has actually happened and been verified live.
