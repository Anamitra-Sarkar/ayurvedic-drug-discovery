# Client Delivery Guide - Ayurvedic Drug Discovery Pipeline

## For Bhumika Tewari - RCCIIT Winter Project 2026

This ZIP contains complete codebase, documentation, guides.

### What is Delivered

- **Whole codebase**: backend (FastAPI 6 layers agents), frontend (React 3Dmol.js), data (IMPPAT sample 100, proteins 10, literature 40, ML 500), models, examples, tests, Dockerfiles, docker-compose
- **Documentation of everything in detail**: README.md, PROJECT_OVERVIEW.md (Section 2 six layers hard constraint five tiers AYUSH-64 justification), ARCHITECTURE.md (six layers detailed), EVIDENTIARY_TIERS.md (five-category taxonomy enforcement), SETUP_GUIDE.md, USER_GUIDE.md, API_DOCUMENTATION.md, docs/LITERATURE_REVIEW_COMBINED.md (extended Section 2, 3.1, 3.2.A-G seven areas, Section 4 matrix 20 rows, Section 5 gap flow diagram taxonomy must not statement argued from literature, Section 6 references 40 entries), docs/PIPELINE_DIAGRAM.md, docs/LITERATURE_MATRIX.md, docs/RESEARCH_GAP.md, docs/REFERENCES.md
- **Guides inside ZIP**: SETUP_GUIDE.md, USER_GUIDE.md, API_DOCUMENTATION.md, CLIENT_DELIVERY_GUIDE.md (this), backend/README.md, frontend/README.md

### How to Present to Client / Evaluator

1. Show README.md first - six layers, five tiers, AYUSH-64 justification, pipeline flow diagram textual
2. Show PROJECT_OVERVIEW.md - Section 2 details
3. Show EVIDENTIARY_TIERS.md - five-category taxonomy, hard constraint enforcement, AYUSH-64 concrete not assertion, must not statement argued from literature [3][14][27][28][32]
4. Show docs/LITERATURE_REVIEW_COMBINED.md - reads as one continuous properly cross-referenced document rather than review bolted onto outline, renumbered matching original brief structure: 2 Project Overview six layers hard constraint five tiers AYUSH-64 case study concrete justification, 3 Literature Review 3.1 Purpose/Scope 3.2.A-G seven areas, 4 Matrix 20-row landscape table, 5 Gap includes actual pipeline flow diagram five-category evidence taxonomy explicit must not present computational prediction as clinical proof statement argued from literature rather than just copied from brief, 6 References 40-entry list
5. Show ARCHITECTURE.md - backend agents, frontend components, evidence enforcement across stack
6. Demo frontend: npm run dev -> Dashboard Triphala network 174 bioactives 44 targets 78 diseases [4] denser combined, AYUSH-64 card 4 plants Mpro 6LU7 open-label RCT adjunct [3], EvidenceTierLegend
7. Demo backend: uvicorn app.main:app --reload -> /docs Swagger, /api/pipeline/info flow diagram, /api/database/triphala, /ayush64
8. Run full pipeline: examples/sample_run.py --plant "Withania somnifera" --target 7E9G --top_n 10 -> outputs sample_output.json with all five tiers labeled, validation_report passed AYUSH-64 compliant
9. Show CandidateRankingTable.jsx: ranked list evidence tiers separated warning banner COMPUTATIONAL ONLY must not present as clinical proof
10. Show MoleculeViewer.jsx: 3Dmol.js viewer PDB protein SDF ligand stick sphere cartoon interactions watermark Computational Pose DOCKING_RESULT badge
11. Show tests: pytest tests/ -v evidence tier tests

### Key Points to Emphasize

- **Six functional layers integrated**: database IMPPAT primary [7][8] complementary TCMSP [9] TCMID [10], cheminformatics RDKit, docking Vina [12] 100x faster Hybrid pKi [14] RF rescoring [13] PLIP 7-8 types [15], ML fusion R2 0.78 [20] 42-alg ExtraTrees R2 0.760 XGB ROC-AUC 0.962 [19] leakage-aware n=49 [16], XAI triangulation [24], RAG 0% hallucinated vs 40-60% [27] 47.8%->12.3% faithful 0.52->0.87 [28] both sides [30], agentic MAS error-propagation risk [32] -> separate ValidationAgent AgentD [35] closest analogue Tippy safety guardrail [36]
- **Hard constraint enforced**: Every output traceable to one of five tiers DATABASE_DERIVED DOCKING_RESULT ML_PREDICTION XAI_INTERPRETATION LITERATURE_DERIVED, no output may collapse two tiers into single undifferentiated claim, must not present computational prediction as clinical proof, AYUSH-64 [3] concrete justification computational NP+docking Mpro 6LU7 -> open-label RCT adjunct separate subsequent step rare documented example, argued from literature not just copied from brief, compositeComputational = null principle
- **Triphala case**: 174 bioactives 44 shared targets 78 diseases denser combined than single [4] supports synergistic not additive
- **63 anti-epileptic herbs**: 63 herbs 349 drug-like phytochemicals mGluR targets 11 novel neuromodulator candidates 74 poly-pharmacological similarity [5] closest precedent confined single target class no downstream ML XAI literature validation -> gap evidence
- **IMPPAT**: 1,742 plants 9,596 phytochemicals 27,074 plant-phytochemical 11,514 plant-therapeutic associations non-redundant in silico library ADMET drug-likeness [7] IMPPAT 2.0 100+ books 7000+ articles largest digital resource [8]
- **TCM comparison**: 7,288 publications 2007-2025 systematic shift NP-AI-multi-omics [6] scale maturity TCM vs sparse Ayurveda evidence gap
- **Vina**: Empirical modified Lennard-Jones H-bond hydrophobic steric up to 100x faster than AutoDock4 improved pose accuracy [12] moderate correlation [14] justifies hypothesis not final
- **Engineering gap closed**: Systematic reproducible application Ayurvedic specifically underexplored, integration six layers + agentic orchestration LangGraph StateGraph checkpointing parallel, explicit five-tier taxonomy enforcement central module + frontend, ValidationAgent separate prevents error propagation [32], safety guardrail Tippy [36], RAG citation-grounded performance targets [27][28], fusion [20], leakage-aware [16], benchmark [19], Vina [12], hybrid [14], RF rescoring [13], PLIP [15], Triphala [4], 63 herbs [5], IMPPAT [7][8], web interface 3Dmol.js automated ranking reporting

### Setup for Client

See SETUP_GUIDE.md - pip install -r requirements.txt, npm install, uvicorn, vite, Docker.

No API keys required - all agents have fallback mock preserving tiers.

### Documentation Structure

- README.md: High-level six layers five tiers AYUSH-64 pipeline flow diagram literature summary gap references safety
- PROJECT_OVERVIEW.md: Section 2 six layers hard constraint AYUSH-64 justification detailed
- ARCHITECTURE.md: Backend layers detailed agents core data methods evidence API frontend stack components pages enforcement data flow deployment
- EVIDENTIARY_TIERS.md: Five tiers source content limitation implementation disclaimer example color hard constraint enforcement central module frontend enforcement AYUSH-64 justification concrete must not statement argued from literature compositeComputational null checklist
- SETUP_GUIDE.md: Prerequisites backend frontend full pipeline example Docker testing env troubleshooting performance notes
- USER_GUIDE.md: Dashboard search compound detail pipeline run candidate ranking documentation evidence tier badges safety interpretation guidelines export workflows Triphala synergy AYUSH-64 repurposing 63 herbs
- API_DOCUMENTATION.md: Root pipeline info health database Triphala AYUSH-64 docking scoring-info ML models explain literature query rag-info references pipeline run status targets schemas evidence enforcement errors frontend integration docs
- docs/LITERATURE_REVIEW_COMBINED.md: Extended document Section 2 Project Overview six layers hard constraint five tiers AYUSH-64 case study concrete justification not just assertion, Section 3 Literature Review 3.1 Purpose Scope 3.2.A-G all seven areas, Section 4 Matrix 20-row landscape table, Section 5 Gap includes actual pipeline flow diagram five-category evidence taxonomy explicit must not present computational prediction as clinical proof statement argued from literature rather than just copied from brief, Section 6 References 40-entry list, reads as one continuous properly cross-referenced document rather than review bolted onto outline
- docs/PIPELINE_DIAGRAM.md: Textual flow diagram mermaid diagram LangGraph orchestration evidence flow implementation files hard constraint integration
- docs/LITERATURE_MATRIX.md: 20-row landscape table dataset scale method key finding limitation relevance covers all 7 areas A-G
- docs/RESEARCH_GAP.md: Section 5 synthesis gap flow diagram taxonomy must not statement argued from literature engineering gap closed
- docs/REFERENCES.md: 40 entries
- CLIENT_DELIVERY_GUIDE.md: This guide

### ZIP Structure

See README.md project structure.

### Final Notes

- This is computational prioritization only, not experimental validation, not clinically effective claim
- Every output labeled by evidentiary tier
- Must not present computational prediction as clinical proof - AYUSH-64 [3] shows computational -> RCT as separate step
- CompositeComputational = null
- Ready for evaluation, demo, further wet-lab investigation

Bhumika Tewari RCCIIT MAKAUT Winter Project 2026
