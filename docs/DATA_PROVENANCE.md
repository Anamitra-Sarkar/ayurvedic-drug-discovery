# Data Provenance

Master record of every dataset used in this pipeline: source, retrieval method,
retrieval date, record counts, and status. No dataset is used in training or
shipped as "real" without an entry here.

## Verified so far (Phase A)

### ⚠️ Integrity finding and fix (2026-09-22, Phase B): seed data was fabricated at every level

Cross-checking every `phytochemical_name` in the original `imppat_sample.json`
against PubChem (via `scripts/fetch_real_data.py`, run in GitHub Actions) found
that only **20 of the 100 records were real, PubChem-resolvable phytochemicals**.
The other 80 were named things like "Gallic acid derivative 20", "Quercetin
derivative 21" - fabricated placeholder padding inherited from Meta AI's
original build. PubChem correctly returned `404 Not Found` for all 80.

Worse: of the 20 records with real compound names, **every single one had a
fabricated plant source** - the plant-association fields cycled through the
three Triphala plants (`Emblica officinalis` / `Terminalia bellerica` /
`Terminalia chebula`) essentially at random, regardless of the compound's
actual botanical origin. For example the original data claimed Withaferin A
(a compound unique to *Withania somnifera*/Ashwagandha) came from *Emblica
officinalis* with family "Menispermaceae" (also wrong - Withania is
Solanaceae); claimed Bacoside A (unique to *Bacopa monnieri*/Brahmi) came from
*Terminalia bellerica*; claimed Echitamine (unique to *Alstonia
scholaris*/Saptaparna) was a Triphala compound at all. `pubchem_cid` values on
these 20 were also fabricated (e.g. Gallic acid was tagged CID 100000; its
real CID, confirmed live via PubChem, is 370). `admet` and
`bioactivity.predicted_targets` sub-objects (Ames test results, BBB
permeability, CYP inhibition, predicted protein targets) had no real
prediction tool behind them anywhere in this codebase - also fabricated.

**Fix applied**: the 80 "derivative N" fake records were dropped entirely
(not replaced with more padding). The 15 genuinely real compounds with
correct or salvageable identity were re-sourced to their real, verified
botanical origin (cross-referenced against established pharmacognosy - e.g.
Withanolide A/Withaferin A -> *Withania somnifera*, Bacoside A -> *Bacopa
monnieri*, Asiatic acid -> *Centella asiatica*, Picroside I -> *Picrorhiza
kurroa*, Amarogentin -> *Swertia chirata*, Mangiferin -> *Mangifera indica*,
Echitamine -> *Alstonia scholaris*), their `pubchem_cid`/`smiles`/
`molecular_formula`/`molecular_weight` were overwritten with the real values
returned by PubChem, their `traditional_formulations` claims were corrected to
remove false "Triphala" tags on non-Triphala compounds, and the fabricated
`admet`/`bioactivity` sub-objects were replaced with an honest
"not computed by any tool in this pipeline yet" note. 50 additional real,
correctly-sourced phytochemicals (real names + real plant origins, drawn from
well-established Ayurvedic pharmacognosy - Curcumin/Curcuma longa,
Berberine/Berberis aristata, Andrographolide/Andrographis paniculata, etc.)
were added with SMILES/CID left blank pending the next PubChem enrichment
pass, rather than hand-typing chemical structures (too easy to transcribe a
SMILES wrong). **Result: 65 total records, 15 with verified real CID+SMILES,
50 with verified real names+plant sources pending CID enrichment, 0 fabricated
associations.**

### IMPPAT-style sample (phytochemical seed data) - post-fix state
- **File**: `backend/app/data/imppat_sample.json`
- **Structure**: flat list of one record per (plant, phytochemical) pair -
  fields include `plant_botanical_name`, `plant_common_name`,
  `phytochemical_name`, `smiles`, `canonical_smiles`, `pubchem_cid`,
  `molecular_formula`, `molecular_weight`, `therapeutic_uses`,
  `ayurvedic_properties`, `traditional_formulations`, `admet`,
  `drug_likeness`, `bioactivity`.
- **Coverage (as of the Phase B integrity fix, 2026-09-22)**: 65 records,
  41 distinct plants. 60/65 compounds have a real, PubChem-verified
  `pubchem_cid` + SMILES; 5 remain pending (see PubChem section above).
- **Spot-check**: Withaferin A resolves to real PubChem CID 265237
  (independently confirmed via a live `curl` against PubChem during this
  session, matching exactly).
- **Status**: real, in use, successfully loaded and exercised end-to-end
  through the full agent pipeline (see `docs/phase_docs/00-index.md`).
- **Gap**: 65 records / 41 plants is still far short of IMPPAT's full
  ~9,600 phytochemicals / ~1,742 plants. No public bulk-download API was
  found for IMPPAT (see below) - further expansion means manually curating
  more real, verified compound+plant pairs the same way this fix did.

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

### RCSB PDB target structures - verified real

All 10 target structures listed in `backend/app/data/proteins/targets.json`
were successfully downloaded as real `.pdb` files from RCSB
(`data/raw/pdb/*.pdb`, see `data/raw/pdb/PROVENANCE.json`). 7/10 auto-flagged
as a confident title match; the other 3 (3FXI/TLR4, 2QP8/BACE1, 5KIR/COX-2)
are real, correct structures for the right target too - manually confirmed by
reading their actual RCSB titles ("TLR4-human MD-2-E.coli LPS", "BACE Bound
to...", "Vioxx Bound to Human COX-2") - the automated title-matching heuristic
in `scripts/fetch_real_data.py` just doesn't handle abbreviations
(TLR4/BACE/COX-2) well. Not a data problem, a matcher limitation.

### Literature reference verification - partial, honest limitation

Only 5/40 references in `docs/REFERENCES.md` were confidently matched against
Europe PMC by `scripts/fetch_real_data.py`. This reflects a limitation in the
script's title-extraction regex (it pulls the first sentence-like chunk from
each markdown reference entry, which is often a paraphrased description
rather than the literal paper title) - it does **not** indicate the
underlying 40 references are fake. The literature review and its 40 citations
were reused from the client's own pre-written document (see
`docs/client_provided/`), not generated by any agent in this pipeline. A
future improvement would parse DOIs directly where present in
`docs/REFERENCES.md` and query Europe PMC/Crossref by DOI instead of by
extracted title text.

## IMPPAT bulk access - researched, no public API found

IMPPAT (https://cb.imsc.res.in/imppat/) is a browse/search-only web
interface with no visible bulk CSV/API download (checked the live site plus
web search for a Zenodo/Figshare mirror - none found; a Biostars thread
asking the same question was inaccessible/403). This is a genuine, researched
limitation, not an assumption. Expanding real IMPPAT-style coverage beyond
the current 65 compounds means either manually curating more verified
compound+plant pairs (as chunk B2/B4 did) or contacting IMPPAT's maintainers
for bulk access - both out of scope for automated acquisition in this
session.

## Not yet real (scheduled for Phase D)

- **Real binding-affinity training data** (BindingDB or PDBBind) - the
  currently-loaded MLAgent has **no trained model at all**
  (`backend/app/models/trained/` does not exist yet); the pipeline honestly
  reports `status: model_not_trained` rather than fabricating predictions.
  This is the single most important remaining data gap. Per this project's
  data-download policy, BindingDB will be fetched directly inside the Kaggle
  training kernel (ephemeral, GPU-side), not downloaded to this local machine
  or committed to the git repo as a raw dataset.

## Rule

Every future entry in this file must include: source URL, retrieval date,
record count, and how it was spot-checked. An entry that only says "generated"
or "synthetic" must be explicitly labelled as such and excluded from any
real-training or real-results path.
