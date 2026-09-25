/**
 * friendly.js — plain-language presentation layer.
 * Internal tier IDs / API shapes are unchanged; only what users SEE is translated here.
 * No jargon (SMILES, PDB, SHAP, docking, pharmacology...) may appear in visible copy.
 */

/** Internal tier id -> plain-language "Confidence Level" label */
export const CONFIDENCE_LEVELS = {
  DATABASE_DERIVED: {
    id: 'DATABASE_DERIVED',
    label: 'Plant library record',
    short: 'Library',
    icon: '🌿',
    color: '#0F5C4D',
    bg: 'bg-forest-50',
    blurb: 'Comes from our curated library of plants and natural compounds.',
    howCalculated: 'We look up the compound in our curated plant library (built from published plant-chemistry collections). No computer guessing is involved at this step — it is simply what is recorded about this plant and compound.',
  },
  DOCKING_RESULT: {
    id: 'DOCKING_RESULT',
    label: 'Shape fit',
    short: 'Fit',
    icon: '🧩',
    color: '#6D5BD0',
    bg: 'bg-violet-50',
    blurb: 'How snugly the compound appears to fit the protein shape.',
    howCalculated: 'The computer tries many orientations of the compound inside the 3D protein shape and scores how snugly it sits — like testing puzzle pieces. A stronger (more negative) score means a snugger fit. This is a computer guess about shape, not proof of any real-world effect.',
  },
  ML_PREDICTION: {
    id: 'ML_PREDICTION',
    label: 'Computer prediction',
    short: 'Prediction',
    icon: '✨',
    color: '#C2437F',
    bg: 'bg-pink-50',
    blurb: 'What our trained computer model predicts about binding strength.',
    howCalculated: 'A computer model trained on past examples looks at the compound\u2019s chemical pattern and predicts a strength score. We also check whether the compound is similar enough to past examples for the guess to be trustworthy (“inside its comfort zone”).',
  },
  XAI_INTERPRETATION: {
    id: 'XAI_INTERPRETATION',
    label: 'Why this result?',
    short: 'Why?',
    icon: '💡',
    color: '#C96F4A',
    bg: 'bg-orange-50',
    blurb: 'Which parts of the compound most influenced the prediction.',
    howCalculated: 'We ask the model to show its working: each chemical feature gets a credit or blame score for pushing the prediction up or down. This explains the model\u2019s reasoning — not how nature actually works.',
  },
  LITERATURE_DERIVED: {
    id: 'LITERATURE_DERIVED',
    label: 'Published research',
    short: 'Research',
    icon: '📖',
    color: '#2E8B57',
    bg: 'bg-forest-50',
    blurb: 'What published studies say about similar compounds.',
    howCalculated: 'We search a small library of published papers for related findings and summarise what they say, always showing the original sources. The summary never creates new findings — it only reflects what others published.',
  },
};

export function confidenceLevel(tierId) {
  return CONFIDENCE_LEVELS[tierId] || null;
}

/** Plain-language glossary used across pages */
export const PLAIN_WORDS = {
  matchStrengthLabel: 'Match strength',
  matchStrengthHint: 'Lower numbers mean a snugger shape fit (a computer guess, not proof).',
  chemicalIdLabel: 'Chemical ID',
  proteinShapeLabel: '3D protein shape',
  confidenceLevelLabel: 'Confidence level',
  whyResultLabel: 'Why this result?',
};

/** Friendly names for the protein shapes we analyse (internal codes kept for API calls) */
export const PROTEIN_SHAPES = [
  { code: '6LU7', name: 'Virus defence protein', hint: 'Studied in virus research', plantContext: 'Ashwagandha · Turmeric' },
  { code: '1P44', name: 'Swelling-related protein', hint: 'Linked to everyday swelling', plantContext: 'Turmeric · Ginger family' },
  { code: '2AZ5', name: 'Immune-signal protein', hint: 'Part of immune signalling', plantContext: 'Triphala · Amla' },
  { code: '4KIK', name: 'Cell-stress protein', hint: 'Involved in cell stress responses', plantContext: 'Ashwagandha · Haritaki' },
];

export function proteinShapeName(code) {
  return PROTEIN_SHAPES.find((p) => p.code === code)?.name || `Protein shape ${code}`;
}

/** Convert a raw kcal/mol fit score into a friendly 0–100 "match strength" meter */
export function fitScoreToMeter(affinity) {
  if (affinity == null || Number.isNaN(affinity)) return null;
  // typical range -4 (weak) .. -9 (strong)
  const clamped = Math.min(-3.5, Math.max(-9.5, affinity));
  return Math.round(((Math.abs(clamped) - 3.5) / 6) * 100);
}

export function fitVerdict(affinity) {
  if (affinity == null) return 'Not measured yet';
  if (affinity <= -8) return 'Very snug fit';
  if (affinity <= -7) return 'Snug fit';
  if (affinity <= -6) return 'Moderate fit';
  return 'Loose fit';
}

/** Shorten long chemical identifier strings for display */
export function shortChemicalId(smiles, len = 18) {
  if (!smiles) return 'Not shown';
  if (smiles.length <= len) return smiles;
  return `${smiles.slice(0, len)}…`;
}

/** Plain-word label + icon for a real interaction type (InteractionType enum
 * values from backend/app/core/docking/interactions.py: hbond, hydrophobic,
 * pi_stacking, pi_cation, salt_bridge, water_bridge, halogen_bond,
 * metal_complex). */
const INTERACTION_LABELS = {
  hbond: { icon: '🤝', label: 'Held' },
  hydrophobic: { icon: '💧', label: 'Snug' },
  pi_stacking: { icon: '🔶', label: 'Stacked' },
  pi_cation: { icon: '⚡', label: 'Charge-pulled' },
  salt_bridge: { icon: '🧂', label: 'Salt-linked' },
  water_bridge: { icon: '💦', label: 'Water-linked' },
  halogen_bond: { icon: '🧲', label: 'Halogen-linked' },
  metal_complex: { icon: '🔩', label: 'Metal-linked' },
};
export function interactionLabel(type) {
  return INTERACTION_LABELS[type] || { icon: '🔗', label: 'Touch' };
}

/** Friendly pipeline steps (internal layer ids i..vi unchanged) */
export const FRIENDLY_STEPS = [
  { id: 'i', name: 'Plant library', icon: '🌿', text: 'Look up the plant and compound in our library.' },
  { id: 'ii', name: 'Chemical check', icon: '⬡', text: 'Measure basic chemical properties.' },
  { id: 'iii', name: 'Shape fit test', icon: '🧩', text: 'Try the compound inside the protein shape.' },
  { id: 'iv', name: 'Strength prediction', icon: '✨', text: 'Predict how strongly it might hold on.' },
  { id: 'v', name: 'Why this result?', icon: '💡', text: 'Show which features mattered most.' },
  { id: 'vi', name: 'Research check', icon: '📖', text: 'Compare with published studies.' },
];
