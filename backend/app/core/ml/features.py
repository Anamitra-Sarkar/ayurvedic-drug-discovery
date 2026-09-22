"""
Feature Engineering: Docking + QSAR Descriptors Fusion
=======================================================
Implements feature fusion as per BACE1 study (R2 0.78 combined features)
and TLR4 study methodology.

Literature-inspired fusion:
- BACE1 hybrid model: docking scores + QSAR descriptors improved R2 from 0.59 (docking alone)
  to 0.78 (combined). We replicate that pattern.
- Ayurvedic phytochemicals: IMPPAT-derived molecules often violate Lipinski but
  have privileged scaffolds (flavonoids, terpenoids, alkaloids).

Feature Groups:
  1. Docking-derived (Tier 2 -> Tier 3 fusion): Vina affinity, ligand efficiency, etc.
  2. QSAR / physicochemical (RDKit-style, pure python fallback)
  3. Ayurvedic-specific: phytochemical class, traditional use embeddings (mock)
  4. Interaction fingerprints: H-bond, hydrophobic counts (from docking mock)
"""

from __future__ import annotations

import hashlib
import math
import re
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional, Any, Union
import numpy as np

# Optional RDKit - fallback to pure python descriptors if not available
try:
    from rdkit import Chem
    from rdkit.Chem import Descriptors, Lipinski, Crippen, rdMolDescriptors
    RDKIT_AVAILABLE = True
except ImportError:
    RDKIT_AVAILABLE = False


# Feature names - canonical order for model input
DOCKING_FEATURES = [
    "vina_affinity",              # kcal/mol, most important
    "ligand_efficiency",          # affinity / heavy atoms
    "intermolecular_energy",      # physics-inspired
    "torsional_energy",
    "desolvation_energy",
    "num_hbonds",
    "num_hydrophobic_contacts",
    "num_vdw_contacts",
    "electrostatic_score",
    "pocket_occupancy",           # fraction of pocket volume occupied
]

QSAR_FEATURES = [
    "molecular_weight",
    "logp",
    "hbd",
    "hba",
    "tpsa",
    "rotatable_bonds",
    "heavy_atom_count",
    "ring_count",
    "aromatic_ring_count",
    "fraction_csp3",
    "num_aliphatic_rings",
    "num_heterocycles",
    "formal_charge",
    "num_radical_electrons",
    "bertz_ct",                   # complexity descriptor
    "balaban_j",                  # topological
    "bcut2d_mwhi",                # Burden eigenvalue (mock in fallback)
    "qed_score",                  # drug-likeness
]

AYURVEDIC_FEATURES = [
    "phytochemical_class_flavonoid",
    "phytochemical_class_alkaloid",
    "phytochemical_class_terpenoid",
    "phytochemical_class_phenolic",
    "phytochemical_class_saponin",
    "phytochemical_class_tannin",
    "is_privileged_scaffold",     # e.g., curcumin-like, withanolide-like
    "traditional_use_score",      # heuristic based on IMPPAT frequency
    "ayurvedic_dosha_vata",
    "ayurvedic_dosha_pitta",
    "ayurvedic_dosha_kapha",
]

ALL_FEATURES = DOCKING_FEATURES + QSAR_FEATURES + AYURVEDIC_FEATURES

PHYTOCHEMICAL_PATTERNS = {
    "flavonoid": ["c1cc", "C2=C", "flavon", "c1ccc(O)c(O)"],
    "alkaloid": ["N", "n1", "C12CCN"],
    "terpenoid": ["CC(C)=C", "CC1=CCC", "isoprene"],
    "phenolic": ["c1ccc(O)cc1", "Oc1ccccc1"],
    "saponin": ["OC2OC", "saponin"],
    "tannin": ["tannin", "gallic"],
}


def _hash_smiles_features(smiles: str, n_bits: int = 12) -> List[float]:
    """
    Deterministic pseudo-descriptors from SMILES hash for fallback when RDKit absent.
    Ensures reproducibility for synthetic training without heavy deps.
    """
    h = hashlib.md5(smiles.encode()).hexdigest()
    # Convert hex to float vector in [0,1]
    vals = []
    for i in range(0, min(n_bits * 2, len(h)), 2):
        vals.append(int(h[i:i+2], 16) / 255.0)
    # Pad
    while len(vals) < n_bits:
        vals.append(0.5)
    return vals[:n_bits]


def compute_qsar_descriptors_fallback(smiles: str) -> Dict[str, float]:
    """
    Pure-python QSAR fallback when RDKit not available.
    Uses heuristics + hash-based pseudo-random but deterministic features.
    """
    # Basic parsing heuristics
    smiles = smiles.strip()
    # Count atoms approx
    heavy = len(re.findall(r"[A-Z][a-z]?|c|n|o|s", smiles))
    heavy = max(heavy, 1)
    # Estimate MW: ~13 per heavy atom avg + hydrogens
    mw_est = heavy * 13.0 + smiles.count("C") * 1.0
    # HBD/HBA heuristic
    hbd = smiles.count("O") + smiles.count("N")  # over-est but deterministic
    hba = smiles.count("O") + smiles.count("N") + smiles.count("F")
    # LogP heuristic
    logp = (smiles.count("C") - smiles.count("O") * 1.5 - smiles.count("N")) / 5.0 + 1.0
    # Rotatable bonds: count single bonds not in ring (approx)
    rot = smiles.count("-") + smiles.count("C-C")
    # Ring count: count ring digits
    rings = len(re.findall(r"\d", smiles)) // 2
    # Hash to get variation
    hvals = _hash_smiles_features(smiles, 18)

    return {
        "molecular_weight": max(100.0, mw_est + (hvals[0]-0.5)*100),
        "logp": max(-3.0, min(8.0, logp + (hvals[1]-0.5)*2)),
        "hbd": min(12, int(hbd * 0.5 + hvals[2]*3)),
        "hba": min(15, int(hba * 0.6 + hvals[3]*4)),
        "tpsa": 20.0 + hvals[4]*120.0,
        "rotatable_bonds": min(15, int(rot + hvals[5]*6)),
        "heavy_atom_count": heavy,
        "ring_count": max(0, min(6, rings + int(hvals[6]*2))),
        "aromatic_ring_count": max(0, min(4, int(hvals[7]*4))),
        "fraction_csp3": hvals[8],
        "num_aliphatic_rings": int(hvals[9]*3),
        "num_heterocycles": int(hvals[10]*3),
        "formal_charge": int((hvals[11]-0.5)*2),
        "num_radical_electrons": 0,
        "bertz_ct": 100.0 + hvals[0]*800.0,
        "balaban_j": 1.0 + hvals[1]*3.0,
        "bcut2d_mwhi": 10.0 + hvals[12]*8.0,
        "qed_score": max(0.1, min(0.95, 0.3 + hvals[13]*0.6)),
    }


def compute_qsar_descriptors_rdkit(smiles: str) -> Dict[str, float]:
    """
    RDKit-based descriptors when available.
    """
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return compute_qsar_descriptors_fallback(smiles)
    try:
        return {
            "molecular_weight": Descriptors.MolWt(mol),
            "logp": Crippen.MolLogP(mol),
            "hbd": Lipinski.NumHDonors(mol),
            "hba": Lipinski.NumHAcceptors(mol),
            "tpsa": rdMolDescriptors.CalcTPSA(mol),
            "rotatable_bonds": Lipinski.NumRotatableBonds(mol),
            "heavy_atom_count": Lipinski.HeavyAtomCount(mol),
            "ring_count": rdMolDescriptors.CalcNumRings(mol),
            "aromatic_ring_count": rdMolDescriptors.CalcNumAromaticRings(mol),
            "fraction_csp3": rdMolDescriptors.CalcFractionCSP3(mol),
            "num_aliphatic_rings": rdMolDescriptors.CalcNumAliphaticRings(mol),
            "num_heterocycles": rdMolDescriptors.CalcNumHeterocycles(mol),
            "formal_charge": Chem.rdmolops.GetFormalCharge(mol),
            "num_radical_electrons": Descriptors.NumRadicalElectrons(mol),
            "bertz_ct": Descriptors.BertzCT(mol),
            "balaban_j": Descriptors.BalabanJ(mol),
            "bcut2d_mwhi": (
                Descriptors.BCUT2D_MWHI(mol) if hasattr(Descriptors, 'BCUT2D_MWHI') else Descriptors.MolWt(mol) / 10.0
            ),
            "qed_score": Descriptors.qed(mol) if hasattr(Descriptors, 'qed') else 0.5,
        }
    except Exception:
        return compute_qsar_descriptors_fallback(smiles)


def compute_qsar_descriptors(smiles: str) -> Dict[str, float]:
    if RDKIT_AVAILABLE:
        return compute_qsar_descriptors_rdkit(smiles)
    else:
        return compute_qsar_descriptors_fallback(smiles)


def classify_phytochemical(smiles: str, traditional_uses: Optional[List[str]] = None) -> Dict[str, float]:
    """
    Ayurvedic-specific features.
    Uses SMILES pattern heuristics and traditional use frequency.
    """
    smiles_lower = smiles.lower()
    features = {}

    # Heuristic classification based on SMILES substrings
    h = _hash_smiles_features(smiles, 6)

    # Define deterministic mapping for 6 classes
    # Use hash to probabilistically assign but keep consistency
    classes = ["flavonoid", "alkaloid", "terpenoid", "phenolic", "saponin", "tannin"]
    for i, cls in enumerate(classes):
        # Check simple pattern or hash
        pattern_score = 0.0
        if cls == "flavonoid" and ("c1c" in smiles_lower and smiles_lower.count("o") >=2):
            pattern_score = 0.8 + h[i%len(h)]*0.2
        elif cls == "alkaloid" and ("n" in smiles_lower):
            pattern_score = 0.6 + h[i%len(h)]*0.4
        elif cls == "terpenoid" and (smiles_lower.count("c") >= 10):
            pattern_score = 0.5 + h[i%len(h)]*0.5
        else:
            pattern_score = h[i%len(h)] * 0.7

        # One-hot-ish but soft
        features[f"phytochemical_class_{cls}"] = 1.0 if pattern_score > 0.6 else 0.0
        # Ensure at least one class active for synthetic data
        if i == 0 and sum(features.values()) == 0:
            features[f"phytochemical_class_{cls}"] = 1.0

    # Privileged scaffold: curcumin (beta-diketone), withanolide (steroidal lactone) etc.
    privileged = 1.0 if ("C=CC(=O)" in smiles or "OC1C" in smiles or h[0] > 0.75) else 0.0
    features["is_privileged_scaffold"] = privileged

    # Traditional use score: based on frequency in IMPPAT mock
    if traditional_uses:
        features["traditional_use_score"] = min(1.0, len(traditional_uses)/5.0 + h[1]*0.3)
    else:
        features["traditional_use_score"] = 0.3 + h[1]*0.7

    # Dosha: Vata, Pitta, Kapha association (Ayurvedic nosology)
    # Mock deterministic mapping
    features["ayurvedic_dosha_vata"] = 1.0 if h[2] > 0.66 else 0.0
    features["ayurvedic_dosha_pitta"] = 1.0 if (0.33 < h[2] <= 0.66) else 0.0
    features["ayurvedic_dosha_kapha"] = 1.0 if h[2] <= 0.33 else 0.0

    return features


def compute_docking_features_mock(
    smiles: str,
    protein_target: str = "BACE1",
    docking_score: Optional[float] = None,
) -> Dict[str, float]:
    """
    Physics-inspired mock docking features when real Vina not available.
    Generates deterministic but plausible features from SMILES + target.

    Mirrors AutoDock Vina output semantics:
    - vina_affinity in [-12, -2] kcal/mol (more negative = better)
    - ligand efficiency = affinity / heavy_atoms
    - intermolecular + torsional decomposition
    """
    hvals = _hash_smiles_features(smiles + protein_target, 16)
    # Deterministic affinity: base -7 plus variation
    if docking_score is not None:
        affinity = float(docking_score)
    else:
        # Hash determines affinity in range -3 to -11
        affinity = -3.0 - (hvals[0] * 8.0)  # [-3, -11]
        # Adjust by QSAR: larger MW slightly better until 500, then worse
        qsar = compute_qsar_descriptors(smiles)
        mw = qsar["molecular_weight"]
        if mw < 500:
            affinity -= (mw/500.0)*1.5
        else:
            affinity += ((mw-500)/500.0)*0.5

    heavy = max(int(compute_qsar_descriptors(smiles)["heavy_atom_count"]), 1)
    le = affinity / heavy

    # Energy decomposition physics-inspired
    intermol = affinity * 0.85 + (hvals[1]-0.5)*1.0
    torsional = 0.2 + hvals[2]*1.5  # penalty for rotatable
    desolv = (hvals[3]-0.5)*2.0
    hbonds = int(hvals[4]*6)  # 0-6
    hydro = int(hvals[5]*10)
    vdw = int(hvals[6]*15 + 5)
    elec = (hvals[7]-0.5)*3.0
    occupancy = 0.3 + hvals[8]*0.7

    return {
        "vina_affinity": affinity,
        "ligand_efficiency": le,
        "intermolecular_energy": intermol,
        "torsional_energy": torsional,
        "desolvation_energy": desolv,
        "num_hbonds": hbonds,
        "num_hydrophobic_contacts": hydro,
        "num_vdw_contacts": vdw,
        "electrostatic_score": elec,
        "pocket_occupancy": occupancy,
    }


def compute_docking_features_real(
    vina_results: Dict[str, Any]
) -> Dict[str, float]:
    """
    Parse real Vina output dict into standardized features.
    Expected keys from docking agent: affinity, etc.
    """
    try:
        return {
            "vina_affinity": float(vina_results.get("affinity", vina_results.get("binding_affinity", -7.0))),
            "ligand_efficiency": float(vina_results.get("ligand_efficiency", vina_results.get("affinity", -7.0)/20.0)),
            "intermolecular_energy": float(vina_results.get("intermolecular_energy", vina_results.get("affinity", -7.0)*0.85)),
            "torsional_energy": float(vina_results.get("torsional_energy", 0.5)),
            "desolvation_energy": float(vina_results.get("desolvation_energy", 0.0)),
            "num_hbonds": float(vina_results.get("num_hbonds", vina_results.get("hbond_count", 2))),
            "num_hydrophobic_contacts": float(vina_results.get("num_hydrophobic_contacts", 5)),
            "num_vdw_contacts": float(vina_results.get("num_vdw_contacts", 10)),
            "electrostatic_score": float(vina_results.get("electrostatic_score", 0.0)),
            "pocket_occupancy": float(vina_results.get("pocket_occupancy", 0.6)),
        }
    except Exception:
        # Fallback
        return compute_docking_features_mock(vina_results.get("smiles", "CCO"), docking_score=vina_results.get("affinity"))


@dataclass
class FeatureEngineeringConfig:
    """Config for feature engineering pipeline"""
    use_docking: bool = True
    use_qsar: bool = True
    use_ayurvedic: bool = True
    normalize: bool = True
    impute_strategy: str = "median"  # for missing


class AyurvedicFeatureEngineer:
    """
    Main feature engineering class fusing docking + QSAR + Ayurvedic.

    BACE1 study inspiration: combined features R2 = 0.78 vs docking alone 0.59.
    Implementation ensures feature parity between training and inference.
    """

    def __init__(self, config: Optional[FeatureEngineeringConfig] = None):
        self.config = config or FeatureEngineeringConfig()
        self.feature_means_: Optional[Dict[str, float]] = None
        self.feature_stds_: Optional[Dict[str, float]] = None
        self.impute_values_: Dict[str, float] = {}
        self.fitted_ = False

    def extract_features(
        self,
        smiles: str,
        docking_result: Optional[Dict[str, Any]] = None,
        protein_target: str = "BACE1",
        traditional_uses: Optional[List[str]] = None,
    ) -> Dict[str, float]:
        """
        Extract fused feature vector for single molecule.

        Args:
            smiles: SMILES string
            docking_result: optional dict from docking agent with affinity etc.
            protein_target: target protein name
            traditional_uses: list of traditional Ayurvedic uses

        Returns:
            Dict of feature_name -> value in canonical order
        """
        fused: Dict[str, float] = {}

        # Docking
        if self.config.use_docking:
            if docking_result and ("affinity" in docking_result or "vina_affinity" in docking_result):
                dock_feats = compute_docking_features_real(docking_result)
            else:
                dock_feats = compute_docking_features_mock(smiles, protein_target, docking_score=None if docking_result is None else docking_result.get("affinity"))
            fused.update(dock_feats)

        # QSAR
        if self.config.use_qsar:
            qsar = compute_qsar_descriptors(smiles)
            fused.update(qsar)

        # Ayurvedic
        if self.config.use_ayurvedic:
            ayur = classify_phytochemical(smiles, traditional_uses)
            fused.update(ayur)

        # Ensure all features present
        for f in ALL_FEATURES:
            if f not in fused:
                fused[f] = 0.0

        return fused

    def featurize_batch(
        self,
        smiles_list: List[str],
        docking_results: Optional[List[Optional[Dict[str, Any]]]] = None,
        protein_targets: Optional[List[str]] = None,
    ) -> Tuple[np.ndarray, List[str]]:
        """
        Batch featurization -> numpy matrix.

        Returns:
            X: (n_samples, n_features)
            feature_names: ordered list
        """
        if docking_results is None:
            docking_results = [None]*len(smiles_list)
        if protein_targets is None:
            protein_targets = ["BACE1"]*len(smiles_list)

        rows = []
        for smi, dock, target in zip(smiles_list, docking_results, protein_targets):
            feat_dict = self.extract_features(smi, dock, target)
            row = [feat_dict.get(fn, 0.0) for fn in ALL_FEATURES]
            rows.append(row)

        X = np.array(rows, dtype=np.float32)
        # Impute NaN/Inf
        X = np.nan_to_num(X, nan=0.0, posinf=10.0, neginf=-10.0)
        return X, ALL_FEATURES

    def fit_scaler(self, X: np.ndarray, feature_names: List[str]) -> None:
        """
        Fit normalization statistics for inference-time scaling.
        """
        self.feature_means_ = {}
        self.feature_stds_ = {}
        for i, name in enumerate(feature_names):
            col = X[:, i]
            mean = float(np.mean(col))
            std = float(np.std(col) + 1e-8)
            self.feature_means_[name] = mean
            self.feature_stds_[name] = std
            # Impute median
            self.impute_values_[name] = float(np.median(col))
        self.fitted_ = True

    def transform(self, X: np.ndarray, feature_names: List[str]) -> np.ndarray:
        """
        Apply normalization if fitted.
        """
        if not self.fitted_ or not self.config.normalize:
            return X
        Xt = X.copy()
        for i, name in enumerate(feature_names):
            mean = self.feature_means_.get(name, 0.0)
            std = self.feature_stds_.get(name, 1.0)
            Xt[:, i] = (Xt[:, i] - mean) / std
        return Xt

    def fit_transform(self, X: np.ndarray, feature_names: List[str]) -> np.ndarray:
        self.fit_scaler(X, feature_names)
        return self.transform(X, feature_names)

    def get_feature_importance_groups(self) -> Dict[str, List[str]]:
        """Group features by type for XAI interpretation"""
        return {
            "docking": DOCKING_FEATURES,
            "qsar": QSAR_FEATURES,
            "ayurvedic": AYURVEDIC_FEATURES,
        }


# Convenience singleton
_default_engineer = AyurvedicFeatureEngineer()


def featurize_smiles(smiles: str, docking_result: Optional[Dict[str, Any]] = None) -> Tuple[np.ndarray, List[str]]:
    """
    Quick single-molecule featurization for external use.
    """
    X, names = _default_engineer.featurize_batch([smiles], [docking_result])
    return X[0], names
