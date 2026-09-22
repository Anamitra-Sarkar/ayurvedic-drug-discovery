
/**
 * Evidence Tier Utilities - Central enforcement for 5-tier evidentiary system
 * HARD CONSTRAINT: Every output must map to one of FIVE tiers
 * AYUSH-64 Justification: computational prediction != clinical proof
 */

export const EVIDENCE_TIERS = {
  DATABASE_DERIVED: {
    id: 'DATABASE_DERIVED',
    label: 'Database-Derived',
    shortLabel: 'DB',
    color: '#0e7490',
    bg: 'bg-cyan-50',
    bgHover: 'hover:bg-cyan-100',
    border: 'border-cyan-200',
    text: 'text-cyan-800',
    badge: 'bg-cyan-700',
    icon: '🗄️',
    description: 'Curated phytochemical data from IMPPAT, PubChem, and traditional medicine databases. Verified botanical sources.',
    layer: 'Layer i: Curated Databases',
    ayush64Note: 'Like AYUSH-64 botanical composition data - foundational but not efficacy proof.',
    confidenceBasis: 'Database curation quality & cross-references',
  },
  DOCKING_RESULT: {
    id: 'DOCKING_RESULT',
    label: 'Docking Result',
    shortLabel: 'DOCK',
    color: '#7c3aed',
    bg: 'bg-violet-50',
    bgHover: 'hover:bg-violet-100',
    border: 'border-violet-200',
    text: 'text-violet-800',
    badge: 'bg-violet-600',
    icon: '🧬',
    description: 'Structure-based protein-ligand docking score (AutoDock Vina). Physics-inspired scoring function - predicts binding pose and affinity.',
    layer: 'Layer iii: Molecular Docking',
    ayush64Note: 'In-silico binding hypothesis; like AYUSH-64 initial target mapping - requires experimental validation.',
    confidenceBasis: 'Vina score + RMSD + pose clustering',
  },
  ML_PREDICTION: {
    id: 'ML_PREDICTION',
    label: 'ML Prediction',
    shortLabel: 'ML',
    color: '#db2777',
    bg: 'bg-pink-50',
    bgHover: 'hover:bg-pink-100',
    border: 'border-pink-200',
    text: 'text-pink-800',
    badge: 'bg-pink-600',
    icon: '🤖',
    description: 'Supervised ML binding-affinity prediction (pKd / ΔG). Trained on curated bioactivity data. Includes applicability domain check.',
    layer: 'Layer iv: Supervised ML',
    ayush64Note: 'Statistical inference from historical data; analogous to AYUSH-64 AI repurposing but not clinical efficacy.',
    confidenceBasis: 'Model uncertainty + applicability domain + training overlap',
  },
  XAI_INTERPRETATION: {
    id: 'XAI_INTERPRETATION',
    label: 'XAI Interpretation',
    shortLabel: 'XAI',
    color: '#ea580c',
    bg: 'bg-orange-50',
    bgHover: 'hover:bg-orange-100',
    border: 'border-orange-200',
    text: 'text-orange-800',
    badge: 'bg-orange-600',
    icon: '🔍',
    description: 'Explainable AI (SHAP) feature attributions for ML predictions. Highlights which chemotypes drive predicted affinity.',
    layer: 'Layer v: Explainable AI',
    ayush64Note: 'Interpretability of model reasoning; explains why model thinks compound may bind, not clinical mechanism proof.',
    confidenceBasis: 'SHAP consistency + feature stability',
  },
  LITERATURE_DERIVED: {
    id: 'LITERATURE_DERIVED',
    label: 'Literature-Derived',
    shortLabel: 'LIT',
    color: '#15803d',
    bg: 'bg-green-50',
    bgHover: 'hover:bg-green-100',
    border: 'border-green-200',
    text: 'text-green-800',
    badge: 'bg-green-700',
    icon: '📚',
    description: 'RAG-retrieved scientific literature + LLM synthesis. Includes faithfulness score, citation verification.',
    layer: 'Layer vi: Literature Mining (RAG)',
    ayush64Note: 'Context from prior studies; like AYUSH-64 literature justification - supportive, not conclusive for new indication.',
    confidenceBasis: 'Retrieval relevance + faithfulness + citation count',
  },
};

export const TIER_ORDER = ['DATABASE_DERIVED','DOCKING_RESULT','ML_PREDICTION','XAI_INTERPRETATION','LITERATURE_DERIVED'];

export function hasEvidenceTier(obj) {
  if (!obj) return false;
  return !!obj.evidenceTier && EVIDENCE_TIERS.hasOwnProperty(obj.evidenceTier);
}

export function enforceEvidenceTier(data, context='unknown') {
  if (!hasEvidenceTier(data)) {
    console.error(`[Evidence Enforcement] Missing tier at ${context}:`, data);
    throw new Error(`Evidence Tier Enforcement Violation at ${context}: All outputs must map to one of 5 tiers.`);
  }
  return data;
}

export function withEvidence(tierId, payload, meta={}) {
  if (!EVIDENCE_TIERS[tierId]) throw new Error(`Unknown tier: ${tierId}`);
  return {
    evidenceTier: tierId,
    tierMeta: EVIDENCE_TIERS[tierId],
    data: payload,
    timestamp: new Date().toISOString(),
    nonClinicalDisclaimer: 'COMPUTATIONAL PREDICTION ONLY - NOT CLINICAL PROOF. Requires experimental validation.',
    ...meta,
  };
}

export function getTier(tierId) { return EVIDENCE_TIERS[tierId] || null; }

export function getTierClasses(tierId) {
  const t = getTier(tierId);
  if (!t) return { bg:'bg-gray-50', border:'border-gray-200', text:'text-gray-700', badge:'bg-gray-500' };
  return { bg:t.bg, border:t.border, text:t.text, badge:t.badge, color:t.color };
}

export function getDisclaimerForTiers(tiersPresent) {
  const hasComputational = tiersPresent.some(t => ['DOCKING_RESULT','ML_PREDICTION','XAI_INTERPRETATION'].includes(t));
  if (hasComputational) {
    return {
      level:'warning',
      title:'Computational Hypothesis - Not Clinical Evidence',
      message:'These results are in-silico predictions (docking scores, ML affinity, XAI attributions). They do NOT constitute clinical proof of efficacy, safety, or therapeutic effect. Inspired by AYUSH-64 development pathway, all computational hypotheses require rigorous experimental and clinical validation per Ayurvedic pharmacology standards.',
    };
  }
  return {
    level:'info',
    title:'Evidence-Tiered Output',
    message:'All data explicitly labeled with provenance tier per AYUSH-64 justification framework.',
  };
}

export function containsClinicalClaim(text) {
  if (!text) return false;
  const banned = ['clinically proven','proves efficacy','demonstrates therapeutic effect','cures','treats disease','clinical proof','proven to treat','effective treatment for','approved drug','clinical efficacy confirmed'];
  const lower = text.toLowerCase();
  return banned.some(p => lower.includes(p));
}

export function computeRankedEvidenceSummary(candidate) {
  return {
    databaseScore: candidate.databaseScore || null,
    dockingScore: candidate.docking?.affinity_kcal_mol || null,
    mlScore: candidate.ml?.pKd_pred || null,
    xaiTopFeature: candidate.xai?.topFeatures?.[0]?.feature || null,
    literatureCount: candidate.literature?.citations?.length || 0,
    tiersPresent: Object.keys(candidate).map(k => candidate[k]?.evidenceTier).filter(Boolean),
    compositeComputational: null,
  };
}
