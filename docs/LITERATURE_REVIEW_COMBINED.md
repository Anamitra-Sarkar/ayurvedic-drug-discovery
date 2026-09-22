LITERATURE REVIEW

AI-Driven Computational Pipeline for Ayurvedic Drug Discovery: Phytochemical Mining, Molecular Docking, and Explainable Binding Prediction

Bhumika Tewari · RCC Institute of Information Technology (RCCIIT), MAKAUT · Winter Project, 2026

2. Project Overview

This project develops an end-to-end computational platform for identifying and prioritising candidate therapeutic compounds from Ayurvedic and other traditional-medicine phytochemical sources. The platform integrates six functional layers: (i) curated phytochemical and traditional-medicine databases, (ii) cheminformatic molecular-structure processing, (iii) structure-based protein–ligand molecular docking, (iv) supervised machine learning for binding-affinity prediction, (v) explainable AI for interpreting those predictions, and (vi) scientific-literature mining via retrieval-augmented generation, coordinated by an agentic orchestration layer and surfaced through an interactive web interface with molecular visualisation and automated candidate ranking and reporting.

The explicit objective of the system is computational candidate prioritisation — narrowing a large space of Ayurvedic phytochemicals down to a short, evidence-labelled list worth further (wet-lab or clinical) investigation. It is not a claim of experimental validation, and it is not a claim that any candidate compound is clinically effective. This distinction, motivated directly by the literature reviewed in Section 3 (in particular the AYUSH-64 case study [3], where a computational prediction was later carried to a randomised controlled trial as a separate, subsequent step), is treated as a hard design constraint rather than a caveat appended after the fact: every output the system produces must be traceable to one of five explicit evidentiary tiers — database-derived information, molecular-docking result, machine-learning prediction, explainable-AI interpretation, or literature-derived/LLM-synthesised evidence — and no output may collapse two of these tiers into a single undifferentiated claim.

3. Literature Review

3.1 Purpose and Scope of the Review

Ayurveda, one of the oldest continuously practised systems of traditional medicine, encodes centuries of empirical therapeutic knowledge in polyherbal formulations whose mechanisms of action are, for the overwhelming majority of compounds, still uncharacterised at the molecular level. The convergence of open phytochemical databases, structure-based computational chemistry, machine learning, explainable AI, and large language model (LLM) tooling has created, for the first time, the technical preconditions for a reproducible, end-to-end computational pipeline that can prioritise Ayurvedic phytochemicals as drug candidates while remaining explicit about the evidentiary status of every claim it produces.

This review surveys the seven literature areas identified in the project scope — (A) computational Ayurvedic and traditional-medicine drug discovery, (B) phytoch

emical and traditional-medicine databases, (C) molecular docking and protein–ligand interaction analysis, (D) machine learning for bioactivity and binding-affinity prediction, (E) explainable AI in drug discovery, (F) large language models and retrieval-augmented generation (RAG) for scientific literature, and (G) agentic AI for computational drug-discovery workflows — and closes by synthesising the specific research and engineering gap the proposed pipeline is designed to fill. Sources were identified through targeted search of peer-reviewed journals (Scientific Reports, Journal of Cheminformatics, Nucleic Acids Research, PLOS ONE, ACS Omega, Expert Opinion on Drug Discovery, WIREs Computational Molecular Science, among others), PubMed/PMC, and, for the fastest-moving sub-areas (agentic AI, RAG), recent arXiv/bioRxiv preprints and industry technical reports, since peer-reviewed coverage of these two areas is still emerging as of 2026. Forty sources are cited; twenty of the most directly relevant are additionally organised into a structured literature matrix in Section 9.

3.2.A Computational Approaches to Ayurvedic and Traditional-Medicine Drug Discovery

Ayurvedic formulations are, by design, polyherbal and multi-target: a single formulation such as Triphala may contain over a hundred distinct bioactive constituents acting on dozens of protein targets simultaneously, a pattern fundamentally incompatible with the single-drug/single-target paradigm that dominates conventional pharmacology [2]. Network pharmacology (NP) — modelling bioactive–target–disease relationships as an interaction graph rather than a list of independent binding events — has consequently become the dominant computational lens for Ayurveda, treating polypharmacology as the object of study rather than a confound to be engineered away [2][4].

The Triphala case study is illustrative of what NP alone can show: mapping 174 bioactives across three constituent herbs (Emblica officinalis, Terminalia bellerica, Terminalia chebula) onto 44 shared targets and 78 associated diseases revealed a substantially denser bioactive–target interaction pattern for the combined formulation than for any single constituent herb, supporting the traditional claim of synergistic, rather than merely additive, therapeutic action [4]. A more recent and more computationally complete example integrates NP with molecular docking directly: a study of 63 anti-epileptic Ayurvedic herbs screened 349 drug-like phytochemicals against metabotropic glutamate receptor (mGluR) targets, using similarity to known DrugBank anti-epileptics as a validation heuristic, and reported eleven novel neuromodulator candidates and a further seventy-four phytochemicals with poly-pharmacological similarity to approved or clinical-trial compounds [5]. This NP-plus-docking design is the closest existing precedent to the pipeline proposed here, though it is confined to a single target class and does not incorporate a downstream, trained

machine-learning affinity model, an explainability layer, or automated literature-grounded validation.

A related strand of the literature tracks Ayurvedic formulations that have progressed from computational prediction toward clinical evaluation. AYUSH-64, a polyherbal formulation, was repurposed against COVID-19 using combined network pharmacology and molecular docking and was subsequently evaluated in an open-label randomised controlled trial as an adjunct to standard care, giving a rare, documented example of a computational hypothesis being carried through to a clinical evidence tier [3]. This progression is instructive for the present project mainly as a cautionary structural template: it underscores why every output of the proposed system must be explicitly labelled by evidentiary tier (database-derived, docking-derived, ML-predicted, literature-supported, or clinically validated) rather than presented as a single undifferentiated "result."

At the field level, a 2023 perspective on the future of Ayurveda-inspired drug discovery frames network pharmacology together with supercomputer-enabled virtual high-throughput screening, docking, and drug repurposing as the near-term direction of the field, and argues that synergistic-formulation discovery need not be confined to reformulating existing dosage forms but can extend to rationally designing new multi-component combinations [1]. A parallel and considerably larger body of work exists for Traditional Chinese Medicine: a 2026 bibliometric-style synthesis covering 7,288 publications from 2007–2025 documents a systematic shift in TCM research toward integrated network-pharmacology–AI–multi-omics workflows [6]. The scale and methodological maturity of this TCM literature relative to the comparatively sparse Ayurveda-specific computational literature is itself evidence of the gap this project addresses: the individual computational techniques required (NP, docking, ML, XAI, agentic orchestration) are well established, but their systematic, reproducible application to Ayurvedic phytochemical data specifically remains underexplored.

3.2.B Phytochemical and Traditional-Medicine Databases

The Indian Medicinal Plants, Phytochemistry And Therapeutics database (IMPPAT) is the primary open resource for this project's compound universe. The original release is a manually curated catalogue of 1,742 Indian medicinal plants, 9,596 phytochemicals, and 1,124 therapeutic uses, spanning 27,074 plant–phytochemical and 11,514 plant–therapeutic associations; the curation effort additionally yielded a non-redundant in silico chemical library with computed physicochemical, ADMET, and drug-likeness properties for every phytochemical, explicitly intended to support downstream virtual screening [7]. IMPPAT 2.0 expanded this curation base to more than one hundred books on traditional Indian medicine and over 7,000 published articles, and is described by its maintainers as the largest digital resource of its kind [8].

Because Ayurveda-specific databases are narrower in scope than their Traditional Chinese Medicine counterparts, this project's data pipeline treats TCM resources as complementary rather than substitutive sources, consistent with common practice in the network-pharmacology literature. The Traditional Chinese Medicine Systems Pharmacology database (TCMSP) covers all 499 herbs registered in the Chinese Pharmacopoeia, with 29,384 ingredients, 3,311 targets, and 837 associated diseases, together with twelve ADME-related properties (oral bioavailability, half-life, Caco-2 permeability, blood–brain-barrier permeability, and Lipinski's rule-of-five compliance, among others) [9]. The Traditional Chinese Medicine Integrated Database (TCMID) and its 2.0 revision provide a complementary herb–formula–ingredient–target–disease mapping oriented toward mechanism analysis and are routinely paired with TCMSP in published NP studies [10]. A newer, simplified resource, TCMSID, addresses a specific weakness of the older databases: most phytochemicals nominally present in a herb or formula are, in practice, low-abundance or pharmacologically inactive, diluting the mechanistic signal when all constituents are mapped indiscriminately; TCMSID's distinguishing feature is a function for extracting the pharmacologically "key" ingredients from a herb or formula rather than mapping every constituent equally [11].

For molecular structure resolution, PubChem remains the standard source of canonical/isomeric SMILES, molecular formulae, and unique compound identifiers, and RCSB PDB the standard source of experimentally resolved protein structures for docking targets, as reflected consistently across the network-pharmacology and docking literature surveyed above. A limitation that applies across all of the traditional-medicine databases reviewed here is that plant–phytochemical and herb–target associations are compiled primarily from literature mining and vary in curation depth and evidentiary strength; none of them provide experimentally measured binding affinities for Ayurvedic compounds at a scale sufficient for supervised machine learning. This is precisely why the proposed pipeline generates its own docking-derived affinity labels rather than relying solely on the databases' predicted-target annotations.

3.2.C Molecular Docking and Protein–Ligand Interaction Analysis

AutoDock Vina is the de facto standard open-source docking engine for structure-based virtual screening pipelines of this kind. Its empirical scoring function combines a modified Lennard-Jones term for van der Waals interactions with hydrogen-bonding, hydrophobic, and steric-complementarity terms, and the software is documented to be up to two orders of magnitude faster than its predecessor, AutoDock 4, while also improving pose-prediction accuracy [12]. The scoring function is explicitly engineered as a trade-off between physical accuracy and computational throughput suitable for large virtual-screening camp

aigns rather than as a precise free-energy calculator [12].

This trade-off is the central limitation the literature repeatedly returns to: docking search algorithms sample the conformational space of a ligand within a binding site reasonably well, but the resulting scores correlate only moderately with experimentally measured binding affinity, motivating a distinct line of rescoring research. DockingApp RF retrains a random-forest scoring function on a combination of intermolecular-interaction features, solvent-accessible surface area, and Vina's native energy terms, and — evaluated on the standard CASF-2013 and CASF-2016 benchmarks — achieves accuracy comparable to other state-of-the-art machine-learning and deep-learning scoring functions while remaining usable through a graphical interface aimed at non-expert users [13]. A separate hybrid scoring function, formed as a linear combination of the AutoDock and AutoDock Vina energy terms and trained on 2,412 PDBbind complexes with validation on a held-out 313-complex test set, likewise demonstrated a statistically significant improvement in correlation with experimental pKi values over either parent function alone [14]. Taken together, this body of work is the direct justification for this project's design decision to treat the raw Vina docking score as one input to a separately trained ML affinity model rather than as a final answer, and to report docking evidence and ML-predicted affinity as two distinct, separately labelled outputs.

For interaction-level analysis beyond a single scalar score, the Protein–Ligand Interaction Profiler (PLIP) provides fully automated, rule-based, atom-level detection of non-covalent interactions directly from a PDB-format complex, without requiring manual structure preparation, covering hydrogen bonds, hydrophobic contacts, π-stacking, π-cation interactions, salt bridges, water bridges, and halogen bonds, and producing both publication-ready diagrams and machine-parsable output files suitable for downstream automation [15]. The tool has been actively maintained and extended: a 2021 update added support for DNA and RNA complexes, and a 2025 update added protein–protein interaction detection, indicating the tool remains suitable for incorporation into a reproducible pipeline several years after its original release [15]. This is the specific tool selected for the project's Interaction Analysis Agent.

3.2.D Machine Learning for Bioactivity and Binding-Affinity Prediction

Across the 2025–2026 QSAR and binding-affinity literature, RDKit-computed molecular descriptors and fingerprints remain the dominant featurisation strategy, and tree-ensemble models — Random Forest, XGBoost, LightGBM, and ExtraTrees — remain consistently the strongest performing regressors and classifiers on the small-to-mid-sized, carefully curated datasets typical of this domain [16][17][19]. This is a directly relevant finding for the present project, whose Ayurvedic compound–target training dat

a will necessarily be modest in size relative to large public bioactivity databases such as ChEMBL.

Methodological rigour around small datasets is treated as a first-order concern rather than an afterthought in the recent literature. A binding-affinity study of Toll-like receptor 4 (TLR4) modulators, built on only 49 curated compounds with experimentally determined affinities, explicitly foregrounds data-leakage prevention and chemically-diverse train/test splitting as core methodological requirements, alongside rigorous statistical validation, precisely because naive random splitting on small, structurally similar compound sets systematically overstates model performance [16]. A Dual-Filter Feature Selection approach, which combines statistical filtering with machine-learning-derived feature importance to select a compact descriptor set, improved a LightGBM QSAR model for estrogen-receptor-alpha antagonists to a mean relative error of 0.0775, outperforming both feature-selection components used individually and a high-dimensional ChemBERTa learned-embedding baseline — evidence that carefully curated classical descriptors remain competitive with, and in some regimes superior to, learned molecular representations when training data is limited [17]. A large-scale benchmark on Factor Xa inhibitors, comparing 42 regression and 42 classification algorithms on 6,400 ChEMBL compounds encoded with 391 Mordred descriptors, found ExtraTreesRegressor (R² = 0.760, RMSE = 0.831) and XGBoostClassifier (accuracy 0.91, ROC-AUC 0.962) to be the most robust models, coupled with SHAP analysis identifying electrostatic, topological, and polar-surface descriptors as dominant contributors, and Williams-plot applicability-domain analysis confirming that most compounds fell within the model's reliable prediction space [19]. This combination — systematic algorithm benchmarking, SHAP-based feature attribution, and explicit applicability-domain checking — is adopted directly as the evaluation protocol for this project's binding-affinity model.

Comparative evidence on representation learning is more mixed than might be expected: testing XGBoost against embeddings from pretrained chemical/protein language models (BioT5+, GPT2, BERT) found LLM-derived embeddings performed comparably to classical RDKit descriptors on some ligand series but noticeably worse on others, particularly where ligands within a series were highly similar to one another — indicating that embedding-based features do not straightforwardly dominate descriptor-based features, and that the choice should be validated per target family rather than assumed [18]. Fusing structure-based docking features with ligand-based QSAR descriptors has also been shown to outperform either feature family alone: for BACE1 inhibitors relevant to Alzheimer's disease, a NuSVR model combining binding-interaction and QSAR features achieved R² = 0.78, compared with R² = 0.65 and 0.64 using binding or QSAR features individually [2

0], and automated machine learning combined with SHAP analysis has similarly been used to relate descriptor sets to serotonin-receptor subtype selectivity [21]. These findings jointly justify this project's architectural choice to fuse docking-derived interaction features with RDKit descriptors and Morgan fingerprints as joint input to the XGBoost affinity model, rather than treating docking and machine learning as sequential, independent stages.

3.2.E Explainable AI in Drug Discovery

SHAP (SHapley Additive exPlanations), a game-theoretic feature-attribution method, is the dominant post-hoc explainer used across essentially every tabular molecular-descriptor binding-affinity study surveyed in Section 5, providing both cohort-level (global) and single-compound (local) explanations [17][19][20][21]. Its widespread adoption reflects a broader consensus, documented in a comprehensive 2025 review of explainable AI applications across the drug-discovery pipeline — spanning molecular modelling, target identification, ADME prediction, clinical-trial design, and personalised medicine — that regulatory bodies including the FDA and EMA increasingly favour model evidence that can be interrogated and questioned over unexplained black-box outputs, particularly as such outputs carry more decision weight [23].

More recent methodological literature, however, treats SHAP/LIME-style attribution as necessary but insufficient on its own. One 2026 review argues explicitly that explainability in drug discovery is valuable only insofar as it improves decisions under uncertainty rather than functioning as a post-hoc rationalisation of an already-made prediction, and recommends grounding explanations causally — for instance through physics-informed constraints — rather than accepting attribution scores at face value [22]. A companion taxonomy-based survey goes further, warning that SHAP and LIME attributions can be actively misleading without additional safeguards, and recommending three concrete practices this project adopts: pairing explanations with bias-aware data splits (scaffold- or series-based rather than random splits), running robustness checks across chemically related compound series and controlled perturbations, and triangulating attributions across multiple explainer methods (for example, verifying that SHAP-flagged descriptors remain stable when cross-checked against integrated gradients or counterfactual explanations) before treating a flagged feature as chemically meaningful [24]. Independent empirical support for the value of multi-explainer triangulation comes from a stacked-ensemble regressor study in which SHAP and LIME jointly identified molecular-flexibility and steric-effect descriptors as the dominant predictors of activity, with the two methods' agreement used as informal corroboration of the finding's reliability [25].

Looking beyond the immediate scope of this project, a 2025 synthesis in WIREs Computational Molecular Science argues that th

e field is converging on neuro-symbolic and multimodal explainability architectures — combining graph neural networks for molecular structure, transformers for sequential or textual data, and symbolic/rule-based layers for mechanistic grounding — together with explicit uncertainty quantification, as the longer-term path toward regulatory-grade explainability [26]. This trajectory connects directly to this project author's broader, longer-horizon research interest in uncertainty-aware and calibrated AI systems, and is noted here as a natural extension of the present project's SHAP layer rather than part of its immediate deliverable. Throughout the literature, one distinction is stated with near-universal consistency and is adopted as a hard requirement for this project's own reporting: a SHAP explanation describes what a trained statistical model attended to when making a specific prediction, and is not, by itself, evidence of biological mechanism of action.

3.2.F Large Language Models and Retrieval-Augmented Generation for Scientific Literature

Large language models queried directly on drug-related scientific questions hallucinate at rates that are unacceptable for a research pipeline expected to produce citable claims. In one literature-mining benchmark, models without retrieval grounding fabricated or cited materially incorrect references in 40–60% of answers, while an otherwise comparable retrieval-augmented system produced zero hallucinated citations on the same task [27]. A more granular, purpose-built evaluation of a full RAG pipeline — Sentence-BERT dense retrieval, FAISS vector indexing, cross-encoder re-ranking, and a Llama 3.2 generator — measured on 150 curated drug-related question–answer pairs across ten commonly used medications, reported a reduction in hallucination rate from 47.8% to 12.3% (a 74.3% relative reduction), together with faithfulness improving from 0.52 to 0.87 and factual accuracy from 0.54 to 0.89 [28]. These are concrete, reproducible numbers that justify the specific architecture proposed in the project brief — chunked embeddings, a vector database, similarity search, and a generation step constrained to retrieved evidence — as an empirically supported design rather than a default choice.

The foundational premise of retrieval-augmented generation is that grounding a language model's output in retrieved passages both reduces hallucination, because the model is not required to reconstruct facts purely from parametric memory, and injects knowledge that may postdate or lie outside the model's training data; biomedical-specific follow-on work has since extended this to literature question-answering and clinical decision support, although comprehensive, standardised evaluation of RAG specifically in biomedicine remains an active and only partially resolved research question [29]. Applications more specific to computational chemistry demonstrate that RAG is already used on both the literature side and the molecule side

of a pipeline resembling the one proposed here: retrieval-augmented generative molecular design systems fuse retrieved exemplar molecules into a pretrained encoder–decoder architecture or use retrieved ligand references to steer a three-dimensional diffusion model, while retrieval-enhanced biomedical text models incorporate retrieved literature evidence directly into text generation via chunked cross-attention mechanisms [30]. At the scale a literature-mining agent would need to operate — a continuously growing PubMed/Europe PMC corpus — systems-level research on high-performance RAG for scientific corpora demonstrates that the design of the ingestion and indexing pipeline, not only the retriever/generator pairing itself, determines whether a scientific RAG system remains reliably grounded as the underlying corpus grows [31].

The design implication adopted for this project is direct: every claim generated by the Report Agent must carry an explicit, checkable evidence pointer (a PMID, DOI, or equivalent identifier) back to a retrieved passage, and the system must be able to represent and surface a "no supporting evidence found" state explicitly rather than allowing the underlying LLM to generate an unsupported claim by default — following precisely the mechanism shown above to be responsible for the measured reduction in hallucination rate.

3.2.G Agentic AI for Computational Drug-Discovery Workflows

A multi-agent system (MAS), as characterised in recent industry and academic literature, consists of multiple autonomous LLM-based agents, each configured with a distinct reasoning scope and access to domain-specific tools, coordinated under a shared orchestration layer to accomplish goals exceeding the capacity of any single model or single agent [32]. The cited DrugAgent framework illustrates this architecture concretely by separating planning from execution: an LLM Planner generates a high-level research strategy, and a separate LLM Instructor translates that strategy into executable, domain-aware machine-learning pipelines [32]. The same review flags an engineering risk of direct relevance to the present project's design: poorly coordinated multi-agent implementations propagate errors downstream, because an agent that receives a flawed input from an upstream stage will produce an output that is difficult to audit after the fact — a finding that directly motivates including an explicit Validation Agent as a distinct pipeline stage rather than chaining agents in a purely linear, unchecked sequence [32].

Case-study evidence of agentic systems specifically for literature-and-structure analysis in early drug discovery includes an orchestrator agent coordinating a Patent Extraction Agent, a Cross-reference Agent, and a Literature Retrieval Agent with shared memory for comprehensive asset evaluation, and a separate case study in which an orchestrator ran parallel sub-agent queries to assess a BTK-inhibitor candidate's target selectivity profile [33].

Both examples are structurally analogous to the Literature Agent / Compound Agent / Validation Agent decomposition specified in the project brief. At production scale, AstraZeneca's ChatInvent system is documented to have evolved from a single-agent proof-of-concept into an extensible, multi-agent architecture with a graphical interface for molecular design and synthesis planning, building on earlier pioneering agentic-chemistry systems — CoScientist, ChemCrow, and LLM-RDF — that first demonstrated LLMs could orchestrate cheminformatics tools and plan chemical reactions; notably, the authors report that real-world adoption challenges persist even after the system reached production use, which tempers expectations for how quickly a comparable academic pipeline can be made fully autonomous [34].

A directly comparable general-purpose framework, AgentD, is explicitly positioned in the literature against three narrower predecessors: CACTUS, which wraps an LLM around simple cheminformatics property calculators (molecular weight, LogP, TPSA, drug-likeness filters) but offers only a narrowly scoped toolset; SciToolAgent, which introduces a knowledge-graph-driven orchestration layer allowing an LLM to select from hundreds of scientific tools across domains; and DrugPilot, which focuses on orchestrating multi-stage discovery workflows via parameterised reasoning but is demonstrated primarily on established benchmark datasets rather than end-to-end molecular design [35]. The authors of this comparison observe that most existing computational drug-discovery methods remain task-specific and require manual orchestration by domain experts — precisely the fragmentation problem the present project's LangGraph-based agent layer (Literature, Compound, Molecular Preparation, Docking, Interaction Analysis, ML, XAI, Validation, and Report agents) is designed to resolve [35]. Finally, Tippy demonstrates a production-oriented five-agent architecture (Supervisor, Molecule, Lab, Analysis, and Report agents) wrapped with an explicit Safety Guardrail role around the Design-Make-Test-Analyze cycle, and is reported by its authors as the first production-ready specialised-agent system for that cycle [36]; while Tippy is oriented toward physical laboratory automation rather than a purely computational pipeline, its Safety-Guardrail-before-Report pattern is a direct template for the gating logic this project's own Validation Agent should implement before any candidate reaches the Report Agent.

No published agentic system, to the evidence surveyed here, yet targets the specific combination this project proposes: Ayurvedic/traditional-medicine phytochemical mining, structure-based docking, trained ML affinity prediction, SHAP-based explainability, and RAG-grounded literature validation, all coordinated within a single orchestrated, reproducible pipeline with explicit evidentiary labelling of every output.

4. Literature Review Matrix

The table below organises twenty of the mos

t directly relevant studies reviewed above (out of forty cited overall) into the structured matrix format requested in the project brief, spanning all seven literature areas. Bracketed numbers correspond to the numbered reference list in Section 6.

5. Research and Engineering Gap

Every individual computational stage required for the proposed pipeline is independently well precedented and, in most cases, independently validated in the recent literature: network pharmacology and docking for Ayurvedic and TCM formulations [1]–[6]; curated phytochemical databases with computed molecular properties [7]–[11]; docking engines and rescoring functions with quantified accuracy trade-offs [12]–[14]; automated protein–ligand interaction profiling [15]; tree-ensemble machine learning for binding-affinity and QSAR prediction with rigorous small-dataset methodology [16]–[21]; SHAP-based explainability with an increasingly well-defined validation protocol [22]–[26]; retrieval-augmented generation with measured, substantial reductions in hallucination for literature-grounded question answering [27]–[31]; and multi-agent orchestration frameworks for computational drug discovery, including at least one production-deployed industrial example [32]–[36]. Broader field-level reviews of AI in drug discovery [37][38][40] and at least one integrated machine-learning-plus-docking repurposing framework validated end-to-end on a real disease target [39] confirm that pairwise integrations (docking + ML, network pharmacology + docking, RAG + literature retrieval) are individually mature.

What the literature does not yet show, to the evidence surveyed here, is a single reproducible pipeline that chains all of these stages together for Ayurvedic phytochemicals specifically, with every output explicitly labelled by evidentiary tier rather than presented as an undifferentiated result. The project therefore investigates whether these currently separate computational components can be integrated into a single reproducible workflow:

Traditional Medicine Data  →  Phytochemical Mining  →  Molecular Processing  →  Target Identification  →  Molecular Docking  →  Binding Analysis  →  Machine Learning  →  Explainable AI  →  Scientific Literature Evidence  →  Agentic Validation  →  Candidate Prioritisation

Consistent with the evidentiary-labelling requirement established throughout the review above (Sections 3.2.A, 3.2.E, and 3.2.F in particular), the system must clearly distinguish, for every candidate compound, between five categories of evidence: experimental evidence (where it exists, e.g. from a cited in vitro or clinical study), published literature evidence (retrieved and cited via the RAG layer), docking-based computational evidence (the Vina score and PLIP-derived interaction profile), machine-learning predictions (the trained affinity model's output, with its SHAP explanation), and LLM-generated summaries (explicitly marked as syntheses of the above, never as new evidence in

themselves). The system must not, at any stage, present a computational prediction as clinical proof.

This is the concrete, literature-supported research and engineering gap the proposed AI-Driven Computational Pipeline for Ayurvedic Drug Discovery is designed to address: the constituent techniques reviewed in Section 3 exist and are individually validated; their systematic, transparently-labelled integration specifically for Ayurvedic phytochemical prioritisation does not yet exist in the published literature.

6. References

[1] Where lies the future of Ayurveda-inspired drug discovery? Expert Opinion on Drug Discovery, 18(9), 2023.

[2] Network Pharmacology Approach for Herbal Drugs Intended for the Therapy of Diseases: A Comprehensive Review.

[3] Ayurveda and in silico Approach: A Challenging Proficient Confluence for Better Development of Effective Traditional Medicine Spotlighting Network Pharmacology. Chinese Journal of Integrative Medicine, 2022.

[4] Network Pharmacology: An Emerging Technique for Natural Product Drug Discovery and Scientific Research on Ayurveda.

[5] Insights about multi-targeting and synergistic neuromodulators in Ayurvedic herbs against epilepsy: integrated computational studies on drug-target and protein-protein interaction networks. (PMC6646331).

[6] Network Pharmacology-Driven Sustainability: AI and Multi-Omics Synergy for Drug Discovery in Traditional Chinese Medicine. (PMC12298991), 2026.

[7] Mohanraj, K., Karthikeyan, B. S., Vivek-Ananth, R. P., et al. IMPPAT: A curated database of Indian Medicinal Plants, Phytochemistry And Therapeutics. Scientific Reports, 8, 4329, 2018. DOI: 10.1038/s41598-018-22631-z.

[8] IMPPAT 2.0 database resource. The Institute of Mathematical Sciences (IMSc), Chennai. cb.imsc.res.in/imppat/.

[9] Ru, J., Li, P., Wang, J., et al. TCMSP: a database of systems pharmacology for drug discovery from herbal medicines. Journal of Cheminformatics, 6, 13, 2014. DOI: 10.1186/1758-2946-6-13.

[10] Xue, R., Fang, Z., Zhang, M., et al. TCMID: Traditional Chinese Medicine integrative database for herb molecular mechanism analysis. Nucleic Acids Research, 41, D1089–D1095, 2013; Huang, L., Xie, D., Yu, Y., et al. TCMID 2.0: a comprehensive resource for TCM. Nucleic Acids Research, 46(D1), D1117–D1120, 2018.

[11] TCMSID: a simplified integrated database for drug discovery from traditional Chinese medicine. Journal of Cheminformatics, 2022. DOI: 10.1186/s13321-022-00670-z.

[12] AutoDock Vina's scoring function in ligand–receptor interactions; Autodock Vina Online documentation.

[13] DockingApp RF: A State-of-the-Art Novel Scoring Function for Molecular Docking in a User-Friendly Interface to AutoDock Vina. (PMC7765429), 2020.

[14] A New Scoring Function for Molecular Docking Based on AutoDock and AutoDock Vina, 2015.

[15] Salentin, S., Schreiber, S., Haupt, V. J., Adasme, M. F., Schroeder, M. PLIP: fully automated protein–ligand interaction profiler. Nucleic Acids Research, 43(W1), W443–W447, 2

015. DOI: 10.1093/nar/gkv315. Updates: PLIP 2021 (DOI: 10.1093/nar/gkab294) and PLIP 2025 (Schake, Bolz, et al., DOI: 10.1093/nar/gkaf361).

[16] Machine Learning-Driven Prediction of TLR4 Binding Affinity: A Comprehensive Molecular Feature Analysis for Drug Discovery. bioRxiv, 2025.

[17] Multi-objective QSAR prediction of ERα antagonists via SHAP-based interpretation. PLOS ONE, 2026.

[18] On Machine Learning Approaches for Protein–Ligand Binding Affinity Prediction. arXiv:2407.19073, 2025.

[19] Interpretable machine learning-driven QSAR modeling for coagulation factor X inhibitors: from molecular descriptors to predictive potency. (PMC12827418), 2026.

[20] Enhancing BACE1 Inhibitor Discovery with Machine Learning by Integrating Binding Interactions and QSAR Features. (PMC12740608), 2025.

[21] Integrated QSAR Models for Prediction of Serotonergic Activity: Machine Learning Unveiling Activity and Selectivity Patterns of Molecular Descriptors. (PMC10974160).

[22] Physics-inspired explainable AI for mechanistic and decision support in drug discovery. ScienceDirect, 2026.

[23] Explainable Artificial Intelligence: A Perspective on Drug Discovery. Pharmaceutics, 17(9), 1119, 2025. DOI: 10.3390/pharmaceutics17091119.

[24] Explainable AI methods for drug discovery: A survey of interpretability, metrics and mechanistic insight. ScienceDirect, 2026.

[25] Meta-Modeling with Drug Discovery Stack Regressor for Drug Discovery: An Explainable AI Perspective. PubMed, 2025.

[26] Lavecchia, A. Explainable Artificial Intelligence in Drug Discovery: Bridging Predictive Power and Mechanistic Insight. WIREs Computational Molecular Science, 2025. DOI: 10.1002/wcms.70049.

[27] Performance of Retrieval-Augmented Generation (RAG) on Pharmaceutical Documents. IntuitionLabs, 2025.

[28] Retrieval-Augmented Generation for Reducing Hallucinations in Drug-Related Question Answering Systems. Research Square, 2026.

[29] Xiong, G., et al. Benchmarking Retrieval-Augmented Generation for Medicine. arXiv:2402.13178, 2024.

[30] Retrieval-Augmented Generation for AI-Generated Content: A Survey (RAG for Science section, incl. RetMol and BIOREADER). arXiv:2402.19473, 2024.

[31] HiPerRAG: High-Performance Retrieval Augmented Generation for Scientific Insights. arXiv:2505.04846, 2025.

[32] Agentic AI in Pharma: Multi-Agent and Self-Driving Labs. Technology Networks, 2026.

[33] AI Agents in Drug Discovery. arXiv:2510.27130, 2025.

[34] Democratising real-world drug discovery through agentic AI. PubMed, 2025.

[35] Large Language Model Agent for Modular Task Execution in Drug Discovery (AgentD). Journal of Chemical Information and Modeling, 2026 / arXiv:2507.02925.

[36] Accelerating Drug Discovery Through Agentic AI: A Multi-Agent Approach to Laboratory Automation in the DMTA Cycle (Tippy). arXiv:2507.09023, 2025.

[37] Bridging traditional and contemporary approaches in computational medicinal chemistry: opportunities for innovation in drug discovery. PubMed, 2025.

[38] F

erreira, F. J. N., Carneiro, A. S. AI-Driven Drug Discovery: A Comprehensive Review. ACS Omega, 10(23), 23889–23903, 2025. DOI: 10.1021/acsomega.5c00549.

[39] Ahmed, F., Lee, J. W., Samantasinghar, A., et al. SperoPredictor: An Integrated Machine Learning and Molecular Docking-Based Drug Repurposing Framework With Use Case of COVID-19. Frontiers in Public Health, 2022. DOI: 10.3389/fpubh.2022.902123.

[40] AI-enabled drug and molecular discovery: computational methods, platforms, and translational horizons. Discover Molecules, Springer Nature, 2025.

Note on citation completeness: several 2025–2026 preprint and industry-report sources (agentic AI, RAG) are cited because peer-reviewed coverage of these fast-moving sub-areas is still emerging; these should be re-checked for peer-reviewed versions before final journal submission, and author/venue details completed from the original PDFs during the drafting stage.

Study | Year | Topic Area | Dataset / Source | Method | Main Result | Limitation | Relevance to This Project

Ayurveda-inspired drug discovery review [1] | 2023 | Ayurveda / NP | Field-wide literature | Review / perspective | Frames NP + virtual HTS + docking + repurposing as the field's near-term direction | Perspective piece; no primary data | Motivates end-to-end computational framing of the pipeline

Network pharmacology of Triphala [4] | 2015 | Ayurvedic formulation NP | Triphala (3 constituent herbs) | NP graph construction | 174 bioactives, 44 targets, 78 diseases; denser network for combined formulation than single herbs | No docking/ML validation of predicted bioactive–target links | Confirms polypharmacology rationale for multi-compound candidate ranking

Neuromodulators in anti-epileptic Ayurvedic herbs [5] | 2019 | Ayurveda NP + docking | 63 herbs / 349 phytochemicals | Integrated NP + molecular docking vs mGluR targets | 11 novel neuromodulator candidates; 74 phytochemicals similar to DrugBank anti-epileptics | Restricted to one target class (mGluRs / epilepsy) | Closest existing precedent to the proposed docking-and-ranking workflow

Ayurveda and in silico approach [3] | 2022 | Ayurveda in silico review | Literature incl. AYUSH-64 | Review, incl. clinical follow-up | Surveys in silico Ayurveda studies; AYUSH-64 progressed to an RCT | Reviewed studies mostly single-formulation, not pipeline-integrated | Supports evidentiary-tier labelling (computational vs clinical) adopted in this project

IMPPAT [7][8] | 2018 / ongoing | Phytochemical database | 1,742 plants / 9,596 phytochemicals | Manual curation + cheminformatics (ADMET, drug-likeness) | Largest open Indian medicinal-plant phytochemical resource with computed properties | Associations are literature-mined, not experimentally validated | Primary compound-source database for this project

TCMSP [9] | 2014 | TCM systems-pharmacology database | 499 herbs / 29,384 ingredients | Database + ADME property computation | Links ingredients to 3,311 targets and 837 diseases with 12

ADME properties | TCM-specific, not Ayurveda-specific | Complementary database for cross-tradition compound triangulation

TCMID / TCMID 2.0 [10] | 2013 / 2018 | TCM integrated database | Herbs, formulae, targets | Database (mechanism mapping) | Comprehensive herb–formula–ingredient–target–disease mapping | Many mapped constituents are low-abundance / inactive | Secondary compound/target source, paired with TCMSP

AutoDock Vina scoring function [12] | ongoing / est. lit. | Molecular docking engine | General protein–ligand complexes | Empirical scoring (modified Lennard-Jones + H-bond + hydrophobic + steric) | Up to ~100× faster than AutoDock4 with improved pose accuracy | Binding-affinity correlation with experiment only moderate | Selected as the primary docking engine for this project

DockingApp RF [13] | 2020 | Docking rescoring | CASF-2013 / CASF-2016 | Random-forest rescoring layered on Vina output | Accuracy comparable to state-of-the-art ML/DL scoring functions | Requires retraining/validation for new target classes | Template for an optional ML-rescoring layer atop Vina

Hybrid AutoDock/Vina scoring function [14] | 2015 | Docking scoring function | 2,412 PDBbind complexes (train) / 313 (test) | Linear combination of AutoDock + Vina energy terms | Statistically significant improvement in correlation with experimental pKi | Trained on a fixed historical PDBbind release | Justifies treating raw Vina score as a hypothesis, not a final affinity

PLIP [15] | 2015 (2021, 2025 updates) | Protein–ligand interaction profiling | PDB-format complexes | Rule-based, atom-level non-covalent interaction detection | Detects 7–8 interaction types without manual structure preparation | Rule-based, not a physics/energy-based method | Selected tool for the project's Interaction Analysis Agent

TLR4 binding-affinity ML study [16] | 2025 | ML / QSAR | 49 compounds, experimental affinities | Ensemble ML with leakage-aware, diversity-preserving splitting | Robust small-dataset methodology; explicit leakage prevention | Very small, target-specific dataset (n = 49) | Methodological template given similarly small Ayurvedic training sets

Interpretable QSAR for Factor Xa inhibitors [19] | 2026 | ML / QSAR + XAI | 6,400 ChEMBL compounds, 391 Mordred descriptors | 42-algorithm benchmark + SHAP + applicability domain | ExtraTrees R²=0.760; XGBoost classifier ROC-AUC=0.962 | Single-target scope (Factor Xa) | Evaluation-protocol template: benchmarking + SHAP + applicability domain

BACE1 inhibitor ML (docking + QSAR fusion) [20] | 2025 | ML + docking feature fusion | BACE1 ligand set | NuSVR combining binding-interaction and QSAR features | R²=0.78 combined vs R²=0.65 / 0.64 using either feature set alone | Single, Alzheimer's-specific target | Justifies fusing docking output with descriptor-based ML features

XAI methods for drug discovery survey [24] | 2026 | Explainable AI | Field-wide literature | Taxonomy + methodological review | Recommends bias-aware splits and mu

lti-explainer triangulation for trustworthy SHAP use | Survey; proposes no new predictive model | Defines the XAI validation protocol adopted in this project

RAG on pharmaceutical documents [27] | 2025 | LLM / RAG | Pharmaceutical literature QA | Comparative RAG vs non-RAG LLM | RAG: 0% hallucinated citations vs 40–60% for non-RAG systems | Single-domain benchmark | Justifies citation-grounded design of the Report Agent

RAG reducing hallucination in drug QA [28] | 2026 | LLM / RAG | 150 drug QA pairs, 10 medications | Sentence-BERT retrieval + FAISS + reranking + Llama 3.2 | Hallucination 47.8%→12.3%; faithfulness 0.52→0.87; accuracy 0.54→0.89 | Narrow QA-pair benchmark, not literature-scale retrieval | Concrete, reproducible performance target for the RAG evidence layer

RAG for AIGC survey — RAG for Science [30] | 2024 | LLM / RAG for molecular design & biomedical NLP | Molecular generation + biomedical text systems | Survey of RetMol, PromptDiff, BIOREADER | Establishes precedent for RAG on both molecule-generation and literature sides | Survey; underlying systems not evaluated on Ayurvedic data | Evidence that RAG is applicable to both the molecule and literature stages of the pipeline

Agentic AI in Pharma review [32] | 2026 | Agentic AI / multi-agent systems | Field-wide + DrugAgent case study | Review of multi-agent architectures | Defines the MAS design pattern; flags error-propagation risk in poorly coordinated pipelines | Perspective/industry review | Motivates an explicit, separate Validation Agent

AgentD [35] | 2026 | Agentic AI | Drug-discovery pipeline tasks | Modular LLM agent framework | Contrasts with CACTUS / SciToolAgent / DrugPilot; automates multi-task pipeline coordination | General-purpose; not integrated with literature/docking/XAI for traditional medicine | Closest general architectural analogue to the proposed LangGraph agent layer

Tippy [36] | 2025 | Agentic AI / lab automation | DMTA cycle | 5-agent architecture + Safety Guardrail | Reported as the first production-ready agentic system for the DMTA cycle | Oriented to physical lab automation, not computation-only pipelines | Template for the Report Agent and the safety/validation gating pattern

[DOCX page 1 image attached. Read this image directly to extract content.]

[DOCX page 2 image attached. Read this image directly to extract content.]

[DOCX page 3 image attached. Read this image directly to extract content.]

[DOCX page 4 image attached. Read this image directly to extract content.]

[DOCX page 5 image attached. Read this image directly to extract content.]

[DOCX page 6 image attached. Read this image directly to extract content.]

[DOCX page 7 image attached. Read this image directly to extract content.]

[DOCX page 8 image attached. Read this image directly to extract content.]

[DOCX page 9 image attached. Read this image directly to extract content.]

[DOCX page 10 image attached. Read this image directly to extract content.]

[DOCX page 11 image attached. Read this image directly to extract content.]

[DOCX page 12 image attached. Read this image directly to extract content.]

[DOCX page 13 image attached. Read this image directly to extract content.]

[DOCX page 14 image attached. Read this image directly to extract content.]