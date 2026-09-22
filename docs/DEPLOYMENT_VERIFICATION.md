# Deployment Verification

**Date**: 2026-09-22

## Live URLs

- **Frontend**: https://ayurvedic-drug-discovery.vercel.app (Vercel, production)
- **Backend API**: https://bhumika-tewari-282006-ayurvedic-drug-discovery-backend.hf.space
  (HuggingFace Space, Docker SDK, bhumika's account)
- **API docs**: https://bhumika-tewari-282006-ayurvedic-drug-discovery-backend.hf.space/docs
- **Trained model**: https://huggingface.co/bhumika-tewari-282006/ayurvedic-drug-discovery-affinity-model
- **Source code**: https://github.com/Anamitra-Sarkar/ayurvedic-drug-discovery

## Verification performed

- `GET /api/pipeline/targets` on the live backend returns real target data (10 real
  protein targets with real PDB IDs, binding sites, disease associations) — confirmed
  via direct `curl`, not through the frontend.
- Frontend (`/`) returns HTTP 200.
- Backend `/docs` (FastAPI auto-generated docs) returns HTTP 200.
- Frontend's `VITE_API_BASE` production env var set to the real backend's `/api` URL
  (not a mock/relative path) — frontend was rebuilt and redeployed after setting this.
- HF Space build completed successfully (real Docker build on HF's infrastructure,
  torch/transformers/rdkit all installed) and reached `RUNNING` state.

## Known follow-ups

- Full pipeline run (`POST /api/pipeline/run`) not yet exercised end-to-end through the
  live frontend in a browser - worth a manual check.
- HF Space is on the free `cpu-basic` tier - real docking (Vina) and RAG retrieval will
  be slower than local testing; large real Vina exhaustiveness settings may time out on
  CPU-only free tier. Consider this a known constraint, not a bug.
