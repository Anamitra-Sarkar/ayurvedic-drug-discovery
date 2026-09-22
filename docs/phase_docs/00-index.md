# Phase Documentation Index

This project follows the 8-phase methodology specified in the client's brief
(`docs/client_provided/complete_phase_plan.md`). Each phase below links to where
its Definition-of-Done evidence actually lives in this repo — no phase is marked
complete here until the linked artifact is real and has been verified by running
it, not just written.

| Phase | Status | Evidence |
|---|---|---|
| 1. Literature Review & Research Design | Done | `docs/LITERATURE_REVIEW_COMBINED.md`, `docs/LITERATURE_MATRIX.md`, `docs/RESEARCH_GAP.md`, `docs/REFERENCES.md` (40 refs, reused from client-provided review) |
| 2. Data Collection, Segregation, Cleaning | In progress | `docs/DATA_PROVENANCE.md` (real IMPPAT seed data verified in Phase A; PubChem/PDB/BindingDB real acquisition scheduled for Phase B) |
| 3. Dataset Training & Benchmarking | Pending | Real training data + Kaggle GPU run scheduled for Phase D; `docs/REPRODUCIBILITY.md` will carry the exact kernel ID |
| 4. Full Scientific Implementation | In progress | Backend agent pipeline verified end-to-end (Phase A); docking/RDKit/PLIP hardening scheduled for Phase C |
| 5. Evaluation Metrics & Validation | Pending | `backend/app/agents/validation_agent.py` (evidence-tier compliance, overclaim guard, hallucination check - all verified running); quantitative model metrics pending Phase D |
| 6. Results & Analysis | Pending | `docs/FINAL_REPORT.md` (to be written from real artifacts in Phase G) |
| 7. Discussion, Limitations, Future Work | Pending | `docs/SCIENTIFIC_LIMITATIONS.md` |
| 8. Final Report & Presentation | Pending | `docs/FINAL_REPORT.md` |

See `docs/client_provided/complete_phase_plan.md` for the full original brief this
tracks against.
