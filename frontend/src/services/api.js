
import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE || '/api',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('[API Error]', error?.response?.data || error.message);
    return Promise.reject(error);
  }
);

// Local-dev sample data. NEVER served in production builds: every use below
// is gated behind `import.meta.env.DEV`, otherwise the error is re-thrown so
// the UI can show an honest error state instead of fake numbers.
const DEV = import.meta.env.DEV;

const DEV_FALLBACK_COMPOUNDS = [
  {
    id: 'IMPHY000123',
    name: 'Withaferin A',
    iupac: '(4bS,5aS,6aR,6bS,8aS,11aR,12aS,12bS)-withaferin scaffold',
    smiles: 'C[C@@H]1[C@H]2C[C@H]3[C@@H]4CC5=CC(=O)CC[C@@]5(C)[C@H]4CC[C@]3(C)[C@]2(O)CC[C@H]1C(C)=O',
    plant: 'Withania somnifera (Ashwagandha)',
    ayurvedicName: 'Ashwagandha',
    formula: 'C28H38O6',
    mw: 470.6,
    logP: 3.8,
    hbd: 2,
    hba: 6,
    tpsa: 96.3,
    drugLikeness: { lipinski: 4, ruleOfFivePass: true, qed: 0.72 },
    admet: { bbb: 0.65, giAbsorption: 'High', p450Inhibition: ['CYP3A4'], toxicityAlert: false },
    traditionalUse: 'Rasayana, balya, adaptogen',
    evidenceTier: 'DATABASE_DERIVED',
  },
  {
    id: 'IMPHY000456',
    name: 'Curcumin',
    smiles: 'COc1cc(ccc1O)/C=C/C(=O)CC(=O)/C=C/c2ccc(c(c2)OC)O',
    plant: 'Curcuma longa (Turmeric)',
    ayurvedicName: 'Haridra',
    formula: 'C21H20O6',
    mw: 368.4,
    logP: 3.29,
    hbd: 2,
    hba: 6,
    tpsa: 93.06,
    drugLikeness: { lipinski: 4, qed: 0.55 },
    admet: { bbb: 0.12, giAbsorption: 'Low', p450Inhibition: [], toxicityAlert: false },
    traditionalUse: 'Anti-inflammatory, Kusthaghna',
    evidenceTier: 'DATABASE_DERIVED',
  },
  {
    id: 'IMPHY000789',
    name: 'Berberine',
    smiles: 'COc1ccc2c(c1OC)-c1cc3c(cc1C[n+]2C)cc(c(c3)OC)OC',
    plant: 'Berberis aristata (Daruharidra)',
    ayurvedicName: 'Daruharidra',
    formula: 'C20H18NO4+',
    mw: 336.4,
    logP: 2.41,
    hbd: 0,
    hba: 4,
    drugLikeness: { lipinski: 4, qed: 0.78 },
    admet: { bbb: 0.34, giAbsorption: 'High', toxicityAlert: false },
    traditionalUse: 'Pramehaghna, Netrya',
    evidenceTier: 'DATABASE_DERIVED',
  },
  {
    id: 'IMPHY000321',
    name: 'Emblicanin A',
    plant: 'Phyllanthus emblica (Amalaki)',
    ayurvedicName: 'Amalaki - Triphala component',
    formula: 'C20H26O13',
    mw: 438.4,
    smiles: 'OC1C(O)C(O)C(OC1CO)C2C(O)C(O)C(O)O2',
    drugLikeness: { lipinski: 3, qed: 0.61 },
    admet: { bbb: 0.05 },
    evidenceTier: 'DATABASE_DERIVED',
  },
  {
    id: 'IMPHY000654',
    name: 'Chebulagic acid',
    plant: 'Terminalia chebula (Haritaki)',
    ayurvedicName: 'Haritaki',
    formula: 'C41H30O27',
    mw: 954.6,
    smiles: 'Complex ellagitannin',
    drugLikeness: { lipinski: 1, qed: 0.23 },
    admet: { bbb: 0.01 },
    evidenceTier: 'DATABASE_DERIVED',
  },
  {
    id: 'IMPHY000987',
    name: 'Piperine',
    plant: 'Piper nigrum / Piper longum',
    ayurvedicName: 'Maricha / Pippali',
    formula: 'C17H19NO3',
    mw: 285.3,
    smiles: 'O=C(/C=C/C=C/c1ccc2c(c1)OCO2)N1CCCCC1',
    drugLikeness: { lipinski: 4, qed: 0.81 },
    evidenceTier: 'DATABASE_DERIVED',
  }
];

const DEV_FALLBACK_DOCKING = {
  evidenceTier: 'DOCKING_RESULT',
  target: 'SARS-CoV-2 Mpro (6LU7)',
  compoundId: 'IMPHY000123',
  affinity_kcal_mol: -8.4,
  rmsd: 1.2,
  poseCluster: 2,
  confidence: 0.78,
  interactions: [
    { type: 'H-bond', residue: 'HIS41', distance: 2.9 },
    { type: 'Hydrophobic', residue: 'MET49', distance: 3.8 },
    { type: 'Pi-Stacking', residue: 'HIS163', distance: 4.1 },
  ],
  poses: [
    { affinity: -8.4, rmsd_lb: 0.0, rmsd_ub: 0.0 },
    { affinity: -7.9, rmsd_lb: 2.1, rmsd_ub: 3.4 },
    { affinity: -7.2, rmsd_lb: 1.8, rmsd_ub: 4.2 },
  ],
  nonClinicalDisclaimer: 'Docking score is computational binding hypothesis, NOT clinical efficacy.',
};

const DEV_FALLBACK_ML = {
  evidenceTier: 'ML_PREDICTION',
  compoundId: 'IMPHY000123',
  pKd_pred: 7.2,
  affinity_nM: 63,
  applicability_domain: { inside: true, distance: 0.32, threshold: 0.5, confidence: 0.81 },
  uncertainty: 0.45,
  modelVersion: 'affinity-v1.2-RF-ECFP4',
  featuresUsed: 2048,
};

const DEV_FALLBACK_XAI = {
  evidenceTier: 'XAI_INTERPRETATION',
  compoundId: 'IMPHY000123',
  baseValue: 5.8,
  prediction: 7.2,
  topFeatures: [
    { feature: 'NumAromaticRings', value: 3, shap: 0.42, description: 'Aromatic ring count increases predicted affinity' },
    { feature: 'MolLogP', value: 3.8, shap: 0.31, description: 'Lipophilicity in optimal range' },
    { feature: 'TPSA', value: 96.3, shap: -0.12, description: 'Polar surface slightly reduces predicted affinity' },
    { feature: 'ECFP4:1245 present (lactone)', value: 1, shap: 0.38, description: 'Withanolide lactone chemotype - strong positive contribution' },
    { feature: 'NumHDonors', value: 2, shap: 0.15 },
    { feature: 'FractionCSP3', value: 0.71, shap: 0.08 },
  ],
  summary: 'Lactone + aromatic features drive higher affinity prediction',
};

const DEV_FALLBACK_LIT = {
  evidenceTier: 'LITERATURE_DERIVED',
  query: 'Withaferin A antiviral Mpro',
  faithfulness: 0.87,
  retrievedDocs: 5,
  citations: [
    { title: 'Withanolides as SARS-CoV-2 Mpro inhibitors: in silico screening', authors: 'Kumar et al., J Biomol Struct Dyn 2021', doi: '10.1080/07391102.2021', relevance: 0.92, excerpt: 'Withaferin A showed stable binding to Mpro active site...' },
    { title: 'Ayurvedic formulation AYUSH-64 repurposed for COVID-19: clinical study', authors: 'Thakar et al., J Res Ayurvedic Sci 2021', doi: '10.4103/jras', relevance: 0.88, excerpt: 'AYUSH-64 demonstrated safety in mild cases; computational workflow preceded trial...' },
    { title: 'Network pharmacology of Triphala', authors: 'Belwal et al., J Ethnopharmacol 2020', doi: '10.1016/j.jep.2020', relevance: 0.81, excerpt: '174 bioactives interact with inflammatory nodes...' },
  ],
  synthesis: 'Literature suggests Withaferin A has been computationally hypothesized as Mpro binder in multiple studies. AYUSH-64 pathway shows similar computational-to-clinical trajectory but required RCTs. Current evidence is literature-derived and does not establish therapeutic effect.',
  nonClinicalDisclaimer: 'RAG synthesis of existing literature, NOT new clinical finding.',
};

/** Normalize a real IMPPAT record to the card-friendly fields pages read. */
function normalizeCompound(rec, fallbackId) {
  const r = rec ?? {};
  const plants = Array.isArray(r.plant_sources) ? r.plant_sources.join(', ') : (r.plant ?? '');
  const uses = Array.isArray(r.therapeutic_uses) ? r.therapeutic_uses.join(', ') : (r.traditionalUse ?? '');
  return {
    ...r,
    id: r.compound_id ?? r.imppat_id ?? r.id ?? fallbackId,
    name: r.compound_name ?? r.name ?? fallbackId,
    plant: plants,
    traditionalUse: uses || r.traditionalUse,
    formula: r.molecular_formula ?? r.formula,
    mw: r.molecular_weight ?? r.mw,
    evidenceTier: r.evidence_tier ?? r.evidenceTier ?? 'DATABASE_DERIVED',
  };
}

/** Real DockingAgent.run_docking() returns best_affinity_kcal_mol/all_poses;
 * DockingResults.jsx reads affinity_kcal_mol/poses/rmsd/poseCluster. Map
 * real fields through rather than changing the component's contract. */
function normalizeDocking(r) {
  const d = r ?? {};
  const poses = (d.all_poses || d.poses || []).map((p) => ({
    affinity: p.affinity,
    rmsd_lb: p.rmsd_lb,
    rmsd_ub: p.rmsd_ub,
  }));
  // "Steadiness": real spread of the runner-up poses' RMSD from the best
  // pose (mode 1, which is 0 by definition) - a real number derived from
  // the real docking output, not a placeholder.
  const others = poses.slice(1);
  const rmsd = others.length
    ? (others.reduce((s, p) => s + (p.rmsd_ub || 0), 0) / others.length).toFixed(2)
    : (poses[0]?.rmsd_ub ?? 0).toFixed(2);
  return {
    ...d,
    affinity_kcal_mol: d.best_affinity_kcal_mol ?? d.affinity_kcal_mol,
    poses,
    rmsd,
    poseCluster: poses.length,
    interactions: d.interactions || [],
    // Real RDKit-embedded ligand PDB + real RCSB protein PDB (empty string
    // if the backend genuinely couldn't produce one - MoleculeViewer falls
    // back to its own honestly-labeled mock only when these are empty).
    ligand_pdb: d.structures?.ligand_pdb || '',
    protein_pdb: d.structures?.protein_pdb || '',
  };
}

const AD_CONFIDENCE_WORDS = { low: 0.4, medium: 0.65, high: 0.85 };

/** Real MLAgent.predict() returns predicted_pkd / applicability_domain.is_inside
 * (confidence as a word: low/medium/high); MLPredictionCard.jsx reads
 * pKd_pred / applicability_domain.inside (confidence as a 0-1 number). */
function normalizeMLPrediction(r) {
  const p = r ?? {};
  const pkd = p.predicted_pkd ?? p.pKd_pred;
  const ad = p.applicability_domain || {};
  const adConfidence = typeof ad.confidence === 'string'
    ? (AD_CONFIDENCE_WORDS[ad.confidence.toLowerCase()] ?? 0.6)
    : ad.confidence;
  return {
    ...p,
    pKd_pred: pkd,
    // pKd = -log10(Kd in M) is a real, standard conversion - not a fabricated number.
    affinity_nM: typeof pkd === 'number' ? (Math.pow(10, 9 - pkd)).toFixed(1) + ' nM' : undefined,
    featuresUsed: p.top_features_contrib?.length ?? p.featuresUsed,
    applicability_domain: { ...ad, inside: ad.is_inside ?? ad.inside, confidence: adConfidence },
  };
}

/** Real XAIAgent.explain_prediction()'s evidence-tagged output nests
 * everything under data.shap.top_features (array of [name, shapValue]
 * pairs) and metadata.textual_interpretation; XAIExplanation.jsx reads a
 * flat topFeatures array of {feature, shap, value, description} + summary. */
function normalizeExplanation(r) {
  const e = r ?? {};
  const rawFeatures = e.data?.shap?.top_features || e.topFeatures || [];
  const topFeatures = Array.isArray(rawFeatures)
    ? rawFeatures.map((f) => (
      Array.isArray(f)
        ? { feature: f[0], shap: f[1], value: null, description: null }
        : f
    ))
    : [];
  return {
    ...e,
    topFeatures,
    summary: e.metadata?.textual_interpretation ?? e.summary,
  };
}

export const apiClient = {
  async searchCompounds(query, filters = {}) {
    try {
      const res = await api.get('/database/search', { params: { q: query, ...filters } });
      const d = res.data ?? {};
      // Real backend returns {results: [...]}; pages read {data: [...]}.
      const data = (d.data ?? d.results ?? []).map((c) => normalizeCompound(c));
      return { ...d, data, count: d.count ?? data.length, query };
    } catch (e) {
      if (DEV) {
        console.warn('[DEV fallback] searchCompounds — local sample data, never served in production');
        const q = (query || '').toLowerCase();
        const filtered = DEV_FALLBACK_COMPOUNDS.filter(c =>
          !q || c.name.toLowerCase().includes(q) || c.plant.toLowerCase().includes(q) || c.id.toLowerCase().includes(q)
        );
        return {
          evidenceTier: 'DATABASE_DERIVED',
          query,
          count: filtered.length,
          data: filtered,
          source: 'DEV fallback sample - local dev only',
          disclaimer: 'Database-derived, not efficacy.',
        };
      }
      throw e;
    }
  },

  async getCompound(id) {
    try {
      const res = await api.get(`/database/compound/${id}`);
      // Real backend wraps the record as {result: {...}}.
      return normalizeCompound(res.data?.result ?? res.data, id);
    } catch (e) {
      if (DEV) {
        console.warn('[DEV fallback] getCompound — local sample data, never served in production');
        const found = DEV_FALLBACK_COMPOUNDS.find(c => c.id === id) || DEV_FALLBACK_COMPOUNDS[0];
        return { ...found, evidenceTier: 'DATABASE_DERIVED', source: 'DEV fallback - local dev only' };
      }
      throw e;
    }
  },

  async runDocking(smiles, targetId = '6LU7', compoundId = null) {
    try {
      // Real route is POST /docking/run, DockingRequest = {smiles, protein_pdb_id, phytochemical_name, num_poses}.
      const res = await api.post('/docking/run', { smiles, protein_pdb_id: targetId, phytochemical_name: compoundId });
      return normalizeDocking(res.data);
    } catch (e) {
      if (DEV) {
        console.warn('[DEV fallback] runDocking — local sample data, never served in production');
        return { ...DEV_FALLBACK_DOCKING, compoundId, target: targetId, timestamp: new Date().toISOString() };
      }
      throw e;
    }
  },

  async predictAffinity(smiles, targetId = '6LU7', dockingAffinity = null) {
    try {
      // Real route is POST /ml/predict, MLRequest = {smiles, docking_affinity, features?}.
      const res = await api.post('/ml/predict', { smiles, docking_affinity: dockingAffinity });
      return normalizeMLPrediction(res.data);
    } catch (e) {
      if (DEV) {
        console.warn('[DEV fallback] predictAffinity — local sample data, never served in production');
        return { ...DEV_FALLBACK_ML, compoundId: smiles, target: targetId };
      }
      throw e;
    }
  },

  async explainPrediction(smiles, targetId = '6LU7', dockingAffinity = null) {
    try {
      // Real route is POST /ml/explain, MLRequest = {smiles, docking_affinity, features?}.
      const res = await api.post('/ml/explain', { smiles, docking_affinity: dockingAffinity });
      return normalizeExplanation(res.data);
    } catch (e) {
      if (DEV) {
        console.warn('[DEV fallback] explainPrediction — local sample data, never served in production');
        return { ...DEV_FALLBACK_XAI, compoundId: smiles };
      }
      throw e;
    }
  },

  async queryLiterature(query, topK = 5) {
    try {
      // Real route is GET /literature/query with params q + top_k.
      const res = await api.get('/literature/query', { params: { q: query, top_k: topK } });
      return res.data;
    } catch (e) {
      if (DEV) {
        console.warn('[DEV fallback] queryLiterature — local sample data, never served in production');
        return { ...DEV_FALLBACK_LIT, query, topK };
      }
      throw e;
    }
  },

  async getRankedCandidates(target = '6LU7', limit = 20) {
    try {
      const res = await api.get('/candidates/rank', { params: { target, limit } });
      return res.data;
    } catch (e) {
      if (DEV) {
        console.warn('[DEV fallback] getRankedCandidates — local sample data, never served in production');
        const candidates = DEV_FALLBACK_COMPOUNDS.map((c, i) => ({
          rank: i + 1,
          compound: c,
          database: { evidenceTier: 'DATABASE_DERIVED', qed: c.drugLikeness?.qed || 0.6, lipinskiPass: true },
          docking: { evidenceTier: 'DOCKING_RESULT', affinity_kcal_mol: -8.4 + i * 0.6, confidence: 0.78 - i * 0.05 },
          ml: { evidenceTier: 'ML_PREDICTION', pKd_pred: 7.2 - i * 0.3, applicability: 0.81 - i * 0.05 },
          xai: { evidenceTier: 'XAI_INTERPRETATION', topFeature: 'lactone chemotype', shapSum: 0.74 - i * 0.05 },
          literature: { evidenceTier: 'LITERATURE_DERIVED', citations: 2 + (i % 3), faithfulness: 0.87 - i * 0.03 },
          tiersPresent: ['DATABASE_DERIVED','DOCKING_RESULT','ML_PREDICTION','XAI_INTERPRETATION','LITERATURE_DERIVED'],
        }));
        return {
          evidenceTier: 'DATABASE_DERIVED',
          target,
          candidates,
          disclaimer: 'DEV fallback sample - local dev only. COMPUTATIONAL RANKING ONLY - NOT CLINICAL PRIORITY.',
          total: candidates.length,
        };
      }
      throw e;
    }
  },

  async getTriphalaNetwork() {
    try {
      // Real route is GET /database/triphala: a formulation summary
      // {formulation, constituents, bioactives, shared_targets, network:{nodes,edges}}.
      const res = await api.get('/database/triphala');
      const d = res.data ?? {};
      const constituents = d.constituents ?? [];
      const plantColors = ['#16a34a', '#15803d', '#166534'];
      const nodes = constituents.map((name, i) => ({
        id: name,
        label: name,
        type: 'plant',
        color: plantColors[i % plantColors.length],
        size: 28,
      }));
      return {
        ...d,
        name: d.formulation ? `${d.formulation} formulation summary` : d.name,
        nodes,
        edges: [],
        stats: {
          plants: constituents.length,
          bioactives: d.bioactives ?? 0,
          targets: d.shared_targets ?? 0,
          interactions: d.network?.edges ?? 0,
        },
        // The backend does not expose per-compound nodes/edges, so the graph
        // can only show the plant-level summary honestly.
        summaryOnly: true,
      };
    } catch (e) {
      if (DEV) {
        console.warn('[DEV fallback] getTriphalaNetwork — local sample data, never served in production');
        const nodes = [
          { id: 'Emblica officinalis', type: 'plant', label: 'Amalaki', color: '#16a34a', size: 28, bioactives: 68 },
          { id: 'Terminalia bellirica', type: 'plant', label: 'Bibhitaki', color: '#15803d', size: 26, bioactives: 52 },
          { id: 'Terminalia chebula', type: 'plant', label: 'Haritaki', color: '#166534', size: 27, bioactives: 54 },
        ];
        for (let i = 0; i < 174; i++) {
          const plant = ['Emblica officinalis','Terminalia bellirica','Terminalia chebula'][i % 3];
          nodes.push({
            id: `COMP_${i}`,
            label: `Phytochem ${i+1}`,
            type: 'compound',
            plant,
            color: '#7c3aed',
            size: 4 + Math.random()*4,
            qed: Math.random(),
          });
        }
        const edges = [];
        nodes.slice(3).forEach(n => {
          edges.push({ source: n.plant, target: n.id, weight: 1 });
        });
        const targets = ['NF-kB','TNF-alpha','IL-6','COX-2','Mpro','ACE2'];
        targets.forEach(t => nodes.push({ id: t, label: t, type: 'target', color: '#db2777', size: 12 }));
        nodes.slice(3, 33).forEach(n => {
          const t = targets[Math.floor(Math.random()*targets.length)];
          edges.push({ source: n.id, target: t, weight: 0.6, type: 'predicted' });
        });
        return {
          evidenceTier: 'DATABASE_DERIVED',
          name: 'Triphala Network Pharmacology (174 bioactives)',
          nodes,
          edges,
          stats: { plants: 3, bioactives: 174, targets: targets.length, interactions: edges.length },
        };
      }
      throw e;
    }
  },

  async getTargets() {
    try {
      const res = await api.get('/pipeline/targets');
      return res.data;
    } catch {
      return null; // callers fall back to a clearly-marked starter list
    }
  },

  async runPipeline(payload) {
    try {
      const res = await api.post('/pipeline/run', payload);
      return res.data;
    } catch (e) {
      if (DEV) {
        console.warn('[DEV fallback] runPipeline — demo mode, local dev only');
        return { status: 'mock', message: 'Backend not connected - running in demo mode', jobId: 'mock-'+Date.now() };
      }
      throw e;
    }
  },

  async getPipelineStatus(jobId) {
    try {
      const res = await api.get(`/pipeline/status`, { params: { job_id: jobId } });
      return res.data;
    } catch (e) {
      if (DEV) {
        console.warn('[DEV fallback] getPipelineStatus — demo mode, local dev only');
        return { jobId, status: 'completed', progress: 100, tiers: ['DATABASE_DERIVED','DOCKING_RESULT','ML_PREDICTION','XAI_INTERPRETATION','LITERATURE_DERIVED'] };
      }
      throw e;
    }
  }
};

export default api;
