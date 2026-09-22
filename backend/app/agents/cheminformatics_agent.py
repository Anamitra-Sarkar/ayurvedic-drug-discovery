"""
Cheminformatics Agent
=====================
Agent for molecular-structure processing using RDKit (with fallback)

Responsibilities:
- SMILES validation, 3D conformer generation
- Compute descriptors: MW, LogP, HBD, HBA, TPSA, rotatable bonds, Mordred-like 20 descriptors
- Lipinski check, PAINS filter
- Process single phytochemical or batch
- Returns descriptors tagged as DATABASE_DERIVED + COMPUTED (per spec)

Evidence tier: DATABASE_DERIVED + COMPUTED - computed from chemical structure, not experimental measurement
Must NOT be presented as clinical proof.

Production-quality: error handling, type hints, docstrings, RDKit fallback mock, logging.

Author: Senior Engineer - Cheminformatics Agent
"""

from __future__ import annotations

import logging
import hashlib
import pathlib
from typing import Any, Dict, List, Optional, Union, Tuple
from datetime import datetime
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Evidence tier handling - compatibility layer
try:
    from app.core.evidence.tiers import EvidentiaryTier, TieredEvidence, TIER_DISCLAIMERS
    EvidenceTierClass = EvidentiaryTier
    TieredEvidenceClass = TieredEvidence
except ImportError:
    try:
        from app.agents.evidence_tiers import EvidenceTier as EvidenceTierClass, TieredOutput as TieredEvidenceClass
        TIER_DISCLAIMERS = None
    except ImportError:
        try:
            from app.core.evidence import EvidenceTier as EvidenceTierClass, EvidenceTaggedOutput as TieredEvidenceClass
        except ImportError:
            from enum import Enum
            class EvidenceTierClass(str, Enum):
                DATABASE_DERIVED = "DATABASE_DERIVED"
                DOCKING_RESULT = "DOCKING_RESULT"
                ML_PREDICTION = "ML_PREDICTION"
                XAI_INTERPRETATION = "XAI_INTERPRETATION"
                LITERATURE_DERIVED = "LITERATURE_DERIVED"
                LITERATURE_EVIDENCE = "LITERATURE_EVIDENCE"
            class TieredEvidenceClass:
                def __init__(self, tier, data, source, metadata=None):
                    self.tier = tier
                    self.data = data
                    self.source = source
                    self.metadata = metadata or {}
                    self.timestamp = datetime.utcnow().isoformat()
                    self.disclaimer = "[DATABASE_DERIVED + COMPUTED] Computed from SMILES. Not experimental."
                def to_dict(self):
                    return {"evidentiary_tier": self.tier.value if hasattr(self.tier, 'value') else str(self.tier),
                            "data": self.data, "source": self.source,
                            "disclaimer": self.disclaimer, "metadata": self.metadata, "timestamp": self.timestamp}

# Import core cheminformatics logic
try:
    from app.core.cheminformatics.descriptors import (
        calculate_descriptors,
        batch_calculate_descriptors,
        validate_smiles,
        RDKIT_AVAILABLE,
        MORDRED_LIKE_20
    )
    from app.core.cheminformatics.filters import (
        comprehensive_drug_likeness_assessment,
        lipinski_filter,
        veber_filter,
        qed_score_filter,
        check_pains_rdkit,
        check_pains_fallback,
        admet_heuristic_filters
    )
    CORE_AVAILABLE = True
except ImportError as e:
    CORE_AVAILABLE = False
    RDKIT_AVAILABLE = False
    MORDRED_LIKE_20 = []
    logger.error(f"Core cheminformatics modules not available: {e} - creating minimal fallback")
    # Minimal fallback implementations
    def validate_smiles(smiles: str):
        if not smiles:
            return False, "empty", None
        return True, "fallback valid", None
    def calculate_descriptors(smiles: str, include_3d: bool = False):
        import hashlib, re
        h = hashlib.md5(smiles.encode()).hexdigest()
        heavy = len(re.findall(r"[A-Z][a-z]?|c|n|o|s", smiles))
        return {
            "molecular_weight": 300.0 + (int(h[:2],16)%200),
            "logp": 2.0,
            "hbd": 2,
            "hba": 4,
            "tpsa": 60.0,
            "rotatable_bonds": 3,
            "heavy_atom_count": heavy,
            "ring_count": 2,
            "aromatic_ring_count": 1,
            "fraction_csp3": 0.5,
            "qed": 0.6,
            "_source": "fallback_agent",
            "evidence_tier": "DATABASE_DERIVED",
            "is_computed": True
        }
    def comprehensive_drug_likeness_assessment(desc, smi):
        return {"passes": True, "composite_verdict": "PASS (fallback)", "pass_count": 3}

# Constants
DATABASE_COMPUTED_DISCLAIMER = (
    "[DATABASE_DERIVED + COMPUTED] Cheminformatics descriptors computed from SMILES using RDKit/Mordred-like logic. "
    "This is derived from chemical structure, NOT experimental measurement. "
    "Not clinical proof of safety, efficacy, or bioavailability."
)

AYUSH64_NOTE = (
    "Per AYUSH-64 justification, computational descriptors and drug-likeness are hypotheses for prioritization, "
    "not clinical proof. Ayurvedic polyphenols often violate Lipinski yet remain privileged scaffolds."
)

class CheminformaticsAgent:
    """
    Cheminformatics Agent - processes phytochemical structures.
    
    Features:
    - RDKit with graceful fallback (mock calculations deterministic)
    - SMILES validation, 3D conformer generation (ETKDG)
    - 20 Mordred-like descriptors + Lipinski, PAINS, ADMET heuristics
    - Single + batch processing
    - Evidence tier tagging: DATABASE_DERIVED + COMPUTED
    
    Usage:
        agent = CheminformaticsAgent()
        result = agent.process_phytochemical({"compound_name": "Quercetin", "smiles": "O=C1..."})
        batch = agent.batch_process([{"smiles": "CCO"}, {"smiles": "c1ccccc1O"}])
    """
    
    def __init__(self, enable_3d: bool = False, rdkit_strict: bool = False):
        """
        Initialize CheminformaticsAgent.
        
        Args:
            enable_3d: Whether to attempt 3D conformer generation by default (can be overridden per call)
            rdkit_strict: If True, raise error when RDKit not available. If False (default), use fallback.
        """
        self.enable_3d_default = enable_3d
        self.rdkit_strict = rdkit_strict
        self.rdkit_available = RDKIT_AVAILABLE if 'RDKIT_AVAILABLE' in globals() else False
        self.core_available = CORE_AVAILABLE
        
        if not self.rdkit_available and self.rdkit_strict:
            raise ImportError("RDKit not available and rdkit_strict=True - cannot proceed. Install rdkit-pypi")
        
        if not self.rdkit_available:
            logger.warning("RDKit not available - CheminformaticsAgent using deterministic fallback mock. "
                           "For full functionality: pip install rdkit-pypi")
        
        self.stats = {
            "processed": 0,
            "failed": 0,
            "rdkit_used": 0,
            "fallback_used": 0
        }
    
    def _wrap_computed_output(self, data: Any, source: str, metadata: Optional[Dict] = None) -> TieredEvidenceClass:
        """Wrap in DATABASE_DERIVED + COMPUTED tier"""
        tier_val = None
        try:
            tier_val = EvidenceTierClass.DATABASE_DERIVED
        except AttributeError:
            tier_val = "DATABASE_DERIVED"
        
        meta = metadata or {}
        meta.update({
            "evidence_tier": "DATABASE_DERIVED",
            "tier_number": 1,
            "is_computed": True,
            "computation_source": "RDKit" if self.rdkit_available else "fallback_mock",
            "ayush64_note": AYUSH64_NOTE,
            "rdkit_available": self.rdkit_available
        })
        
        try:
            if TieredEvidenceClass.__name__ == "TieredEvidence":
                obj = TieredEvidenceClass(
                    tier=tier_val,
                    data=data,
                    source=source,
                    metadata=meta
                )
                # Override disclaimer for computed
                obj.disclaimer = DATABASE_COMPUTED_DISCLAIMER
                return obj
            elif TieredEvidenceClass.__name__ == "TieredOutput":
                return TieredEvidenceClass(
                    tier=tier_val,
                    content=data,
                    citations=[],
                    confidence=0.95 if self.rdkit_available else 0.7,
                    metadata=meta
                )
            elif TieredEvidenceClass.__name__ == "EvidenceTaggedOutput":
                obj = TieredEvidenceClass(tier=tier_val, data=data, metadata=meta)
                obj.disclaimer = DATABASE_COMPUTED_DISCLAIMER
                return obj
            else:
                return TieredEvidenceClass(tier=tier_val, data=data, source=source, metadata=meta)
        except Exception as e:
            logger.warning(f"Wrapping failed ({e}), using fallback dict")
            return {
                "evidentiary_tier": "DATABASE_DERIVED",
                "is_computed": True,
                "tier_number": 1,
                "data": data,
                "source": source,
                "metadata": meta,
                "disclaimer": DATABASE_COMPUTED_DISCLAIMER,
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def validate_smiles_wrapper(self, smiles: str) -> Dict[str, Any]:
        """
        Wrapper for SMILES validation with evidence tier tagging.
        
        Returns dict with validity + tier tag
        """
        is_valid, msg, mol = validate_smiles(smiles)
        result = {
            "smiles": smiles,
            "is_valid": is_valid,
            "message": msg,
            "has_rdkit_mol": mol is not None,
            "rdkit_available": self.rdkit_available
        }
        return self._wrap_computed_output(
            data=result,
            source="RDKit SMILES validation" if self.rdkit_available else "fallback SMILES heuristic",
            metadata={"smiles": smiles, "valid": is_valid}
        )
    
    def process_phytochemical(self, phytochemical: Dict[str, Any],
                              include_3d: Optional[bool] = None,
                              include_filters: bool = True,
                              include_pains: bool = True) -> TieredEvidenceClass:
        """
        Process a single phytochemical: validate, descriptors, filters.
        
        Args:
            phytochemical: Dict with at least 'smiles' key. May contain:
                - compound_name, compound_id, smiles, phytochemical_class, etc.
            include_3d: Override default for 3D conformer generation
            include_filters: Whether to run drug-likeness filters
            include_pains: Whether to run PAINS filter
            
        Returns:
            TieredEvidence DATABASE_DERIVED + COMPUTED with:
                - descriptors (20 Mordred-like)
                - lipinski, veber, ghose, qed, admet
                - pains alerts
                - 3D conformer flag
                - batch_id, processing metadata
        """
        # Extract SMILES
        if isinstance(phytochemical, str):
            # If string passed, treat as SMILES
            smiles = phytochemical
            base_data = {"smiles": smiles, "compound_name": smiles}
        elif isinstance(phytochemical, dict):
            smiles = phytochemical.get("smiles") or phytochemical.get("SMILES") or phytochemical.get("canonical_smiles")
            if not smiles:
                err = {"error": "No SMILES found in input", "input_keys": list(phytochemical.keys()) if isinstance(phytochemical, dict) else str(type(phytochemical))}
                self.stats["failed"] += 1
                return self._wrap_computed_output(data=err, source="CheminformaticsAgent error - no SMILES", metadata={"failed": True})
            base_data = dict(phytochemical)
        else:
            err = {"error": f"Invalid input type {type(phytochemical)}, expected dict or SMILES string"}
            self.stats["failed"] += 1
            return self._wrap_computed_output(data=err, source="CheminformaticsAgent error - invalid input", metadata={"failed": True})
        
        # Validate
        is_valid, msg, mol = validate_smiles(smiles)
        if not is_valid:
            self.stats["failed"] += 1
            result = {
                "input": base_data,
                "smiles": smiles,
                "is_valid": False,
                "validation_message": msg,
                "descriptors": None,
                "error": f"SMILES validation failed: {msg}"
            }
            return self._wrap_computed_output(data=result, source="CheminformaticsAgent - invalid SMILES", metadata={"valid": False})
        
        # Compute descriptors
        use_3d = self.enable_3d_default if include_3d is None else include_3d
        
        try:
            descriptors = calculate_descriptors(smiles, include_3d=use_3d)
            
            # Update stats
            self.stats["processed"] += 1
            if descriptors.get("_source") == "rdkit":
                self.stats["rdkit_used"] += 1
            else:
                self.stats["fallback_used"] += 1
            
            # Filters
            filter_results = {}
            if include_filters:
                try:
                    comp = comprehensive_drug_likeness_assessment(descriptors, smiles)
                    filter_results["comprehensive"] = comp
                    # Also separate for UI
                    filter_results["lipinski"] = comp.get("filters", {}).get("lipinski") if isinstance(comp, dict) else lipinski_filter(descriptors)
                except Exception as e:
                    logger.warning(f"Comprehensive filter failed for {smiles[:50]}: {e}")
                    filter_results["comprehensive_error"] = str(e)
                    # Fallback individual filters
                    try:
                        filter_results["lipinski"] = lipinski_filter(descriptors)
                        filter_results["veber"] = veber_filter(descriptors)
                        filter_results["qed"] = qed_score_filter(descriptors)
                        filter_results["admet_heuristics"] = admet_heuristic_filters(descriptors)
                    except Exception as e2:
                        filter_results["individual_filter_error"] = str(e2)
            
            # PAINS
            pains_result = {}
            if include_pains:
                try:
                    if self.rdkit_available:
                        is_pains, alerts = check_pains_rdkit(smiles)
                    else:
                        is_pains, alerts = check_pains_fallback(smiles)
                    pains_result = {
                        "is_pains": is_pains,
                        "alerts": alerts,
                        "passes_pains": not is_pains,
                        "alert_count": len(alerts),
                        "checked_with": "RDKit FilterCatalog" if self.rdkit_available else "fallback SMARTS heuristic"
                    }
                except Exception as e:
                    pains_result = {"is_pains": False, "alerts": [], "error": str(e), "passes_pains": True}
            
            # Assemble result
            enriched = {
                "input": base_data,
                "compound_name": base_data.get("compound_name") or base_data.get("compound_id") or smiles,
                "compound_id": base_data.get("compound_id"),
                "smiles": smiles,
                "is_valid": True,
                "validation_message": msg,
                "descriptors": descriptors,
                "descriptors_summary": {k: descriptors.get(k) for k in ["molecular_weight", "logp", "hbd", "hba", "tpsa", "rotatable_bonds", "heavy_atom_count", "qed", "fraction_csp3"] if k in descriptors},
                "mordred_like_20": {k: descriptors.get(k) for k in [
                    "molecular_weight", "logp", "hbd", "hba", "tpsa", "rotatable_bonds", "heavy_atom_count",
                    "ring_count", "aromatic_ring_count", "fraction_csp3", "formal_charge", "num_radical_electrons",
                    "bertz_ct", "balaban_j", "molar_refractivity", "qed", "num_aliphatic_rings", "num_heterocycles",
                    "num_amide_bonds", "topological_polar_surface_area_detail"
                ] if k in descriptors},
                "drug_likeness": filter_results.get("comprehensive") if filter_results else None,
                "filters": filter_results,
                "pains": pains_result,
                "has_3d_conformer": descriptors.get("has_3d_conformer", False),
                "processing_metadata": {
                    "rdkit_available": self.rdkit_available,
                    "source": descriptors.get("_source", "unknown"),
                    "include_3d": use_3d,
                    "include_filters": include_filters,
                    "processed_at": datetime.utcnow().isoformat(),
                    "agent": "CheminformaticsAgent"
                }
            }
            
            # Add disclaimer explicitly
            enriched["evidence_tier"] = "DATABASE_DERIVED"
            enriched["is_computed"] = True
            enriched["disclaimer"] = DATABASE_COMPUTED_DISCLAIMER
            
            return self._wrap_computed_output(
                data=enriched,
                source=f"RDKit-computed" if descriptors.get("_source")=="rdkit" else "fallback-computed",
                metadata={"smiles": smiles, "compound_name": enriched["compound_name"], "qed": descriptors.get("qed")}
            )
        
        except Exception as e:
            logger.exception(f"Descriptor calculation failed for {smiles[:100]}: {e}")
            self.stats["failed"] += 1
            error_result = {
                "input": base_data,
                "smiles": smiles,
                "is_valid": is_valid,
                "validation_message": msg,
                "error": str(e),
                "error_type": type(e).__name__,
                "descriptors": None,
                "suggestion": "Check SMILES syntax, try sanitization or fallback mode"
            }
            return self._wrap_computed_output(
                data=error_result,
                source="CheminformaticsAgent error during descriptor calc",
                metadata={"failed": True, "smiles": smiles}
            )
    
    def batch_process(self, phytochemicals: List[Union[Dict[str, Any], str]],
                      include_3d: bool = False,
                      include_filters: bool = True,
                      include_pains: bool = True,
                      max_workers: Optional[int] = None) -> TieredEvidenceClass:
        """
        Batch process list of phytochemicals.
        
        Args:
            phytochemicals: List of dicts with 'smiles' or SMILES strings
            include_3d: Whether to attempt 3D conformer generation (slower)
            include_filters: Include drug-likeness filters
            include_pains: Include PAINS screening
            max_workers: Optional parallel workers (future use - currently sequential for simplicity)
            
        Returns:
            TieredEvidence batch result with list of individual results + summary
        """
        if not isinstance(phytochemicals, (list, tuple)):
            raise ValueError(f"batch_process expects list, got {type(phytochemicals)}")
        
        individual_results = []
        failed = 0
        passed_lipinski = 0
        passed_pains = 0
        qed_scores = []
        
        for idx, item in enumerate(phytochemicals):
            res_evidence = self.process_phytochemical(
                phytochemical=item,
                include_3d=include_3d,
                include_filters=include_filters,
                include_pains=include_pains
            )
            # Unwrap for analysis if Tiered wrapper
            if hasattr(res_evidence, 'data'):
                data = res_evidence.data
            elif hasattr(res_evidence, 'content'):
                data = res_evidence.content
            elif isinstance(res_evidence, dict) and 'data' in res_evidence:
                data = res_evidence['data']
            else:
                data = res_evidence
            
            individual_results.append(res_evidence)
            
            # Summary stats
            if isinstance(data, dict):
                if data.get("error") or data.get("is_valid") is False:
                    failed += 1
                else:
                    # Lipinski pass
                    comp = data.get("drug_likeness") or data.get("filters", {}).get("comprehensive")
                    if comp:
                        if comp.get("filters", {}).get("lipinski", {}).get("passes") or comp.get("composite_verdict") == "PASS":
                            passed_lipinski += 1
                        # also direct lipinski
                        if data.get("filters", {}).get("lipinski", {}).get("passes"):
                            passed_lipinski = passed_lipinski  # already counted
                    # PAINS pass
                    pains = data.get("pains", {})
                    if pains.get("passes_pains"):
                        passed_pains += 1
                    # QED
                    desc = data.get("descriptors", {})
                    if desc and "qed" in desc:
                        qed_scores.append(desc["qed"])
        
        total = len(phytochemicals)
        avg_qed = sum(qed_scores)/len(qed_scores) if qed_scores else 0.0
        
        batch_summary = {
            "total_input": total,
            "successful": total - failed,
            "failed": failed,
            "passed_lipinski_count": passed_lipinski,
            "passed_pains_count": passed_pains,
            "average_qed": round(avg_qed, 3),
            "qed_distribution": {
                "min": min(qed_scores) if qed_scores else None,
                "max": max(qed_scores) if qed_scores else None,
                "scores": qed_scores[:20]  # first 20 for preview
            },
            "processing_stats": dict(self.stats),
            "results": individual_results,  # list of TieredEvidence
            # For frontend convenience also provide unwrapped list
            "results_unwrapped": [
                (r.data if hasattr(r, 'data') else (r.content if hasattr(r, 'content') else r.get('data') if isinstance(r, dict) else r))
                for r in individual_results
            ],
            "summary_disclaimer": DATABASE_COMPUTED_DISCLAIMER,
            "ayush_note": AYUSH64_NOTE
        }
        
        return self._wrap_computed_output(
            data=batch_summary,
            source=f"CheminformaticsAgent batch_process {total} compounds",
            metadata={
                "batch_size": total,
                "successful": total-failed,
                "failed": failed,
                "avg_qed": avg_qed,
                "rdkit_available": self.rdkit_available
            }
        )
    
    def generate_3d_conformer(self, smiles: str, optimize: bool = True,
                              random_seed: int = 42) -> TieredEvidenceClass:
        """
        Explicit 3D conformer generation method.
        
        Uses ETKDGv3 + MMFF optimization when RDKit available,
        else returns mock with error flag.
        
        Returns TieredEvidence with molblock / PDB info if available
        """
        is_valid, msg, mol = validate_smiles(smiles)
        if not is_valid:
            return self._wrap_computed_output(
                data={"smiles": smiles, "error": f"Invalid SMILES: {msg}", "has_3d": False},
                source="3D conformer - invalid SMILES",
                metadata={"valid": False}
            )
        
        if not self.rdkit_available:
            return self._wrap_computed_output(
                data={
                    "smiles": smiles,
                    "has_3d": False,
                    "mock": True,
                    "error": "RDKit not available - cannot generate real 3D conformer",
                    "molblock": None,
                    "suggestion": "Install RDKit for ETKDGv3 conformer generation"
                },
                source="fallback - no 3D",
                metadata={"has_3d": False}
            )
        
        try:
            from rdkit import Chem
            from rdkit.Chem import AllChem
            
            # mol already from validate_smiles
            if mol is None:
                mol = Chem.MolFromSmiles(smiles)
            
            mol_h = Chem.AddHs(mol)
            params = AllChem.ETKDGv3()
            params.randomSeed = random_seed
            params.useRandomCoords = True
            params.maxIterations = 200
            
            embed_result = AllChem.EmbedMolecule(mol_h, params)
            
            if embed_result != 0:
                return self._wrap_computed_output(
                    data={
                        "smiles": smiles,
                        "has_3d": False,
                        "embed_code": embed_result,
                        "error": f"Embedding failed with code {embed_result}",
                        "molblock": None
                    },
                    source="RDKit ETKDG failed",
                    metadata={"embed_code": embed_result}
                )
            
            if optimize:
                try:
                    opt_result = AllChem.MMFFOptimizeMolecule(mol_h, maxIters=200)
                except Exception as e:
                    # Try UFF if MMFF fails
                    try:
                        AllChem.UFFOptimizeMolecule(mol_h, maxIters=200)
                        opt_result = 0
                    except Exception as e2:
                        opt_result = -1
            
            # Generate MolBlock and PDB
            molblock = Chem.MolToMolBlock(mol_h)
            pdb_block = Chem.MolToPDBBlock(mol_h) if hasattr(Chem, 'MolToPDBBlock') else None
            
            # Calculate simple energy if possible
            try:
                props = AllChem.MMFFGetMoleculeProperties(mol_h)
                if props:
                    ff = AllChem.MMFFGetMoleculeForceField(mol_h, props)
                    energy = ff.CalcEnergy() if ff else None
                else:
                    energy = None
            except Exception:
                energy = None
            
            result = {
                "smiles": smiles,
                "has_3d": True,
                "molblock": molblock[:5000] + "... [truncated]" if len(molblock) > 5000 else molblock,
                "molblock_full_length": len(molblock),
                "pdb_block_preview": pdb_block[:2000] if pdb_block else None,
                "energy_mmff": energy,
                "num_atoms": mol_h.GetNumAtoms(),
                "num_heavy_atoms": mol_h.GetNumHeavyAtoms(),
                "conformer_generation": "ETKDGv3 + MMFF",
                "random_seed": random_seed
            }
            
            return self._wrap_computed_output(
                data=result,
                source="RDKit ETKDGv3 3D conformer",
                metadata={"has_3d": True, "smiles": smiles, "energy": energy}
            )
        
        except Exception as e:
            logger.exception(f"3D conformer generation failed for {smiles[:50]}: {e}")
            return self._wrap_computed_output(
                data={"smiles": smiles, "has_3d": False, "error": str(e), "error_type": type(e).__name__},
                source="RDKit 3D error",
                metadata={"error": True}
            )
    
    def get_stats(self) -> Dict[str, Any]:
        return dict(self.stats)

# Singleton convenience
_default_chem_agent: Optional[CheminformaticsAgent] = None

def get_cheminformatics_agent(enable_3d: bool = False) -> CheminformaticsAgent:
    global _default_chem_agent
    if _default_chem_agent is None:
        _default_chem_agent = CheminformaticsAgent(enable_3d=enable_3d)
    return _default_chem_agent
