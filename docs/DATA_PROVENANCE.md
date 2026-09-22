# Data Provenance

Master record of every dataset used in this pipeline: source, retrieval method,
retrieval date, record counts, and status. No dataset is used in training or
shipped as "real" without an entry here.

## Verified so far (Phase A)

### IMPPAT sample (phytochemical seed data)
- **File**: `backend/app/data/imppat_sample.json`
- **Shipped by**: Meta AI's original build (inherited into this repo's seed commit)
- **Structure** (verified by actually loading it, 2026-09-22): flat list of 100
  records, one per (plant, phytochemical) pair - fields include
  `plant_botanical_name`, `plant_common_name`, `phytochemical_name`, `smiles`,
  `canonical_smiles`, `pubchem_cid`, `molecular_formula`, `molecular_weight`,
  `therapeutic_uses`, `ayurvedic_properties`, `traditional_formulations`,
  `admet`, `drug_likeness`, `bioactivity`.
- **Coverage**: 20 distinct plants, 100 phytochemical records.
- **Spot-check**: first record (Gallic acid / Amla, `Emblica officinalis`) has a
  real SMILES (`C1=CC(=C(C(=C1O)O)O)C(=O)O`) and molecular weight (170.12)
  matching gallic acid's actual known values.
- **Status**: real, in use, successfully loaded and exercised end-to-end through
  the full agent pipeline (see `docs/phase_docs/00-index.md` Phase 4 note).
- **Gap**: only 100 phytochemicals / 20 plants - far short of IMPPAT's full
  ~9,600 phytochemicals / ~1,742 plants. Full-scale acquisition is Phase B.

### Literature corpus (RAG grounding)
- **Location**: `backend/app/data/literature_corpus/` (`references.json` + 5 full
  paper `.txt` files), ingested into a TF-IDF index at runtime
  (`backend/app/core/rag/corpus.py`, `retriever.py`).
- **Coverage**: 40 documents matching the 40 references in
  `docs/REFERENCES.md` / the client-provided literature review.
- **Status**: real, verified - RAG retrieval, citation validation, and
  clinical-overclaim sanitization were all observed firing correctly on real
  queries during the Phase A pipeline smoke test (e.g. citations
  `REF_034, REF_033, REF_036` returned and validated against the actual corpus,
  not fabricated).

### ML rescorer model (docking-score rescoring, NOT the primary affinity model)
- **File**: `backend/app/models/ml_rescorer.pkl` (7.0MB)
- **Metrics on load**: RMSE 0.717, R² 0.760, n=1200 (self-reported in the
  pickle's metadata, not independently re-verified against held-out data yet -
  flagged for Phase D re-audit).
- **Status**: real file, loads successfully, used only as an auxiliary rescorer
  inside `DockingAgent`'s hybrid scoring - NOT the primary binding-affinity
  predictor and NOT a substitute for real training data.

## Not yet real (scheduled for Phase B/D)

- **PubChem enrichment** (CID/InChIKey cross-referencing beyond the 100 seed
  records) - pending.
- **RCSB PDB structures** for real docking targets - pending (Phase C needs
  real `.pdb` files; current smoke test used target string `"6LU7"` only as an
  identifier, no structure was actually downloaded or docked against).
- **Real binding-affinity training data** (BindingDB or PDBBind) - the
  currently-loaded MLAgent has **no trained model at all**
  (`backend/app/models/trained/` does not exist yet); the pipeline honestly
  reports `status: model_not_trained` rather than fabricating predictions.
  This is the single most important remaining data gap - see Phase D.
- **Expanded literature corpus** beyond the original 40 references, if needed
  for broader RAG coverage.

## Rule

Every future entry in this file must include: source URL, retrieval date,
record count, and how it was spot-checked. An entry that only says "generated"
or "synthetic" must be explicitly labelled as such and excluded from any
real-training or real-results path.
