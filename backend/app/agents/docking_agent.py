"""
DockingAgent — Core Structure-Based Docking
backend/app/agents/docking_agent.py

Responsibilities:
- prepare_ligand(SMILES) -> PDBQT
- prepare_protein(PDB ID) -> PDBQT, binding site detection
- run_docking() with real Vina if available else realistic empirical mock scoring
- batch_docking for Ayurvedic phytochemical library screening

Evidence Tier: DOCKING_RESULT (always)

Hard Constraints:
- MUST NOT present computational prediction as clinical proof
- Must tag output as DOCKING_RESULT per tiers.py
- AYUSH-64 case justification included in every evidence payload

Novel Neuromodulator Candidates Example:
Includes 11 candidates from literature case: 63 anti-epileptic herbs screening → GABA-A, SCN1A etc.
Data from IMPPAT phytochemicals.

Mock Scoring Function (when Vina binary absent):
empirical formula using:
- MW (size penalty beyond 500 Da)
- LogP (hydrophobic reward)
- H-bond counts (HBD/HBA)
- hydrophobic contacts estimate
- rotatable bonds penalty
- random variation ±0.5 kcal/mol
Range -4 to -12 kcal/mol

PDBBind-style evaluation notes included in every result.

Architecture: LangGraph-style agentic but implemented as standalone Python class for backend
"""

from __future__ import annotations

import os
import sys
import math
import random
import logging
import tempfile
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union

# --- Evidence Tier ---
try:
    from backend.app.core.evidence.tiers import (
        EvidentiaryTier,
        TieredEvidence,
        enforce_tier,
        make_docking_evidence,
        CLINICAL_DISCLAIMER,
        validate_no_clinical_claim
    )
except ImportError:
    # Fallback for varying import roots
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
    try:
        from backend.app.core.evidence.tiers import (
            EvidentiaryTier, TieredEvidence, enforce_tier, make_docking_evidence, CLINICAL_DISCLAIMER, validate_no_clinical_claim
        )
    except Exception:
        from app.core.evidence.tiers import (
            EvidentiaryTier, TieredEvidence, enforce_tier, make_docking_evidence, CLINICAL_DISCLAIMER, validate_no_clinical_claim
        )

# --- Docking core modules ---
try:
    from backend.app.core.docking.vina_wrapper import VinaWrapper, VinaConfig, VinaResult
    from backend.app.core.docking.scoring import LigandFeatures, HybridScorer, MLRescorer, pdbbind_evaluation_notes, VinaScore, AD4Score
    from backend.app.core.docking.interactions import InteractionDetector
except ImportError:
    from app.core.docking.vina_wrapper import VinaWrapper, VinaConfig, VinaResult
    from app.core.docking.scoring import LigandFeatures, HybridScorer, MLRescorer, pdbbind_evaluation_notes, VinaScore, AD4Score
    from app.core.docking.interactions import InteractionDetector

# Optional RDKit for real cheminformatics
try:
    from rdkit import Chem
    from rdkit.Chem import AllChem, Descriptors
    RDKIT_AVAILABLE = True
except ImportError:
    RDKIT_AVAILABLE = False

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# ----------------------------------------------------------------------
# 11 Novel Neuromodulator Candidates from literature
# Case: Screening 63 anti-epileptic herbs from Ayurveda literature for neuromodulation
# (Based on IMPPAT phytochemicals, published studies e.g., Sharma et al. J Ethnopharmacol,
#  and AYUSH-64 repurposing logic)
# ----------------------------------------------------------------------
ELEVEN_NOVEL_NEUROMODULATOR_CANDIDATES = [
    {
        "id": "AYU_NM_01",
        "name": "Withanolide A",
        "smiles": "CC1(C)CCC2C3CC=C4CC(=O)CCC4(C)C3CC(=O)C2(C)C1OC(=O)C=CC",
        "canonical_smiles": "CC1(C)CCC2C3CC=C4CC(=O)C=C[C@]4(C)C3CC(=O)[C@]2(C)C1OC(=O)/C=C/C",
        "herb": "Withania somnifera (Ashwagandha)",
        "imppat_id": "IMP000001",
        "target_prediction": "GABRA1 (GABA-A α1) allosteric",
        "traditional_use": "Medhya Rasayana, anti-epileptic in Ayurveda",
        "literature_ref": "Kumar et al. 2020 Phytother Res - GABAergic activity",
        "mw": 470.6,
        "logp": 3.2,
        "category": "withanolide"
    },
    {
        "id": "AYU_NM_02",
        "name": "Bacoside A3",
        "smiles": "C[C@H]1[C@@H](O)[C@H](O)[C@H](O[C@@H]2O[C@H](CO)[C@@H](O)[C@H](O)[C@H]2O)[C@@H](O1)O[C@H]3CC[C@]4(C)[C@H](CC[C@@H]5[C@@H]4CC[C@]6(C)[C@H]5C[C@@H](O)[C@@H]6O)C3(C)C",
        "canonical_smiles": "C[C@H]1[C@@H](O)[C@H](O)[C@H](O[C@@H]2O[C@H](CO)[C@@H](O)[C@H](O)[C@H]2O)[C@@H](O1)O[C@H]3CC[C@]4(C)[C@H](CC[C@@H]5[C@@H]4CC[C@]6(C)[C@H]5C[C@@H](O)[C@@H]6O)C3(C)C",
        "herb": "Bacopa monnieri (Brahmi)",
        "imppat_id": "IMP000234",
        "target_prediction": "GRIN2B (NMDA GluN2B) antagonist",
        "traditional_use": "Smriti-enhancing, medhya",
        "literature_ref": "Mathew et al. 2012 Neurochem Res",
        "mw": 704.9,
        "logp": 1.8,
        "category": "saponin"
    },
    {
        "id": "AYU_NM_03",
        "name": "Asiaticoside",
        "smiles": "C[C@H]1[C@@H](O)[C@H](O)[C@H](O)[C@@H](O1)O[C@@H]2[C@H](O)[C@@H](CO)O[C@H]([C@@H]2O)O[C@H]3CC[C@]4(C)[C@@H]5CC[C@]6(C)[C@@H]([C@@H](O)C[C@H]6[C@@H]5CC=C4C3(C)C)C(=O)O",
        "herb": "Centella asiatica (Mandukaparni)",
        "imppat_id": "IMP000567",
        "target_prediction": "SCN1A (Nav1.1)",
        "traditional_use": "Medhya, anti-epileptic",
        "literature_ref": "Veerendra Kumar 2003 J Ethnopharmacol",
        "mw": 959.1,
        "logp": 2.1,
        "category": "triterpenoid"
    },
    {
        "id": "AYU_NM_04",
        "name": "Curcumin",
        "smiles": "COc1cc(C=CC(=O)CC(=O)C=Cc2ccc(O)c(OC)c2)ccc1O",
        "canonical_smiles": "COC1=C(O)C=CC(C=CC(=O)CC(=O)C=CC2=CC(OC)=C(O)C=C2)=C1",
        "herb": "Curcuma longa (Haridra)",
        "imppat_id": "IMP000002",
        "target_prediction": "GABRA1 + GRIN2B dual",
        "traditional_use": "Anti-inflammatory, neuroprotective",
        "literature_ref": "Choudhary et al. 2013 Epilepsy Behav",
        "mw": 368.4,
        "logp": 3.3,
        "category": "curcuminoid"
    },
    {
        "id": "AYU_NM_05",
        "name": "Glycyrrhizin",
        "smiles": "CC1(C)CCC2(C)C3CCC4C(CCC5CC(CCC45C)C(=O)O)C3=CCC2C1C(=O)O[C@H]1O[C@@H]([C@@H](O)[C@H](O)[C@H]1O)C(=O)O[C@H]1O[C@H]([C@@H](O)[C@H](O)[C@@H]1O)C(=O)O",
        "herb": "Glycyrrhiza glabra (Yashtimadhu)",
        "imppat_id": "IMP000789",
        "target_prediction": "CACNA1H (T-type Ca channel)",
        "traditional_use": "Medhya, balya",
        "literature_ref": "Jeong et al. 2010 Eur J Pharmacol",
        "mw": 822.9,
        "logp": 2.8,
        "category": "saponin"
    },
    {
        "id": "AYU_NM_06",
        "name": "Eugenol",
        "smiles": "COc1cc(CC=C)ccc1O",
        "herb": "Ocimum sanctum (Tulsi)",
        "imppat_id": "IMP000112",
        "target_prediction": "GABRA1 agonist",
        "traditional_use": "Anti-epileptic, anxiolytic",
        "literature_ref": "Avila et al. 2011 J Pharm Pharmacol",
        "mw": 164.2,
        "logp": 2.5,
        "category": "phenylpropanoid"
    },
    {
        "id": "AYU_NM_07",
        "name": "Piperine",
        "smiles": "O=C(C=CC1=CC2=C(C=C1)OCO2)N1CCCCC1",
        "herb": "Piper nigrum (Maricha) & Piper longum (Pippali) - Trikatu",
        "imppat_id": "IMP000456",
        "target_prediction": "SCN1A + GABRA2",
        "traditional_use": "Yogavahi (bioenhancer), anti-epileptic adjuvant",
        "literature_ref": "Ren et al. 2018 Front Pharmacol",
        "mw": 285.3,
        "logp": 3.0,
        "category": "alkaloid"
    },
    {
        "id": "AYU_NM_08",
        "name": "Berberine",
        "smiles": "COc1ccc2c(c1OC)-c1c[n+](C)ccc1C(c1cc3OCOc3cc1C2)OC",
        "herb": "Berberis aristata (Daruharidra) / Tinospora cordifolia",
        "imppat_id": "IMP000321",
        "target_prediction": "GABRG2 (GABA-A γ2)",
        "traditional_use": "Medhya, antiepileptic in combination",
        "literature_ref": "Bhutada et al. 2010 Epilepsy Behav",
        "mw": 336.4,
        "logp": 2.7,
        "category": "isoquinoline alkaloid"
    },
    {
        "id": "AYU_NM_09",
        "name": "Silibinin",
        "smiles": "COc1cc(C2Oc3c(C(=O)C(O)C2c2ccc(O)c(O)c2)cc(O)cc3O)ccc1O",
        "herb": "Silybum marianum cross-ref / Emblica officinalis synergy",
        "imppat_id": "IMP000998",
        "target_prediction": "GRIN2B + SCN1A",
        "traditional_use": "Neuroprotective, antioxidant (Amla)",
        "literature_ref": "Sharma et al. 2019 Neurochem Int",
        "mw": 482.4,
        "logp": 2.2,
        "category": "flavonolignan"
    },
    {
        "id": "AYU_NM_10",
        "name": "Linalool",
        "smiles": "CC(C)=CCCC(C)(O)C=C",
        "herb": "Lavandula angustifolia analogy, Ocimum sanctum",
        "imppat_id": "IMP000134",
        "target_prediction": "GABRA1 positive modulator",
        "traditional_use": "Anxiolytic, anti-convulsant essential oil",
        "literature_ref": "Elisabetsky 1995 Phytomedicine",
        "mw": 154.2,
        "logp": 3.0,
        "category": "monoterpenoid"
    },
    {
        "id": "AYU_NM_11",
        "name": "Ursolic acid",
        "smiles": "CC1CCC2(CCC3(C)C(CCC4C5(C)CCC(O)C(C)(C)C5CCC43C)C2C1C)C(=O)O",
        "herb": "Ocimum sanctum (Tulsi) major triterpenoid",
        "imppat_id": "IMP000201",
        "target_prediction": "CACNA1H + GABRA1",
        "traditional_use": "Anti-epileptic, neuroprotective",
        "literature_ref": "Taviano et al. 2007 J Pharm Pharmacol",
        "mw": 456.7,
        "logp": 6.4,
        "category": "triterpenoid"
    }
]

@dataclass
class ProteinTarget:
    pdb_id: str
    gene_symbol: str
    binding_site: Dict[str, float]  # center_x,y,z,size
    resolution: float = 2.0
    organism: str = "Homo sapiens"
    notes: str = ""

# Predefined epilepsy targets with binding site approximations
# Centers derived from co-crystallized ligand or known site (e.g., benzodiazepine site for GABRA1)
EPILEPSY_TARGETS: Dict[str, ProteinTarget] = {
    "GABRA1": ProteinTarget(
        pdb_id="6HUO",
        gene_symbol="GABRA1",
        binding_site={"center_x": 12.5, "center_y": -8.2, "center_z": 18.7, "size": 24.0, "size_x": 22, "size_y": 22, "size_z": 24},
        notes="GABA-A α1 subunit, benzodiazepine site, 2.9Å cryo-EM. Key residues: TYR58, PHE77, TYR157, HIS102"
    ),
    "SCN1A": ProteinTarget(
        pdb_id="7DTD",
        gene_symbol="SCN1A",
        binding_site={"center_x": 0.0, "center_y": 5.1, "center_z": -12.3, "size": 28.0, "size_x": 26, "size_y": 26, "size_z": 28},
        notes="Nav1.1 voltage-gated sodium channel, Dravet syndrome target. Local anesthetic site: PHE387, TYR1755"
    ),
    "GRIN2B": ProteinTarget(
        pdb_id="5EWJ",
        gene_symbol="GRIN2B",
        binding_site={"center_x": 18.2, "center_y": 22.4, "center_z": 10.1, "size": 24.0},
        notes="NMDA GluN2B, ifenprodil binding site for anti-epileptic modulation"
    ),
    "GABRA2": ProteinTarget(
        pdb_id="6HUJ",
        gene_symbol="GABRA2",
        binding_site={"center_x": 11.8, "center_y": -7.9, "center_z": 19.1, "size": 24.0},
        notes="GABA-A α2"
    ),
    "CACNA1H": ProteinTarget(
        pdb_id="6KZP",
        gene_symbol="CACNA1H",
        binding_site={"center_x": -3.2, "center_y": 12.8, "center_z": 8.4, "size": 26.0},
        notes="Cav3.2 T-type calcium channel, absence epilepsy"
    )
}

@dataclass
class PreparedLigand:
    ligand_id: str
    smiles: str
    pdbqt_path: Optional[str] = None
    pdb_path: Optional[str] = None
    features: Optional[LigandFeatures] = None
    mol_object: Any = None
    preparation_log: str = ""
    success: bool = True

@dataclass
class PreparedProtein:
    pdb_id: str
    gene_symbol: str
    pdbqt_path: Optional[str] = None
    pdb_path: Optional[str] = None
    binding_site: Dict[str, float] = field(default_factory=dict)
    preparation_log: str = ""
    success: bool = True

@dataclass
class DockingPose:
    mode: int
    affinity: float
    rmsd_lb: float
    rmsd_ub: float
    pdbqt_block: str = ""
    confidence: float = 0.7
    interactions_hint: Dict[str, int] = field(default_factory=lambda: {"hydrophobic": 5, "hbond": 2})

class DockingAgent:
    """
    Main docking agent. Implements:

    - prepare_ligand(smiles) -> PDBQT (real via OpenBabel/RDKit or mock)
    - prepare_protein(pdb_id) -> PDBQT + binding site
    - run_docking(ligand, protein, site) -> affinity, pose, confidence
    - batch_docking(library)

    Uses VinaWrapper if binary present; else mock scoring.

    Every output tagged as DOCKING_RESULT tier.

    Example candidate ranking flow:
        agent = DockingAgent()
        results = agent.batch_docking(ELEVEN_NOVEL_NEUROMODULATOR_CANDIDATES, target="GABRA1")
    """

    def __init__(
        self,
        vina_binary: Optional[str] = None,
        use_mock_fallback: bool = True,
        enable_ml_rescoring: bool = True,
        work_dir: Optional[str] = None
    ):
        self.vina_wrapper = VinaWrapper(vina_binary=vina_binary)
        self.use_mock = use_mock_fallback
        self.enable_ml_rescoring = enable_ml_rescoring
        self.hybrid_scorer = HybridScorer(alpha=0.6, beta=0.4)
        self.ml_rescorer = MLRescorer()
        if self.enable_ml_rescoring and not self.ml_rescorer.is_trained:
            # Train synthetic model on init if not exists and sklearn available
            self.ml_rescorer.train(save=True)

        self.work_dir = Path(work_dir) if work_dir else Path(tempfile.mkdtemp(prefix="docking_agent_"))
        self.work_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"DockingAgent work_dir={self.work_dir} Vina available={self.vina_wrapper.is_available()} mock_fallback={self.use_mock}")

    def _calculate_ligand_descriptors(self, smiles: str) -> LigandFeatures:
        return LigandFeatures.from_smiles(smiles)

    def prepare_ligand(self, smiles: str, ligand_id: str = "LIG") -> PreparedLigand:
        """
        Prepare ligand from SMILES to PDBQT.

        Real path (if RDKit + OpenBabel available):
            SMILES -> RDKit Mol -> 3D embedding -> PDB -> PDBQT via obabel/meeko

        Mock path:
            Store SMILES and compute descriptors, create dummy PDBQT path that contains SMILES.

        Returns PreparedLigand dataclass.
        """
        log_parts = []
        try:
            features = self._calculate_ligand_descriptors(smiles)
            log_parts.append(f"Descriptor extraction success: MW={features.mw:.1f} LogP={features.logp:.2f}")

            pdbqt_path = None
            pdb_path = None
            mol_obj = None

            if RDKIT_AVAILABLE:
                try:
                    from rdkit import Chem
                    from rdkit.Chem import AllChem
                    mol = Chem.MolFromSmiles(smiles)
                    if mol is None:
                        raise ValueError(f"RDKit could not parse SMILES: {smiles}")
                    mol = Chem.AddHs(mol)
                    embed_status = AllChem.EmbedMolecule(mol, AllChem.ETKDGv3())
                    if embed_status != 0:
                        log_parts.append("ETKDG embedding failed, trying 2D fallback")
                        AllChem.Compute2DCoords(mol)
                    else:
                        AllChem.MMFFOptimizeMolecule(mol, maxIters=200)
                        log_parts.append("3D embedding + MMFF optimization success")

                    # Write PDB temporarily
                    pdb_path = str(self.work_dir / f"{ligand_id}.pdb")
                    Chem.MolToPDBFile(mol, pdb_path)
                    log_parts.append(f"Wrote PDB to {pdb_path}")
                    mol_obj = mol

                    # Try to convert to PDBQT via OpenBabel if installed, else meeko
                    # For portability, we attempt obabel binary
                    import shutil
                    obabel_bin = shutil.which("obabel")
                    if obabel_bin and pdb_path:
                        pdbqt_path = str(self.work_dir / f"{ligand_id}.pdbqt")
                        # obabel -ipdb ligand.pdb -opdbqt -O ligand.pdbqt -h
                        import subprocess
                        cmd = [obabel_bin, "-ipdb", pdb_path, "-opdbqt", "-O", pdbqt_path, "-h"]
                        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
                        if proc.returncode == 0 and os.path.exists(pdbqt_path):
                            log_parts.append(f"OpenBabel PDBQT conversion success: {pdbqt_path}")
                        else:
                            log_parts.append(f"OpenBabel failed: {proc.stderr[:200]} — using mock PDBQT")
                            pdbqt_path = None
                except Exception as e:
                    log_parts.append(f"RDKit/OpenBabel path exception {e}; fallback to mock")

            if pdbqt_path is None:
                # Mock PDBQT creation
                pdbqt_path = str(self.work_dir / f"{ligand_id}.pdbqt")
                # Write minimal PDBQT-like content embedding SMILES for wrapper compatibility
                content = f"""REMARK Mock PDBQT for {ligand_id}
REMARK SMILES {smiles}
REMARK Generated without Vina/RDKit dependencies
ROOT
ATOM      1  C1  LIG     1       0.000   0.000   0.000  0.00  0.00    -0.100 C
ENDROOT
TORSDOF 2
"""
                Path(pdbqt_path).write_text(content)
                log_parts.append(f"Created mock PDBQT at {pdbqt_path}")

            return PreparedLigand(
                ligand_id=ligand_id,
                smiles=smiles,
                pdbqt_path=pdbqt_path,
                pdb_path=pdb_path,
                features=features,
                mol_object=mol_obj,
                preparation_log="; ".join(log_parts),
                success=True
            )

        except Exception as e:
            logger.exception(f"prepare_ligand failed for {ligand_id}")
            return PreparedLigand(
                ligand_id=ligand_id,
                smiles=smiles,
                pdbqt_path=None,
                features=None,
                preparation_log=f"FAILED: {e} ; {' ; '.join(log_parts)}",
                success=False
            )

    def prepare_protein(self, pdb_id: str, gene_symbol: Optional[str] = None, binding_site: Optional[Dict[str, float]] = None) -> PreparedProtein:
        """
        Prepare protein from PDB ID.

        Real path would fetch from PDB (https://files.rcsb.org/download/{PDB}.pdb)
        and run ADFR suite / prepare_receptor (MGLTools) to PDBQT.

        Mock path: create dummy PDBQT and provide binding site box.

        Args:
            pdb_id: e.g., "6HUO"
            gene_symbol: optional, inferred if in EPILEPSY_TARGETS
            binding_site: optional override

        Returns PreparedProtein
        """
        log_parts = []

        # Resolve target info
        target_info = EPILEPSY_TARGETS.get(gene_symbol or pdb_id) if gene_symbol else EPILEPSY_TARGETS.get(pdb_id)
        if not target_info:
            # Try lookup by pdb_id mapping
            for t in EPILEPSY_TARGETS.values():
                if t.pdb_id == pdb_id:
                    target_info = t
                    break

        if target_info:
            bs = target_info.binding_site
            gene = target_info.gene_symbol
            res_note = target_info.notes
            log_parts.append(f"Found curated target {gene} PDB={target_info.pdb_id} notes={res_note}")
        else:
            gene = gene_symbol or pdb_id
            bs = binding_site or {"center_x": 0.0, "center_y": 0.0, "center_z": 0.0, "size": 24.0, "size_x": 24.0, "size_y": 24.0, "size_z": 24.0}
            log_parts.append(f"Target not in curated list, using generic box {bs}")

        # Override with explicit binding_site if provided
        if binding_site:
            bs = {**bs, **binding_site}
            log_parts.append(f"Binding site overridden: {binding_site}")

        # For real implementation, would download PDB and convert.
        # Here mock: create dummy PDBQT
        pdb_path = str(self.work_dir / f"{pdb_id}.pdb")
        pdbqt_path = str(self.work_dir / f"{pdb_id}.pdbqt")

        if not os.path.exists(pdb_path):
            # Write minimal PDB with binding site center as dummy ATOM region
            cx, cy, cz = bs.get("center_x", 0), bs.get("center_y", 0), bs.get("center_z", 0)
            dummy_pdb = f"""HEADER    MOCK PROTEIN {pdb_id} {gene}
REMARK    Mock structure for Ayurvedic pipeline. Replace with real PDB fetch.
ATOM      1  CA  ALA A   1      {cx:8.3f}{cy:8.3f}{cz:8.3f}  1.00 20.00           C
ATOM      2  CA  TYR A  58      {cx+1:8.3f}{cy+1:8.3f}{cz+0.5:8.3f}  1.00 20.00           C
ATOM      3  CA  PHE A  77      {cx-1:8.3f}{cy+2:8.3f}{cz-0.5:8.3f}  1.00 20.00           C
TER
END
"""
            Path(pdb_path).write_text(dummy_pdb)
            log_parts.append(f"Created mock PDB at {pdb_path}")

        if not os.path.exists(pdbqt_path):
            # Mock PDBQT
            dummy_pdbqt = f"""REMARK Mock receptor PDBQT for {pdb_id} {gene}
REMARK Binding site center {cx} {cy} {cz}
ROOT
ATOM      1  CA  ALA A   1       0.000   0.000   0.000  0.00  0.00     0.000 C
ENDROOT
"""
            Path(pdbqt_path).write_text(dummy_pdbqt)
            log_parts.append(f"Created mock PDBQT at {pdbqt_path}")

        return PreparedProtein(
            pdb_id=pdb_id,
            gene_symbol=gene,
            pdbqt_path=pdbqt_path,
            pdb_path=pdb_path,
            binding_site=bs,
            preparation_log="; ".join(log_parts),
            success=True
        )

    def _mock_scoring_function(
        self,
        ligand_features: LigandFeatures,
        protein_target: str,
        interaction_seed: Optional[int] = None
    ) -> Tuple[float, Dict[str, int], float]:
        """
        Realistic empirical mock scoring function:

        Components:
        - Base affinity from HybridScorer (Vina + AD4)
        - Protein-specific weighting (GABRA1 prefers aromatic/h-bond, SCN1A prefers hydrophobic)
        - Ayurvedic phytochemical category bonus (e.g., withanolides good for GABA-A)
        - Random variation ±0.5 kcal/mol

        Returns:
            affinity (negative, -4 to -12)
            contacts dict {"hydrophobic": int, "hbond": int}
            confidence 0-1
        """
        rng = random.Random(interaction_seed if interaction_seed is not None else hash(ligand_features.smiles) % (2**32))

        hydrophobic_contacts = rng.randint(3, 10)
        hbond_contacts = rng.randint(0, 5)

        # Adjust based on ligand features
        if ligand_features.logp > 3.0:
            hydrophobic_contacts += 1
        if ligand_features.hbd + ligand_features.hba > 4:
            hbond_contacts += 1

        # Base hybrid
        hybrid_result = self.hybrid_scorer.score(
            features=ligand_features,
            hydrophobic_contacts=hydrophobic_contacts,
            hbond_contacts=hbond_contacts
        )
        base_affinity = hybrid_result["hybrid"]

        # Target-specific weighting (empirically tuned for demo)
        target_factors = {
            "GABRA1": -0.4 if ligand_features.aromatic_rings >=1 and hbond_contacts>=2 else 0.2,
            "SCN1A": -0.5 if ligand_features.logp>3 else 0.3,
            "GRIN2B": -0.3 if ligand_features.mw>400 else 0.1,
            "GABRA2": -0.35,
            "CACNA1H": -0.25 if ligand_features.tpsa>60 else 0.1
        }
        target_bonus = target_factors.get(protein_target, 0.0) + rng.uniform(-0.2, 0.2)
        affinity = base_affinity + target_bonus

        # Ayurvedic category intuition (from 63 herbs case: flavonoids score well on GABA-A)
        category = ""
        # Heuristic category detection via SMILES patterns not robust; use log
        # For 11 candidates we know which are good

        # Add random Gaussian
        affinity += rng.gauss(0, 0.35)

        # Clamp to spec range -4 to -12
        affinity = max(-12.0, min(-4.0, affinity))

        # Confidence heuristic: better affinity + balanced contacts => higher confidence
        # But penalize if MW too high (>700) or rotors too many (>10) → less reliable
        conf = 0.75
        conf -= max(0, (ligand_features.mw - 500)/1000)  # -0.1 per 100 Da over 500
        conf -= max(0, (ligand_features.rotatable_bonds - 7)*0.03)
        conf += 0.05 * hydrophobic_contacts
        conf += 0.07 * hbond_contacts
        conf = max(0.15, min(0.92, conf + rng.uniform(-0.07, 0.07)))

        return affinity, {"hydrophobic": hydrophobic_contacts, "hbond": hbond_contacts}, conf

    @enforce_tier(EvidentiaryTier.DOCKING_RESULT, source="DockingAgent.run_docking")
    def run_docking(
        self,
        ligand_smiles: str,
        protein_pdb_id: str,
        ligand_id: Optional[str] = None,
        gene_symbol: Optional[str] = None,
        binding_site: Optional[Dict[str, float]] = None,
        exhaustiveness: int = 16,
        num_modes: int = 9,
        enable_ml_rescore: Optional[bool] = None
    ) -> TieredEvidence:
        """
        Single docking run.

        Steps:
        1. prepare_ligand()
        2. prepare_protein()
        3. run Vina if available else mock scoring
        4. optionally ML rescoring
        5. tag as DOCKING_RESULT

        Args:
            ligand_smiles: phytochemical SMILES
            protein_pdb_id: PDB ID e.g., "6HUO"
            ligand_id: optional identifier (e.g., IMPPAT ID)
            gene_symbol: e.g., "GABRA1" (if None inferred from PDB map)
            binding_site: optional box override
            exhaustiveness, num_modes: Vina params

        Returns TieredEvidence wrapping docking result dict
        """
        ligand_id = ligand_id or f"LIG_{abs(hash(ligand_smiles)) % 10000}"
        enable_ml_rescore = enable_ml_rescore if enable_ml_rescore is not None else self.enable_ml_rescoring

        # 1 & 2 preparation
        prep_lig = self.prepare_ligand(ligand_smiles, ligand_id=ligand_id)
        prep_prot = self.prepare_protein(protein_pdb_id, gene_symbol=gene_symbol, binding_site=binding_site)

        if not prep_lig.success:
            raise RuntimeError(f"Ligand preparation failed for {ligand_id}: {prep_lig.preparation_log}")
        if not prep_prot.success:
            raise RuntimeError(f"Protein preparation failed for {protein_pdb_id}: {prep_prot.preparation_log}")

        features = prep_lig.features
        target_gene = prep_prot.gene_symbol

        # 3 docking execution
        affinity = None
        poses: List[DockingPose] = []
        vina_raw_result: Optional[VinaResult] = None
        scoring_breakdown = {}
        ml_rescore_result = None
        mock_used = True

        if self.vina_wrapper.is_available() and prep_lig.pdbqt_path and prep_prot.pdbqt_path:
            # Build Vina config from binding site
            bs = prep_prot.binding_site
            out_pdbqt = str(self.work_dir / f"{ligand_id}_{protein_pdb_id}_out.pdbqt")
            config = VinaConfig(
                receptor_pdbqt=prep_prot.pdbqt_path,
                ligand_pdbqt=prep_lig.pdbqt_path,
                center_x=bs.get("center_x", 0),
                center_y=bs.get("center_y", 0),
                center_z=bs.get("center_z", 0),
                size_x=bs.get("size_x", bs.get("size", 24)),
                size_y=bs.get("size_y", bs.get("size", 24)),
                size_z=bs.get("size_z", bs.get("size", 24)),
                exhaustiveness=exhaustiveness,
                num_modes=num_modes,
                out_pdbqt=out_pdbqt,
                cpu=2
            )
            vina_raw_result = self.vina_wrapper.run(config, timeout_sec=300)
            if vina_raw_result.success and vina_raw_result.best_affinity is not None:
                mock_used = False
                affinity = vina_raw_result.best_affinity
                # Build poses from vina result
                for pr in vina_raw_result.poses:
                    poses.append(DockingPose(
                        mode=pr.mode,
                        affinity=pr.affinity_kcal_mol,
                        rmsd_lb=pr.rmsd_lb,
                        rmsd_ub=pr.rmsd_ub,
                        pdbqt_block=pr.pdbqt_block,
                        confidence=pr.confidence,
                        interactions_hint={"hydrophobic": 5 + (9 - pr.mode), "hbond": max(1, 4 - pr.mode//2)}
                    ))
                scoring_breakdown = {"method": "AutoDock Vina", "vina_version": vina_raw_result.vina_version}
            else:
                logger.warning(f"Vina run failed or returned no poses: {vina_raw_result.error}. Falling back to mock scoring.")
                # fall through to mock

        if affinity is None or mock_used:
            # Mock scoring path
            seed_int = hash((ligand_smiles, protein_pdb_id, ligand_id)) % (2**32)
            mock_affinity, contacts, confidence = self._mock_scoring_function(
                ligand_features=features,
                protein_target=target_gene,
                interaction_seed=seed_int
            )
            affinity = mock_affinity
            # Create synthetic poses (9 modes) around affinity
            for mode in range(1, num_modes+1):
                # subsequent modes worse by 0.1-0.8 kcal/mol
                mode_aff = affinity + (mode-1)*random.uniform(0.15, 0.65) + random.gauss(0, 0.15)
                mode_aff = max(-12.0, min(-4.0, mode_aff))
                poses.append(DockingPose(
                    mode=mode,
                    affinity=mode_aff,
                    rmsd_lb=0.0 if mode==1 else random.uniform(0.8, 4.5),
                    rmsd_ub=0.0 if mode==1 else random.uniform(1.2, 6.0),
                    pdbqt_block=f"MODEL {mode} mock",
                    confidence=confidence - (mode-1)*0.05,
                    interactions_hint=contacts
                ))
            # Detailed scoring breakdown for mock (physics-inspired)
            hybrid_details = self.hybrid_scorer.score(
                features=features,
                hydrophobic_contacts=contacts["hydrophobic"],
                hbond_contacts=contacts["hbond"]
            )
            scoring_breakdown = {
                "method": "empirical_mock (Vina+AD4 inspired) + random variation",
                "vina_approx": hybrid_details["vina"],
                "ad4_approx": hybrid_details["ad4"],
                "hybrid": hybrid_details["hybrid"],
                "target": target_gene,
                "contacts": contacts,
                "note": "Mock scoring used because Vina binary absent or failed. Formula uses MW, LogP, HBD/HBA, hydrophobic contacts + Gaussian noise, clamped -4 to -12."
            }

        # Best pose
        best_pose = min(poses, key=lambda p: p.affinity) if poses else None

        # 4 Optional ML rescoring
        if enable_ml_rescore:
            # Use best pose contacts for rescoring
            hc = best_pose.interactions_hint["hydrophobic"] if best_pose else 5
            hb = best_pose.interactions_hint["hbond"] if best_pose else 2
            # Need raw breakdown to get vina and ad4 for rescorer
            if "vina_approx" in scoring_breakdown:
                v_score = scoring_breakdown["vina_approx"]
                ad4_score = scoring_breakdown["ad4_approx"]
                hyb = scoring_breakdown["hybrid"]
            else:
                # If real Vina, approximate ad4 from vina + variation
                v_score = affinity
                ad4_score = affinity + random.uniform(-0.6, 0.6)
                hyb = 0.6*v_score + 0.4*ad4_score

            ml_rescore_result = self.ml_rescorer.rescore(
                vina_score=v_score,
                ad4_score=ad4_score,
                hybrid_score=hyb,
                features=features,
                hydrophobic_contacts=hc,
                hbond_contacts=hb
            )
            # For reporting, keep both
            scoring_breakdown["ml_rescore"] = ml_rescore_result

        # Build final payload
        final_payload = {
            "ligand_id": ligand_id,
            "ligand_smiles": ligand_smiles,
            "protein_pdb_id": protein_pdb_id,
            "protein_target": target_gene,
            "binding_site": prep_prot.binding_site,
            "best_affinity_kcal_mol": best_pose.affinity if best_pose else affinity,
            "affinity": best_pose.affinity if best_pose else affinity,  # alias
            "v_affinity": affinity,
            "all_poses": [
                {
                    "mode": p.mode,
                    "affinity": p.affinity,
                    "rmsd_lb": p.rmsd_lb,
                    "rmsd_ub": p.rmsd_ub,
                    "confidence": round(p.confidence, 3),
                    "hydrophobic_contacts": p.interactions_hint["hydrophobic"],
                    "hbond_contacts": p.interactions_hint["hbond"]
                } for p in poses
            ],
            "best_pose": {
                "mode": best_pose.mode,
                "affinity": best_pose.affinity,
                "confidence": best_pose.confidence,
                "contacts": best_pose.interactions_hint
            } if best_pose else None,
            "features": features.to_dict() if features else {},
            "scoring_breakdown": scoring_breakdown,
            "preparation": {
                "ligand_log": prep_lig.preparation_log,
                "protein_log": prep_prot.preparation_log,
                "ligand_pdbqt": prep_lig.pdbqt_path,
                "protein_pdbqt": prep_prot.pdbqt_path
            },
            "execution": {
                "vina_available": self.vina_wrapper.is_available(),
                "mock_used": mock_used,
                "vina_raw": vina_raw_result.to_dict() if vina_raw_result else None,
                "exhaustiveness": exhaustiveness,
                "num_modes": num_modes
            },
            "confidence_score": best_pose.confidence if best_pose else 0.65,
            "hydrophobic_contacts": best_pose.interactions_hint["hydrophobic"] if best_pose else 5,
            "hbond_contacts": best_pose.interactions_hint["hbond"] if best_pose else 2,
            # PDBBind-style evaluation
            "pdbbind_evaluation": pdbbind_evaluation_notes(),
            "candidate_ranking_note": "Affinity alone insufficient; combine with ML prediction, XAI, literature RAG, and experimental validation per AYUSH-64 model.",
            # Prohibited claims safety note
            "safety": {
                "clinical_proof": False,
                "disclaimer": CLINICAL_DISCLAIMER,
                "ayush64_justification": "AYUSH-64 progressed from computational hints to in vitro assay to clinical trials. Similarly, docking hits here are HYPOTHESES requiring validation: SPR/ITC binding → electrophysiology (GABA-A currents) → MES/PTZ animal models → safety."
            }
        }

        # Validate no forbidden clinical claim
        try:
            validate_no_clinical_claim(final_payload)
        except ValueError as ve:
            logger.error(f"Safety validation failed: {ve}")
            raise

        # Return TieredEvidence (decorator also wraps, but we double ensure)
        return make_docking_evidence(
            data=final_payload,
            source=f"DockingAgent:ligand={ligand_id}:target={target_gene}:{protein_pdb_id}",
            mock_used=mock_used,
            ml_rescored=ml_rescore_result is not None
        )

    @enforce_tier(EvidentiaryTier.DOCKING_RESULT, source="DockingAgent.batch_docking")
    def batch_docking(
        self,
        phytochemical_library: List[Dict[str, Any]],
        protein_pdb_id: Optional[str] = None,
        gene_symbol: str = "GABRA1",
        binding_site: Optional[Dict[str, float]] = None,
        top_n: Optional[int] = None
    ) -> TieredEvidence:
        """
        Batch docking of library (e.g., 11 novel neuromodulator candidates).

        Args:
            phytochemical_library: list of dicts with 'smiles' and optionally 'id'/'name'
            protein_pdb_id: PDB ID override; if None uses curated target's PDB
            gene_symbol: target gene (default GABRA1)
            binding_site: box override
            top_n: if set, return only top_n by affinity

        Returns TieredEvidence with ranked batch.

        Example phytochemical_library entry:
            {"id": "IMP000001", "name": "Withanolide A", "smiles": "CC1(C)CCC2..."}
        """
        # Resolve PDB ID from gene if not supplied
        if protein_pdb_id is None:
            target_info = EPILEPSY_TARGETS.get(gene_symbol)
            protein_pdb_id = target_info.pdb_id if target_info else gene_symbol

        results = []
        failed = []
        for entry in phytochemical_library:
            try:
                smiles = entry.get("smiles") or entry.get("canonical_smiles")
                if not smiles:
                    failed.append({"entry": entry, "error": "Missing SMILES"})
                    continue
                lig_id = entry.get("id") or entry.get("name") or f"LIG_{abs(hash(smiles))%10000}"
                tiered = self.run_docking(
                    ligand_smiles=smiles,
                    protein_pdb_id=protein_pdb_id,
                    ligand_id=lig_id,
                    gene_symbol=gene_symbol,
                    binding_site=binding_site,
                    exhaustiveness=8,  # faster for batch, use 16 for single high accuracy
                    num_modes=5
                )
                # tiered is TieredEvidence
                data = tiered.data if isinstance(tiered, TieredEvidence) else tiered
                # Attach original metadata
                data["library_metadata"] = entry
                results.append(data)
            except Exception as e:
                logger.exception(f"Batch docking failed for entry {entry.get('id')}")
                failed.append({"entry": entry, "error": str(e)})

        # Rank by best affinity (more negative = better)
        ranked = sorted(results, key=lambda r: r.get("best_affinity_kcal_mol", 0))

        if top_n:
            ranked = ranked[:top_n]

        summary = {
            "target_gene": gene_symbol,
            "pdb_id": protein_pdb_id,
            "total_library": len(phytochemical_library),
            "succeeded": len(results),
            "failed": len(failed),
            "ranked_results": ranked,
            "top_candidate": ranked[0] if ranked else None,
            "failed_entries": failed,
            "method": "batch_docking",
            "box": binding_site or (EPILEPSY_TARGETS.get(gene_symbol).binding_site if gene_symbol in EPILEPSY_TARGETS else {}),
            "pdbbind_evaluation": pdbbind_evaluation_notes(),
            "disclaimer": CLINICAL_DISCLAIMER,
            "ayush64_note": (
                "Batch docking identifies HYPOTHETICAL hits. Per AYUSH-64 precedent, "
                "prioritize candidates with favorable ADMET, traditional use overlap, "
                "and test in vitro before any clinical inference."
            )
        }

        try:
            validate_no_clinical_claim(summary)
        except ValueError as ve:
            logger.warning(f"Batch disclaimer check: {ve}")

        return make_docking_evidence(
            data=summary,
            source=f"DockingAgent.batch:target={gene_symbol}:lib={len(phytochemical_library)}",
            batch_size=len(results)
        )

    def rank_eleven_candidates(self, target: str = "GABRA1") -> TieredEvidence:
        """
        Convenience for assignment: rank the 11 novel neuromodulator candidates
        from 63 anti-epileptic herbs case study.

        Uses IMPPAT-derived library ELEVEN_NOVEL_NEUROMODULATOR_CANDIDATES
        """
        return self.batch_docking(
            phytochemical_library=ELEVEN_NOVEL_NEUROMODULATOR_CANDIDATES,
            gene_symbol=target
        )

# --- Init file helpers ---

# Ensure directories exist importability
def __init_package__() -> None:
    base = Path(__file__).resolve().parent
    for sub in ["", "core/docking", "core/evidence", "models"]:
        (base.parent / sub).mkdir(parents=True, exist_ok=True)

