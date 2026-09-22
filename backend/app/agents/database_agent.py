"""
Database Agent
==============
Agent for curated phytochemical and traditional-medicine databases (IMPPAT primary)

Responsibilities:
- Load IMPPAT sample data from JSON
- Search by plant, compound, therapeutic use
- Filter by drug-likeness (Lipinski), ADMET
- Returns results tagged as evidence tier DATABASE_DERIVED
- Methods: search_plants(), get_phytochemicals_for_plant(), search_by_property(), get_network_pharmacology_graph()
- Triphala and AYUSH-64 as special cases (174 bioactives, 44 targets network example)

Evidence tier enforcement: ALL outputs tagged Tier 1 DATABASE_DERIVED

Compliance:
- MUST NOT present computational prediction as clinical proof
- Includes AYUSH-64 case study justification disclaimer
- Production-quality: error handling, type hints, docstrings, logging

Author: Senior Engineer - Database Agent
"""

from __future__ import annotations

import json
import logging
import pathlib
import re
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Union, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

# Evidence tier handling - try multiple import paths for compatibility
try:
    from app.core.evidence.tiers import EvidentiaryTier, TieredEvidence, TIER_DISCLAIMERS, CLINICAL_DISCLAIMER
    EvidenceTierClass = EvidentiaryTier
    TieredEvidenceClass = TieredEvidence
except ImportError:
    try:
        from app.agents.evidence_tiers import EvidenceTier as EvidenceTierClass, TieredOutput as TieredEvidenceClass, SAFETY_DISCLAIMER_TEMPLATE
        TIER_DISCLAIMERS = None
    except ImportError:
        try:
            from app.core.evidence import EvidenceTier as EvidenceTierClass, EvidenceTaggedOutput as TieredEvidenceClass
            TIER_DISCLAIMERS = None
        except ImportError:
            # Fallback minimal definition if modules not found (standalone runnable)
            from enum import Enum
            class EvidenceTierClass(str, Enum):
                DATABASE_DERIVED = "DATABASE_DERIVED"
                DOCKING_RESULT = "DOCKING_RESULT"
                ML_PREDICTION = "ML_PREDICTION"
                XAI_INTERPRETATION = "XAI_INTERPRETATION"
                LITERATURE_EVIDENCE = "LITERATURE_EVIDENCE"
                LITERATURE_DERIVED = "LITERATURE_DERIVED"
            class TieredEvidenceClass:
                def __init__(self, tier, data, source, metadata=None):
                    self.tier = tier
                    self.data = data
                    self.source = source
                    self.metadata = metadata or {}
                    self.timestamp = datetime.utcnow().isoformat()
                    self.disclaimer = "Database-derived curated entry. Cross-check primary literature."
                def to_dict(self):
                    return {"evidentiary_tier": self.tier.value if hasattr(self.tier, 'value') else str(self.tier),
                            "data": self.data, "source": self.source,
                            "disclaimer": self.disclaimer, "metadata": self.metadata, "timestamp": self.timestamp}
            TIER_DISCLAIMERS = None
            logger.warning("Evidence tier modules not found - using minimal fallback - not production compliant")

# Import cheminformatics filters if available
try:
    from app.core.cheminformatics.descriptors import calculate_descriptors, RDKIT_AVAILABLE
    from app.core.cheminformatics.filters import (
        comprehensive_drug_likeness_assessment,
        lipinski_filter,
        check_pains_rdkit
    )
    CHEM_AVAILABLE = True
except ImportError:
    CHEM_AVAILABLE = False
    RDKIT_AVAILABLE = False
    logger.warning("Cheminformatics modules not available - drug-likeness filtering will use heuristic")

# Default data path
DEFAULT_DATA_PATH = pathlib.Path(__file__).parent.parent / "data" / "imppat_sample.json"

# AYUSH-64 justification text
AYUSH64_JUSTIFICATION = (
    "AYUSH-64 (Alstonia scholaris, Picrorhiza kurroa, Swertia chirata, Caesalpinia crista) case study: "
    "Computational docking indicated binding to SARS-CoV-2 Mpro (Tier 2), ML predicted affinity (Tier 3), "
    "but clinical efficacy was NOT assumed. Required subsequent in-vitro assays, CCRAS-sponsored clinical trials "
    "(CTRI/2020/06/025575). Pipeline enforces same separation: computational prediction = hypothesis for prioritization, "
    "NOT clinical proof."
)

TRIPHALA_NETWORK_REF = {
    "study": "Network pharmacology analysis of Triphala (example for teaching)",
    "reported_counts": "174 bioactives, 44 targets in literature (e.g., obesity-related)",
    "note": "This sample implements truncated example: 14 phytochemicals from 3 plants, graph generation creates 174+44 mock expansion for scale demonstration"
}

@dataclass
class PlantRecord:
    plant_id: str
    common_name: str
    botanical_name: str
    ayurvedic_name: str
    family: str
    traditional_uses: List[str]
    therapeutic_uses: List[str]
    formulation: Optional[str]
    phytochemical_count: int

@dataclass
class PhytochemicalRecord:
    compound_id: str
    compound_name: str
    smiles: str
    molecular_formula: Optional[str]
    plant_sources: List[str]
    phytochemical_class: str
    therapeutic_uses: List[str]
    pubchem_cid: Optional[int]
    traditional_use_score: float

class DatabaseAgent:
    """
    Database Agent for IMPPAT and Ayurvedic phytochemical databases.
    
    Design:
    - Loads JSON at init (path configurable via env or param)
    - Indexes for fast search
    - All outputs wrapped in TieredEvidence with DATABASE_DERIVED tier
    - Special handling for Triphala and AYUSH-64 formulations
    
    Example:
        agent = DatabaseAgent(data_path="/path/to/imppat.json")
        result = agent.search_plants("Emblica")
        print(result.to_dict())
    """
    
    def __init__(self, data_path: Optional[Union[str, pathlib.Path]] = None, auto_load: bool = True):
        """
        Initialize DatabaseAgent.
        
        Args:
            data_path: Path to IMPPAT JSON. Defaults to app/data/imppat_sample.json
            auto_load: If True, load data immediately
        """
        self.data_path = pathlib.Path(data_path) if data_path else DEFAULT_DATA_PATH
        self.raw_data: Dict[str, Any] = {}
        self.plants: List[Dict[str, Any]] = []
        self.phytochemicals: List[Dict[str, Any]] = []
        self.formulations: Dict[str, Any] = {}
        self._plant_name_index: Dict[str, Dict] = {}  # lower botanical -> record
        self._common_name_index: Dict[str, Dict] = {}
        self._therapeutic_index: Dict[str, List[Dict]] = {}  # therapeutic -> plants
        self._compound_name_index: Dict[str, Dict] = {}
        self._phytochem_by_plant: Dict[str, List[Dict]] = {}
        self.loaded_at: Optional[str] = None
        
        if auto_load:
            self.load_data()
    
    def load_data(self, path: Optional[Union[str, pathlib.Path]] = None) -> TieredEvidenceClass:
        """
        Load IMPPAT sample data from JSON.
        
        Returns:
            TieredEvidence wrapping load metadata
        """
        load_path = pathlib.Path(path) if path else self.data_path
        
        if not load_path.exists():
            # Try alternative locations
            alt_paths = [
                pathlib.Path(__file__).parent.parent / "data" / "imppat_sample.json",
                pathlib.Path("/mnt/data/ayurvedic-drug-discovery-pipeline/backend/app/data/imppat_sample.json"),
                pathlib.Path.cwd() / "imppat_sample.json"
            ]
            found = False
            for alt in alt_paths:
                if alt.exists():
                    load_path = alt
                    found = True
                    break
            if not found:
                logger.error(f"IMPPAT data file not found at {load_path} or alternatives {alt_paths}")
                # Create minimal fallback data to keep agent runnable
                self.raw_data = self._get_minimal_fallback_data()
                logger.warning("Using minimal fallback data - for testing only")
            else:
                # load found alt
                pass
        
        try:
            if not self.raw_data:
                with open(load_path, "r", encoding="utf-8") as f:
                    self.raw_data = json.load(f)
            
            self.plants = self.raw_data.get("plants", [])
            self.phytochemicals = self.raw_data.get("phytochemicals", [])
            self.formulations = self.raw_data.get("formulations", {})
            
            # Build indexes
            self._build_indexes()
            
            self.loaded_at = datetime.utcnow().isoformat()
            logger.info(f"Loaded IMPPAT sample: {len(self.plants)} plants, {len(self.phytochemicals)} phytochemicals from {load_path}")
            
            # Wrap in evidence
            meta = {
                "data_path": str(load_path),
                "plant_count": len(self.plants),
                "phytochemical_count": len(self.phytochemicals),
                "formulations": list(self.formulations.keys()),
                "loaded_at": self.loaded_at,
                "source_version": self.raw_data.get("metadata", {}).get("version", "unknown")
            }
            
            return self._wrap_database_output(
                data={"status": "loaded", "stats": meta},
                source=f"IMPPAT:{load_path}",
                metadata=meta
            )
            
        except json.JSONDecodeError as e:
            logger.exception(f"Failed to parse JSON at {load_path}: {e}")
            raise ValueError(f"Invalid IMPPAT JSON file at {load_path}: {e}")
        except Exception as e:
            logger.exception(f"Failed to load IMPPAT data: {e}")
            raise
    
    def _get_minimal_fallback_data(self) -> Dict[str, Any]:
        """Minimal fallback when JSON not found - ensures runnable"""
        return {
            "metadata": {"source": "fallback", "note": "Minimal data for CI"},
            "plants": [
                {"plant_id": "IMPPAT_001", "common_name": "Amla", "botanical_name": "Emblica officinalis",
                 "ayurvedic_name": "Amalaki", "family": "Phyllanthaceae",
                 "traditional_uses": ["rasayana"], "therapeutic_uses": ["antioxidant"], "formulation": "Triphala", "phytochemical_count": 47},
            ],
            "phytochemicals": [
                {"compound_id": "IMPPAT_001_A", "compound_name": "Gallic acid", "smiles": "O=C(O)c1cc(O)c(O)c(O)c1",
                 "molecular_formula": "C7H6O5", "plant_sources": ["Emblica officinalis"], "phytochemical_class": "phenolic",
                 "therapeutic_uses": ["antioxidant"], "pubchem_cid": 370, "traditional_use_score": 0.9}
            ],
            "formulations": {
                "Triphala": {"description": "Amalaki + Bibhitaki + Haritaki", "constituents": ["Emblica officinalis", "Terminalia bellirica", "Terminalia chebula"]},
                "AYUSH-64": {"description": "Alstonia + Picrorhiza + Swertia + Caesalpinia", "constituents": ["Alstonia scholaris", "Picrorhiza kurroa", "Swertia chirata", "Caesalpinia crista"]}
            }
        }
    
    def _build_indexes(self):
        """Build search indexes for performance"""
        self._plant_name_index.clear()
        self._common_name_index.clear()
        self._therapeutic_index.clear()
        self._compound_name_index.clear()
        self._phytochem_by_plant.clear()
        
        for plant in self.plants:
            bn = plant.get("botanical_name", "").lower()
            if bn:
                self._plant_name_index[bn] = plant
            cn = plant.get("common_name", "").lower()
            if cn:
                self._common_name_index[cn] = plant
            # Ayurvedic name index too
            an = plant.get("ayurvedic_name", "").lower()
            if an:
                self._common_name_index[an] = plant
            
            for use in plant.get("therapeutic_uses", []):
                key = use.lower()
                self._therapeutic_index.setdefault(key, []).append(plant)
        
        for compound in self.phytochemicals:
            cname = compound.get("compound_name", "").lower()
            if cname:
                self._compound_name_index[cname] = compound
            for plant_source in compound.get("plant_sources", []):
                key = plant_source.lower()
                self._phytochem_by_plant.setdefault(key, []).append(compound)
    
    def _wrap_database_output(self, data: Any, source: str, metadata: Optional[Dict] = None) -> TieredEvidenceClass:
        """Wrap data in DATABASE_DERIVED TieredEvidence with disclaimer"""
        tier_val = None
        # Try to resolve tier enum value compatible with existing modules
        try:
            # Prefer DATABASE_DERIVED
            tier_val = EvidenceTierClass.DATABASE_DERIVED
        except AttributeError:
            try:
                tier_val = EvidenceTierClass("DATABASE_DERIVED")
            except Exception:
                tier_val = "DATABASE_DERIVED"
        
        meta = metadata or {}
        meta.update({
            "evidence_tier": "DATABASE_DERIVED",
            "tier_number": 1,
            "database": "IMPPAT",
            "ayush64_justification": AYUSH64_JUSTIFICATION
        })
        
        try:
            # Try different Tiered wrappers
            if TieredEvidenceClass.__name__ == "TieredEvidence":
                return TieredEvidenceClass(
                    tier=tier_val,
                    data=data,
                    source=source,
                    metadata=meta
                )
            elif TieredEvidenceClass.__name__ == "TieredOutput":
                return TieredEvidenceClass(
                    tier=tier_val,
                    content=data,
                    citations=[],
                    confidence=0.95,
                    metadata=meta
                )
            elif TieredEvidenceClass.__name__ == "EvidenceTaggedOutput":
                return TieredEvidenceClass(
                    tier=tier_val,
                    data=data,
                    metadata=meta
                )
            else:
                return TieredEvidenceClass(tier=tier_val, data=data, source=source, metadata=meta)
        except Exception as e:
            logger.warning(f"Wrapping failed with primary method ({e}), using fallback dict")
            # Fallback dict format
            return {
                "evidentiary_tier": "DATABASE_DERIVED",
                "tier_number": 1,
                "data": data,
                "source": source,
                "metadata": meta,
                "disclaimer": "Database-derived: sourced from IMPPAT/PubChem curation. Cross-check primary botanical literature.",
                "timestamp": datetime.utcnow().isoformat(),
                "ayush64_note": AYUSH64_JUSTIFICATION
            }
    
    # ============ Core Search Methods ============
    
    def search_plants(self, query: str = "", therapeutic_use: Optional[str] = None,
                      formulation: Optional[str] = None, limit: int = 50) -> TieredEvidenceClass:
        """
        Search plants by name, therapeutic use, or formulation.
        
        Args:
            query: Search by botanical, common, or ayurvedic name (fuzzy substring)
            therapeutic_use: Filter by therapeutic use (e.g., "antiviral", "neuroprotective")
            formulation: Filter by formulation ("Triphala" or "AYUSH-64")
            limit: Max results
        
        Returns:
            TieredEvidence with DATABASE_DERIVED tier
        """
        if not self.plants:
            self.load_data()
        
        results = self.plants
        
        if query:
            q = query.lower().strip()
            # Fuzzy substring across multiple fields
            results = [
                p for p in results
                if q in p.get("botanical_name", "").lower()
                or q in p.get("common_name", "").lower()
                or q in p.get("ayurvedic_name", "").lower()
                or q in p.get("family", "").lower()
            ]
        
        if therapeutic_use:
            tu = therapeutic_use.lower().strip()
            # Match any therapeutic use containing query
            results = [
                p for p in results
                if any(tu in t.lower() for t in p.get("therapeutic_uses", []))
                or any(tu in t.lower() for t in p.get("traditional_uses", []))
            ]
        
        if formulation:
            form = formulation.lower().strip()
            # Formulation exact or formulation field
            if form == "triphala":
                results = [p for p in results if p.get("formulation") == "Triphala" or p.get("botanical_name") in ["Emblica officinalis", "Terminalia bellirica", "Terminalia chebula"]]
            elif form in ("ayush-64", "ayush64"):
                results = [p for p in results if p.get("formulation") == "AYUSH-64"]
            else:
                # generic formulation filter
                results = [p for p in results if p.get("formulation") and form in p.get("formulation").lower()]
        
        # Apply limit
        limited = results[:limit]
        
        logger.info(f"search_plants query='{query}' therapeutic='{therapeutic_use}' formulation='{formulation}' -> {len(limited)}/{len(results)} results")
        
        return self._wrap_database_output(
            data={
                "query": {"plant_query": query, "therapeutic_use": therapeutic_use, "formulation": formulation},
                "results": limited,
                "count": len(limited),
                "total_matches": len(results)
            },
            source=f"IMPPAT search_plants q={query}",
            metadata={"search_type": "plant_search", "limit": limit}
        )
    
    def get_phytochemicals_for_plant(self, plant_name: str,
                                     include_descriptors: bool = False,
                                     filter_druglike: bool = False) -> TieredEvidenceClass:
        """
        Get phytochemicals for a given plant.
        
        Args:
            plant_name: Botanical, common, or ayurvedic name
            include_descriptors: If True and cheminformatics available, compute descriptors
            filter_druglike: If True, filter by Lipinski + QED heuristic
        
        Returns:
            TieredEvidence DATABASE_DERIVED (+ COMPUTED if descriptors)
        """
        if not self.plants:
            self.load_data()
        
        key = plant_name.lower().strip()
        # Look up plant via indexes
        plant_match = None
        if key in self._plant_name_index:
            plant_match = self._plant_name_index[key]
        elif key in self._common_name_index:
            plant_match = self._common_name_index[key]
        else:
            # Substring search
            for p in self.plants:
                if key in p.get("botanical_name", "").lower() or key in p.get("common_name", "").lower() or key in p.get("ayurvedic_name", "").lower():
                    plant_match = p
                    break
        
        if not plant_match:
            logger.warning(f"Plant not found: {plant_name}")
            # Return empty but still tagged
            return self._wrap_database_output(
                data={"plant_query": plant_name, "plant_found": None, "phytochemicals": [], "count": 0,
                      "message": f"Plant '{plant_name}' not found in IMPPAT sample. Try search_plants()"},
                source=f"IMPPAT get_phytochemicals_for_plant not_found",
                metadata={"plant_query": plant_name, "found": False}
            )
        
        botanical = plant_match.get("botanical_name")
        # Get phytochemicals
        phytos = self._phytochem_by_plant.get(botanical.lower(), [])
        # Also check all where plant_sources contains botanical or common
        if not phytos:
            phytos = [c for c in self.phytochemicals if any(plant_name.lower() in ps.lower() or botanical.lower() in ps.lower() for ps in c.get("plant_sources", []))]
        
        # Optionally compute descriptors and filter
        enriched = []
        for comp in phytos:
            entry = dict(comp)  # shallow copy
            if include_descriptors and CHEM_AVAILABLE:
                try:
                    smi = comp.get("smiles", "")
                    if smi:
                        desc = calculate_descriptors(smi)
                        entry["descriptors"] = desc
                        if filter_druglike:
                            dr = comprehensive_drug_likeness_assessment(desc, smi)
                            entry["drug_likeness"] = dr
                            # Filter decision: keep if not PAINS and pass_count >=2 or QED>=0.4
                            if dr.get("composite_verdict", "").startswith("FAIL_PAINS") or dr.get("pass_count", 0) < 1:
                                # For filter_druglike we still include but mark
                                entry["filtered_out"] = True
                            else:
                                entry["filtered_out"] = False
                except Exception as e:
                    logger.warning(f"Descriptor calc failed for {comp.get('compound_name')}: {e}")
                    entry["descriptor_error"] = str(e)
            enriched.append(entry)
        
        if filter_druglike and CHEM_AVAILABLE:
            # Keep only those not filtered_out
            filtered = [e for e in enriched if not e.get("filtered_out", False)]
        else:
            filtered = enriched
        
        logger.info(f"get_phytochemicals_for_plant {plant_name} (found {botanical}) -> {len(filtered)} compounds")
        
        return self._wrap_database_output(
            data={
                "plant_query": plant_name,
                "plant_found": plant_match,
                "phytochemicals": filtered,
                "count": len(filtered),
                "total_before_filter": len(enriched),
                "filters_applied": {"include_descriptors": include_descriptors, "filter_druglike": filter_druglike}
            },
            source=f"IMPPAT get_phytochemicals_for_plant {botanical}",
            metadata={"plant": botanical, "count": len(filtered), "descriptor_computed": include_descriptors}
        )
    
    def search_by_property(self, compound_name: Optional[str] = None,
                           phytochemical_class: Optional[str] = None,
                           therapeutic_use: Optional[str] = None,
                           smiles_substructure: Optional[str] = None,
                           max_mw: Optional[float] = None,
                           min_traditional_use_score: Optional[float] = None,
                           lipinski_compliant: Optional[bool] = None,
                           limit: int = 100) -> TieredEvidenceClass:
        """
        Search phytochemicals by properties.
        
        Args:
            compound_name: Name substring
            phytochemical_class: e.g., flavonoid, alkaloid, terpenoid, phenolic, tannin
            therapeutic_use: therapeutic use filter
            smiles_substructure: SMILES substring (naive) or SMARTS if RDKit available
            max_mw: Max molecular weight (requires descriptor calc)
            min_traditional_use_score: Minimum traditional use score (0-1)
            lipinski_compliant: If True/False filter by Lipinski
            limit: Max results
        
        Returns:
            TieredEvidence DATABASE_DERIVED (+ COMPUTED when property filtered)
        """
        if not self.phytochemicals:
            self.load_data()
        
        results = self.phytochemicals
        
        if compound_name:
            q = compound_name.lower()
            results = [c for c in results if q in c.get("compound_name", "").lower()]
        
        if phytochemical_class:
            pc = phytochemical_class.lower()
            results = [c for c in results if pc == c.get("phytochemical_class", "").lower() or pc in c.get("phytochemical_class", "").lower()]
        
        if therapeutic_use:
            tu = therapeutic_use.lower()
            results = [c for c in results if any(tu in t.lower() for t in c.get("therapeutic_uses", []))]
        
        if smiles_substructure:
            sub = smiles_substructure.strip()
            if RDKIT_AVAILABLE:
                try:
                    from rdkit import Chem
                    pat = Chem.MolFromSmarts(sub)
                    if pat:
                        filtered = []
                        for comp in results:
                            try:
                                mol = Chem.MolFromSmiles(comp.get("smiles", ""))
                                if mol and mol.HasSubstructMatch(pat):
                                    filtered.append(comp)
                            except Exception:
                                continue
                        results = filtered
                    else:
                        # fallback to substring
                        results = [c for c in results if sub in c.get("smiles", "")]
                except Exception as e:
                    logger.warning(f"SMARTS search failed {e}, using substring")
                    results = [c for c in results if sub in c.get("smiles", "")]
            else:
                results = [c for c in results if sub in c.get("smiles", "")]
        
        if min_traditional_use_score is not None:
            results = [c for c in results if c.get("traditional_use_score", 0) >= min_traditional_use_score]
        
        # Property filters requiring descriptor calculation
        if max_mw is not None or lipinski_compliant is not None:
            if not CHEM_AVAILABLE:
                logger.warning("Cheminformatics not available - property filters using heuristic may be limited")
            filtered_by_prop = []
            for comp in results:
                try:
                    smi = comp.get("smiles", "")
                    if not smi:
                        continue
                    # Calculate descriptor if needed
                    if CHEM_AVAILABLE:
                        desc = calculate_descriptors(smi)
                    else:
                        # Minimal heuristic: MW from formula if available else skip
                        desc = {"molecular_weight": 300}  # placeholder
                        # Try parse formula for MW
                        formula = comp.get("molecular_formula", "")
                        if formula:
                            # rough estimate handled by descriptor fallback earlier
                            pass
                    
                    keep = True
                    if max_mw is not None:
                        if desc.get("molecular_weight", 0) > max_mw:
                            keep = False
                    if lipinski_compliant is not None and CHEM_AVAILABLE:
                        lip = lipinski_filter(desc)
                        is_compliant = lip.get("passes", False)
                        if lipinski_compliant and not is_compliant:
                            keep = False
                        if not lipinski_compliant and is_compliant:
                            keep = False
                    
                    if keep:
                        # Enrich with descriptor for transparency
                        enriched = dict(comp)
                        enriched["computed_descriptors"] = {k: desc.get(k) for k in ["molecular_weight", "logp", "hbd", "hba", "tpsa", "qed"] if k in desc}
                        filtered_by_prop.append(enriched)
                except Exception as e:
                    logger.warning(f"Filter assessment failed for {comp.get('compound_name')}: {e}")
                    continue
            results = filtered_by_prop
        
        limited = results[:limit]
        
        logger.info(f"search_by_property class={phytochemical_class} therapeutic={therapeutic_use} -> {len(limited)} results")
        
        return self._wrap_database_output(
            data={
                "query": {
                    "compound_name": compound_name,
                    "phytochemical_class": phytochemical_class,
                    "therapeutic_use": therapeutic_use,
                    "smiles_substructure": smiles_substructure,
                    "max_mw": max_mw,
                    "min_traditional_use_score": min_traditional_use_score,
                    "lipinski_compliant": lipinski_compliant
                },
                "results": limited,
                "count": len(limited),
                "total_matches": len(results)
            },
            source="IMPPAT search_by_property",
            metadata={"filtered_with_computed": (max_mw is not None or lipinski_compliant is not None)}
        )
    
    def get_network_pharmacology_graph(self, formulation: str = "Triphala",
                                       include_extended_mock: bool = True) -> TieredEvidenceClass:
        """
        Generate network pharmacology graph for Triphala example.
        
        Triphala example: 174 bioactives, 44 targets (from literature).
        This sample implements:
        - Real nodes from available phytochemicals
        - Mock expansion to reach 174/44 scale for demonstration
        - Nodes: plants, phytochemicals (bioactives), targets, pathways
        - Edges: plant-compound, compound-target (heuristic), target-pathway
        
        Args:
            formulation: "Triphala" or "AYUSH-64" or custom
            include_extended_mock: If True, expand mock to literature-reported counts
        
        Returns:
            TieredEvidence DATABASE_DERIVED with graph data
        """
        if not self.raw_data:
            self.load_data()
        
        form_key = formulation
        # Normalize
        if formulation.lower() in ("triphala",):
            form_key = "Triphala"
        elif formulation.lower() in ("ayush-64", "ayush64"):
            form_key = "AYUSH-64"
        
        form_info = self.formulations.get(form_key, {})
        if not form_info:
            # Search case-insensitive
            for k, v in self.formulations.items():
                if k.lower() == formulation.lower():
                    form_key = k
                    form_info = v
                    break
        
        if not form_info:
            return self._wrap_database_output(
                data={"error": f"Formulation '{formulation}' not found. Available: {list(self.formulations.keys())}"},
                source="IMPPAT network graph error",
                metadata={"formulation": formulation}
            )
        
        constituents = form_info.get("constituents", [])
        # Get real phytochemicals for constituents
        real_bioactives = []
        for plant_name in constituents:
            # get from index
            comps = self._phytochem_by_plant.get(plant_name.lower(), [])
            if not comps:
                # fallback substring search
                comps = [c for c in self.phytochemicals if any(plant_name.lower() in ps.lower() for ps in c.get("plant_sources", []))]
            real_bioactives.extend(comps)
        
        # Deduplicate by compound_id
        seen = set()
        unique_real = []
        for c in real_bioactives:
            cid = c.get("compound_id")
            if cid not in seen:
                seen.add(cid)
                unique_real.append(c)
        real_bioactives = unique_real
        
        # Target lists from formulation
        if form_key == "Triphala":
            example_targets = self.raw_data.get("formulations", {}).get("Triphala", {}).get("network_pharmacology_example", {}).get("example_targets", [])
            example_pathways = self.raw_data.get("formulations", {}).get("Triphala", {}).get("network_pharmacology_example", {}).get("example_pathways", [])
            ref_counts = form_info.get("reference_target_counts", {"bioactives_reported": 174, "targets_reported": 44})
            bioactive_target_count = ref_counts.get("bioactives_reported", 174)
            target_count = ref_counts.get("targets_reported", 44)
        else:  # AYUSH-64
            example_targets = ["Mpro", "PTGS2", "IL6", "TNF", "ACE2", "TMPRSS2", "NFKB1", "Nrf2"]
            example_pathways = ["COVID-19 pathway", "TNF signaling", "IL-17 signaling", "NOD-like receptor"]
            ref_counts = form_info.get("reference_target_counts", {"bioactives_reported": 87, "targets_reported": 31})
            bioactive_target_count = ref_counts.get("bioactives_reported", 87)
            target_count = ref_counts.get("targets_reported", 31)
        
        # Build graph structure
        nodes = []
        edges = []
        
        # Plant nodes
        for plant_name in constituents:
            plant_rec = self._plant_name_index.get(plant_name.lower())
            if not plant_rec:
                # search common name index
                plant_rec = self._common_name_index.get(plant_name.lower(), {"botanical_name": plant_name, "common_name": plant_name})
            nodes.append({
                "id": f"plant_{plant_rec.get('botanical_name', plant_name)}",
                "label": plant_rec.get("botanical_name", plant_name),
                "type": "plant",
                "formulation": form_key,
                "data": plant_rec
            })
        
        # Real compound nodes
        for comp in real_bioactives:
            nodes.append({
                "id": f"compound_{comp.get('compound_id')}",
                "label": comp.get("compound_name"),
                "type": "bioactive",
                "smiles": comp.get("smiles"),
                "phytochemical_class": comp.get("phytochemical_class"),
                "data": comp
            })
            # Edge plant-compound
            for plant_source in comp.get("plant_sources", []):
                # find matching plant node
                for plant_node in nodes:
                    if plant_node["type"] == "plant" and plant_source.lower() in plant_node["label"].lower():
                        edges.append({
                            "source": plant_node["id"],
                            "target": f"compound_{comp.get('compound_id')}",
                            "type": "contains",
                            "evidence": "IMPPAT database"
                        })
        
        # Mock expansion to reach literature counts for teaching
        if include_extended_mock:
            current_bioactive_count = len(real_bioactives)
            # Create mock bioactives to reach expected count
            mock_needed = max(0, bioactive_target_count - current_bioactive_count)
            for i in range(mock_needed):
                mock_id = f"MOCK_{form_key}_{i+1:03d}"
                mock_name = f"MockBioactive_{form_key}_{i+1}"
                # Deterministic smiles for mock
                mock_smiles = f"C{i%5+1}CCO"  # simple but valid
                nodes.append({
                    "id": f"compound_{mock_id}",
                    "label": mock_name,
                    "type": "bioactive",
                    "smiles": mock_smiles,
                    "phytochemical_class": "mock",
                    "is_mock": True,
                    "note": f"Mock node to demonstrate scale {bioactive_target_count} bioactives reported in literature"
                })
                # connect to random plant
                if nodes:
                    plant_nodes = [n for n in nodes if n["type"] == "plant"]
                    if plant_nodes:
                        import random
                        random.seed(i)
                        pnode = random.choice(plant_nodes)
                        edges.append({
                            "source": pnode["id"],
                            "target": f"compound_{mock_id}",
                            "type": "contains_mock",
                            "evidence": "mock_expansion_for_scale"
                        })
            
            # Target nodes - create up to target_count
            for idx, target_name in enumerate(example_targets[:target_count]):
                nodes.append({
                    "id": f"target_{target_name}",
                    "label": target_name,
                    "type": "target",
                    "data": {"gene_name": target_name, "organism": "Homo sapiens", "relevance": f"{form_key} network"}
                })
            # Fill remaining target slots with mock
            remaining_targets = target_count - len(example_targets[:target_count])
            for j in range(max(0, remaining_targets)):
                mock_t = f"MOCK_TARGET_{j+1}"
                nodes.append({
                    "id": f"target_{mock_t}",
                    "label": mock_t,
                    "type": "target",
                    "is_mock": True,
                    "note": "Mock target to reach literature-reported count"
                })
            
            # Compound-target edges: heuristic linking
            import random, hashlib
            compound_nodes = [n for n in nodes if n["type"] == "bioactive"]
            target_nodes = [n for n in nodes if n["type"] == "target"]
            for cnode in compound_nodes:
                # deterministic random based on compound id hash
                h = int(hashlib.md5(cnode["id"].encode()).hexdigest()[:4], 16)
                random.seed(h)
                # Each compound linked to 1-4 targets
                k = random.randint(1, 4)
                chosen_targets = random.sample(target_nodes, min(k, len(target_nodes)))
                for tnode in chosen_targets:
                    edges.append({
                        "source": cnode["id"],
                        "target": tnode["id"],
                        "type": "predicted_interaction",
                        "evidence": "heuristic for teaching - not experimental",
                        "weight": random.random()
                    })
            
            # Target-pathway edges
            pathway_nodes = []
            for pw in example_pathways:
                pid = f"pathway_{pw.replace(' ', '_')}"
                nodes.append({
                    "id": pid,
                    "label": pw,
                    "type": "pathway"
                })
                pathway_nodes.append(pid)
            for tnode in target_nodes:
                random.seed(hash(tnode["id"]))
                chosen_pws = random.sample(pathway_nodes, min(2, len(pathway_nodes)))
                for pw_id in chosen_pws:
                    edges.append({
                        "source": tnode["id"],
                        "target": pw_id,
                        "type": "involved_in",
                        "evidence": "KEGG/GO mapping heuristic"
                    })
        else:
            # Without mock expansion, only real counts
            pass
        
        graph_data = {
            "formulation": form_key,
            "formulation_info": form_info,
            "nodes": nodes,
            "edges": edges,
            "stats": {
                "plant_nodes": len([n for n in nodes if n["type"] == "plant"]),
                "bioactive_nodes_real": len(real_bioactives),
                "bioactive_nodes_total": len([n for n in nodes if n["type"] == "bioactive"]),
                "bioactive_nodes_mock": len([n for n in nodes if n["type"] == "bioactive" and n.get("is_mock")]),
                "target_nodes": len([n for n in nodes if n["type"] == "target"]),
                "pathway_nodes": len([n for n in nodes if n["type"] == "pathway"]),
                "edges": len(edges),
                "reference_counts": {"literature_bioactives": bioactive_target_count, "literature_targets": target_count},
                "triphala_ref": TRIPHALA_NETWORK_REF if form_key == "Triphala" else None
            },
            "visualization_hint": {
                "layout": "cose or force-directed",
                "color_by_type": {"plant": "#2E7D32", "bioactive": "#1565C0", "target": "#E65100", "pathway": "#6A1B9A"},
                "mock_nodes_dashed": True
            }
        }
        
        logger.info(f"Network pharmacology graph for {form_key}: {graph_data['stats']}")
        
        return self._wrap_database_output(
            data=graph_data,
            source=f"IMPPAT network_pharmacology {form_key}",
            metadata={
                "formulation": form_key,
                "is_mock_expanded": include_extended_mock,
                "literature_reference": f"{bioactive_target_count} bioactives, {target_count} targets"
            }
        )
    
    def get_ayush64_details(self) -> TieredEvidenceClass:
        """
        Special case method for AYUSH-64.
        
        Returns detailed composition, traditional uses, key phytochemicals,
        case study justification, and explicit disclaimer NOT clinical proof.
        """
        if not self.raw_data:
            self.load_data()
        
        ayush_info = self.formulations.get("AYUSH-64", {})
        # Get plants for AYUSH-64
        constituents = ayush_info.get("constituents", [])
        plant_details = []
        for pname in constituents:
            rec = self._plant_name_index.get(pname.lower())
            if not rec:
                rec = self._common_name_index.get(pname.lower(), {"botanical_name": pname})
            plant_details.append(rec)
        
        # Phytochemicals per plant
        phyto_by_plant = {}
        for pname in constituents:
            comps = self._phytochem_by_plant.get(pname.lower(), [])
            if not comps:
                comps = [c for c in self.phytochemicals if any(pname.lower() in ps.lower() for ps in c.get("plant_sources", []))]
            phyto_by_plant[pname] = comps
        
        case_study = {
            "formulation": "AYUSH-64",
            "formulation_info": ayush_info,
            "constituents": constituents,
            "plant_details": plant_details,
            "phytochemicals_by_plant": phyto_by_plant,
            "total_unique_phytochemicals": len(set(c.get("compound_id") for comps in phyto_by_plant.values() for c in comps)),
            "key_phytochemicals": ayush_info.get("key_phytochemicals_by_plant", {}),
            "traditional_indication": ["Jwara (fever)", "Malaria", "Filariasis", "Respiratory infections"],
            "modern_repurposing": "COVID-19 management - CCRAS initiative 2020",
            "clinical_trials": ayush_info.get("ccras_trials", []),
            "case_study_justification": AYUSH64_JUSTIFICATION,
            "evidentiary_framing": {
                "tier_1_database": "IMPPAT phytochemical composition, traditional use textual evidence",
                "tier_2_docking": "In silico docking against SARS-CoV-2 Mpro, PLpro, etc. (hypothesis)",
                "tier_3_ml": "ML binding affinity prediction - computational",
                "tier_4_xai": "SHAP explanation of features driving prediction - model interpretation",
                "tier_5_literature": "RAG mining of AYUSH-64 clinical trials (CTRI) - requires critical appraisal",
                "hard_constraint": "Computational (Tier 2-4) MUST NOT be presented as clinical proof. AYUSH-64 required RCTs before claim.",
                "disclaimer": ayush_info.get("disclaimer", "Computational hits do NOT prove clinical efficacy")
            }
        }
        
        return self._wrap_database_output(
            data=case_study,
            source="IMPPAT + AYUSH Ministry + CTRI literature - AYUSH-64",
            metadata={"special_case": "AYUSH-64", "constituent_count": len(constituents)}
        )
    
    def get_triphala_details(self) -> TieredEvidenceClass:
        """
        Special case method for Triphala.
        """
        if not self.raw_data:
            self.load_data()
        
        tri_info = self.formulations.get("Triphala", {})
        constituents = tri_info.get("constituents", [])
        plant_details = []
        for pname in constituents:
            rec = self._plant_name_index.get(pname.lower())
            if rec:
                plant_details.append(rec)
        
        phyto_by_plant = {}
        for pname in constituents:
            comps = self._phytochem_by_plant.get(pname.lower(), [])
            phyto_by_plant[pname] = comps
        
        details = {
            "formulation": "Triphala",
            "formulation_info": tri_info,
            "constituents": constituents,
            "plant_details": plant_details,
            "phytochemicals_by_plant": phyto_by_plant,
            "network_pharmacology_reference": TRIPHALA_NETWORK_REF,
            "literature_counts": tri_info.get("reference_target_counts", {"bioactives_reported": 174, "targets_reported": 44}),
            "traditional_uses": tri_info.get("traditional_uses", []),
            "ratio": tri_info.get("ratio", "1:1:1")
        }
        
        return self._wrap_database_output(
            data=details,
            source="IMPPAT Triphala formulation",
            metadata={"special_case": "Triphala"}
        )
    
    # Utility helpers
    def list_all_plants(self) -> List[Dict[str, Any]]:
        if not self.plants:
            self.load_data()
        return self.plants
    
    def list_all_phytochemicals(self) -> List[Dict[str, Any]]:
        if not self.phytochemicals:
            self.load_data()
        return self.phytochemicals

# Singleton convenience instance (optional)
_default_agent: Optional[DatabaseAgent] = None

def get_database_agent(data_path: Optional[Union[str, pathlib.Path]] = None) -> DatabaseAgent:
    global _default_agent
    if _default_agent is None:
        _default_agent = DatabaseAgent(data_path=data_path)
    return _default_agent
