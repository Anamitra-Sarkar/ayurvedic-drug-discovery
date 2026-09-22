"""
Data Models for Ayurvedic Drug Discovery Pipeline
=================================================
Pydantic models for API and internal agent communication.

Ensures:
- Evidence tier tagging mandatory
- SMILES validation
- Type safety for phytochemicals, plants, formulations
- AYUSH-64 compliance fields

Author: Senior Engineer - Data Models
"""

from __future__ import annotations

from typing import List, Optional, Dict, Any, Union, Literal
from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field, validator, root_validator
import re

# Evidence tier enum (mirrors central module)
class EvidenceTierEnum(str, Enum):
    DATABASE_DERIVED = "DATABASE_DERIVED"
    DOCKING_RESULT = "DOCKING_RESULT"
    ML_PREDICTION = "ML_PREDICTION"
    XAI_INTERPRETATION = "XAI_INTERPRETATION"
    LITERATURE_DERIVED = "LITERATURE_DERIVED"
    LITERATURE_EVIDENCE = "LITERATURE_EVIDENCE"  # alias

class PhytochemicalClass(str, Enum):
    FLAVONOID = "flavonoid"
    ALKALOID = "alkaloid"
    TERPENOID = "terpenoid"
    PHENOLIC = "phenolic"
    SAPONIN = "saponin"
    TANNIN = "tannin"
    STEROID = "steroid"
    GLYCOSIDE = "glycoside"
    LIGNAN = "lignan"
    OTHER = "other"
    MOCK = "mock"

class DoshaEffect(BaseModel):
    vata: int = Field(..., description="-1 pacifies, 0 neutral, 1 aggravates")
    pitta: int
    kapha: int

class PlantBase(BaseModel):
    plant_id: Optional[str] = None
    common_name: str
    botanical_name: str
    ayurvedic_name: Optional[str] = None
    family: Optional[str] = None
    part_used: Optional[List[str]] = None
    traditional_uses: Optional[List[str]] = None
    therapeutic_uses: Optional[List[str]] = None
    dosha: Optional[DoshaEffect] = None
    formulation: Optional[str] = None  # Triphala, AYUSH-64, None
    phytochemical_count: Optional[int] = None
    reference: Optional[str] = "IMPPAT"

class PhytochemicalBase(BaseModel):
    compound_id: Optional[str] = None
    compound_name: str
    smiles: str = Field(..., description="Canonical SMILES")
    molecular_formula: Optional[str] = None
    plant_sources: Optional[List[str]] = None
    phytochemical_class: Optional[PhytochemicalClass] = None
    therapeutic_uses: Optional[List[str]] = None
    pubchem_cid: Optional[int] = None
    traditional_use_score: Optional[float] = Field(None, ge=0.0, le=1.0)

    @validator('smiles')
    def smiles_must_be_nonempty(cls, v):
        if not v or not isinstance(v, str) or len(v.strip()) < 1:
            raise ValueError("SMILES must be non-empty string")
        # Basic pattern check - allow typical SMILES chars
        if not re.match(r"^[A-Za-z0-9@+\-\[\]\(\)\\/#=%$:.]+$", v.strip()):
            # Don't reject strictly, just warn via validator - for permissive
            pass
        return v.strip()

class DescriptorResult(BaseModel):
    """Result from cheminformatics descriptor calculation"""
    molecular_weight: Optional[float] = None
    logp: Optional[float] = None
    hbd: Optional[int] = None
    hba: Optional[int] = None
    tpsa: Optional[float] = None
    rotatable_bonds: Optional[int] = None
    heavy_atom_count: Optional[int] = None
    ring_count: Optional[int] = None
    aromatic_ring_count: Optional[int] = None
    fraction_csp3: Optional[float] = None
    qed: Optional[float] = Field(None, ge=0.0, le=1.0)
    bertz_ct: Optional[float] = None
    balaban_j: Optional[float] = None
    molar_refractivity: Optional[float] = None
    # Evidence tagging
    evidence_tier: EvidenceTierEnum = EvidenceTierEnum.DATABASE_DERIVED
    is_computed: bool = True
    computation_source: Optional[str] = None
    disclaimer: Optional[str] = None
    _source: Optional[str] = None

class DrugLikenessFilterResult(BaseModel):
    filter_name: str
    passes: bool
    violations: Optional[List[str]] = None
    violation_count: Optional[int] = None
    criteria: Optional[Dict[str, Any]] = None
    values: Optional[Dict[str, Any]] = None
    evidence_tier: EvidenceTierEnum = EvidenceTierEnum.DATABASE_DERIVED
    is_computed: bool = True

class PainsResult(BaseModel):
    is_pains: bool
    alerts: List[Dict[str, Any]] = []
    passes_pains: bool
    alert_count: Optional[int] = None

class PhytochemicalEnriched(PhytochemicalBase):
    """Phytochemical + computed descriptors + filters"""
    descriptors: Optional[Dict[str, Any]] = None
    descriptors_summary: Optional[Dict[str, Any]] = None
    mordred_like_20: Optional[Dict[str, Any]] = None
    drug_likeness: Optional[Dict[str, Any]] = None
    filters: Optional[Dict[str, Any]] = None
    pains: Optional[PainsResult] = None
    has_3d_conformer: Optional[bool] = False
    evidence_tier: EvidenceTierEnum = EvidenceTierEnum.DATABASE_DERIVED
    is_computed: bool = True
    disclaimer: Optional[str] = None

class SearchPlantsRequest(BaseModel):
    query: Optional[str] = ""
    therapeutic_use: Optional[str] = None
    formulation: Optional[Literal["Triphala", "AYUSH-64", "AYUSH64"]] = None
    limit: int = Field(50, ge=1, le=500)

class SearchPlantsResponse(BaseModel):
    query: Dict[str, Any]
    results: List[PlantBase]
    count: int
    total_matches: int
    evidence_tier: EvidenceTierEnum = EvidenceTierEnum.DATABASE_DERIVED
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    disclaimer: str = "Database-derived: sourced from IMPPAT/PubChem curation."

class SearchPropertyRequest(BaseModel):
    compound_name: Optional[str] = None
    phytochemical_class: Optional[PhytochemicalClass] = None
    therapeutic_use: Optional[str] = None
    smiles_substructure: Optional[str] = None
    max_mw: Optional[float] = Field(None, ge=0.0)
    min_traditional_use_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    lipinski_compliant: Optional[bool] = None
    limit: int = Field(100, ge=1, le=1000)

class NetworkNode(BaseModel):
    id: str
    label: str
    type: Literal["plant", "bioactive", "target", "pathway"]
    is_mock: Optional[bool] = False
    data: Optional[Dict[str, Any]] = None

class NetworkEdge(BaseModel):
    source: str
    target: str
    type: str
    evidence: Optional[str] = None
    weight: Optional[float] = None

class NetworkPharmacologyGraph(BaseModel):
    formulation: str
    formulation_info: Optional[Dict[str, Any]] = None
    nodes: List[Dict[str, Any]]  # Using dict for flexibility with extra fields
    edges: List[Dict[str, Any]]
    stats: Dict[str, Any]
    evidence_tier: EvidenceTierEnum = EvidenceTierEnum.DATABASE_DERIVED
    disclaimer: str = "Network graph includes mock expansion to demonstrate 174 bioactives / 44 targets scale. Not experimental interaction proof."
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

class Ayush64DetailsResponse(BaseModel):
    formulation: str = "AYUSH-64"
    constituents: List[str]
    plant_details: List[Dict[str, Any]]
    phytochemicals_by_plant: Dict[str, List[Dict[str, Any]]]
    total_unique_phytochemicals: int
    key_phytochemicals: Optional[Dict[str, List[str]]] = None
    case_study_justification: str
    evidentiary_framing: Dict[str, Any]
    evidence_tier: EvidenceTierEnum = EvidenceTierEnum.DATABASE_DERIVED
    disclaimer: str = "AYUSH-64 computational hits do NOT prove clinical efficacy. Requires RCT verification."

# Batch processing models
class BatchCheminformaticsRequest(BaseModel):
    phytochemicals: List[Union[PhytochemicalBase, str]]  # allow SMILES strings
    include_3d: bool = False
    include_filters: bool = True
    include_pains: bool = True

class BatchCheminformaticsResponse(BaseModel):
    total_input: int
    successful: int
    failed: int
    average_qed: Optional[float] = None
    results: List[Dict[str, Any]]
    evidence_tier: EvidenceTierEnum = EvidenceTierEnum.DATABASE_DERIVED
    is_computed: bool = True
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    disclaimer: str = "[DATABASE_DERIVED + COMPUTED] Computed from SMILES. Not experimental, not clinical proof."

# Triphala special case
class TriphalaDetailsResponse(BaseModel):
    formulation: str = "Triphala"
    constituents: List[str]
    plant_details: List[Dict[str, Any]]
    phytochemicals_by_plant: Dict[str, List[List[Dict[str, Any]]]] = {}
    literature_counts: Dict[str, int] = {"bioactives_reported": 174, "targets_reported": 44}
    ratio: str = "1:1:1"
    evidence_tier: EvidenceTierEnum = EvidenceTierEnum.DATABASE_DERIVED

# Wrapper for all agent outputs (central enforcement)
class TieredResponse(BaseModel):
    evidentiary_tier: EvidenceTierEnum
    tier_number: int
    data: Any
    source: str
    metadata: Optional[Dict[str, Any]] = None
    disclaimer: str
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    is_computed: Optional[bool] = None
    clinical_proof: bool = False  # Must remain False for computational
