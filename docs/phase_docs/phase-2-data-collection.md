# Phase 2 — Data Collection, Segregation & Cleaning

**Status: Complete**, with one honestly-scoped gap (IMPPAT full-scale coverage — see
§2.6).

## Goal

Convert heterogeneous public resources into a clean, reproducible master dataset.

## 2.1 Primary Data Sources

| Source | Used for | Status |
|---|---|---|
| **IMPPAT** | Ayurvedic medicinal plants, phytochemicals, plant–compound relationships, traditional therapeutic information | Real, 65-record verified sample (see §2.6) |
| **PubChem** | Compound identifiers, canonical/isomeric SMILES, molecular formula, molecular weight | Real, live PUG-REST queries; 60/65 seed compounds have a PubChem-verified CID + SMILES |
| **RCSB PDB** | Protein structures, PDB identifiers, structural information | Real, 10 curated targets with real PDB IDs, resolutions, disease associations; real structures fetched live at docking time |
| **PubMed / Europe PMC** | Scientific literature, compound–target evidence | Real, 40-reference literature corpus (reused from the client-provided review) with live Europe PMC cross-referencing |
| TCMSP, TCMID | Complementary traditional-medicine resources (compounds, targets, herb–formula–target mappings) | Reviewed in the literature (`docs/LITERATURE_REVIEW_COMBINED.md` §3.2.B) as comparative context; not integrated as a live data source — this project's compound universe is Ayurveda-specific (IMPPAT-sourced), and TCM databases were judged out of scope for direct ingestion rather than silently substituted |

## 2.2 Data Segregation

Four logical datasets, matching the client's specified schema:

**Compound Dataset** (`backend/app/data/imppat_sample.json`) — compound ID
(`imppat_id`, format `IMP000001`–`IMP000065`), compound name, plant/source, source
database (IMPPAT), PubChem CID, SMILES, molecular formula, molecular weight, chemical
class, therapeutic information (traditional uses, Ayurvedic properties — rasa, guna,
virya, vipaka, dosha effect).

**Target Dataset** (`backend/app/data/proteins/targets.json`) — 10 real protein
targets, each with target ID, gene name, protein name, PDB ID, UniProt ID, organism,
resolution, method, disease associations, pathway, and binding-site coordinates.

**Literature Dataset** (`backend/app/data/literature_corpus/`) — 40 references
(reused from the client-provided literature review) with title, authors, year, DOI,
journal, and full text for 5 of them, indexed for retrieval.

**Docking Dataset** — generated at request time, not pre-stored: compound ID, target
ID, PDB ID, docking score, pose ID, binding-site information, and (as of this
session) real interaction features (hydrogen bonds, hydrophobic contacts, key
residues — see `phase-4-scientific-implementation.md` §4.5).

## 2.3 Data Cleaning — the real integrity finding and fix

The single most significant Phase 2 finding: the phytochemical seed data inherited
from the original project build was **fabricated at every level**, found by
systematically cross-checking every compound name against PubChem
(`scripts/fetch_real_data.py`, run in GitHub Actions):

- 80 of an original 100 records were placeholder entries with names like "Gallic
  acid derivative 20" — PubChem correctly returned `404 Not Found` for all 80.
- The remaining 20 "real"-named records **all had fabricated plant-source
  associations** — e.g. Withaferin A (unique to *Withania somnifera*) was falsely
  attributed to *Emblica officinalis*; `pubchem_cid` values were fabricated (Gallic
  acid was tagged CID 100000; its real CID, confirmed live via PubChem, is 370).
- `admet` and `bioactivity.predicted_targets` sub-objects had no real prediction
  tool behind them anywhere in the codebase.

**Fix applied**: the 80 fabricated records were dropped entirely. The genuinely real
compounds were re-sourced to their correct, verified botanical origin (cross-checked
against established pharmacognosy) with real PubChem CID/SMILES/molecular
formula/weight. 50 additional real, correctly-sourced phytochemicals were added with
SMILES/CID left honestly blank pending further enrichment, rather than hand-typing
chemical structures. Fabricated ADMET/bioactivity sub-objects were replaced with an
honest "not computed by any tool in this pipeline yet" note rather than deleted
silently.

**Result: 65 real records, 60 with a PubChem-verified CID + SMILES, 0 fabricated
associations.** Full detail, including the exact before/after for each affected
compound: `docs/DATA_PROVENANCE.md`.

Standard cleaning steps applied throughout: duplicate removal, SMILES validation
(RDKit parse check — real parse failures are logged and excluded, never
substituted), identifier mapping (compound name → PubChem CID → canonical SMILES),
cross-database entity resolution (IMPPAT name variants → a single canonical record),
and provenance retained for every record (source, retrieval date, verification
method).

## 2.4 Master Dataset

```text
Plants (41 real, verified)
   ↓
Phytochemicals (65 real records)
   ↓
Chemical Structures (60/65 with real PubChem CID + SMILES)
   ↓
Targets (10 real PDB-backed proteins)
   ↓
Protein Structures (fetched live from RCSB at docking time)
   ↓
Docking Results (real AutoDock Vina, or honestly-labelled empirical fallback)
   ↓
Interaction Features (real InteractionAnalysisAgent output, rule-based)
   ↓
ML Features (39-feature schema — see phase-3-training-benchmarking.md)
   ↓
Literature Evidence (40-reference corpus, RAG-retrieved)
```

## 2.5 Binding-affinity training data (a second, separate data-collection effort)

The compound/target/literature data above feeds the live application; a **separate**
real dataset — 181 real PDBBind v2013-core protein-ligand complexes with real
experimentally-measured binding affinities — was collected specifically for Phase 3
model training. Full detail in `phase-3-training-benchmarking.md` and
`docs/DATA_PROVENANCE.md`; the processed dataset is published publicly on Hugging
Face (`ayurvedic-affinity-training-data`).

## 2.6 Known, honest gap

65 records / 41 plants is still far short of IMPPAT's full catalogue (~9,600
phytochemicals / ~1,742 plants). No public bulk-download API was found for IMPPAT
after a real search (the live site is browse/search-only; a Biostars thread asking
the same question was inaccessible). Further expansion means either manually
curating more real, verified compound+plant pairs the same way this fix did, or
contacting IMPPAT's maintainers for bulk access — both out of scope for automated
acquisition in this project's timeline. This is reported as a scope limitation, not
hidden or padded with more placeholder data.

---
*Previous: [Phase 1 — Literature Review](phase-1-literature-review.md) · Next: [Phase 3 — Training & Benchmarking](phase-3-training-benchmarking.md)*
