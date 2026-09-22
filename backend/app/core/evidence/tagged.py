"""
Evidence Tier Enforcement Module
================================
Central module for AYUSH-64 case study justification compliance.

FIVE evidentiary tiers:
1. DATABASE_DERIVED
2. DOCKING_RESULT
3. ML_PREDICTION
4. XAI_INTERPRETATION
5. LITERATURE_DERIVED

HARD CONSTRAINT: Must NOT present computational prediction as clinical proof.
All outputs must be tagged with evidentiary tier and disclaimer.

Reference: AYUSH-64 repurposing case study - shows computational evidence
requires experimental validation before clinical claims.
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime
import hashlib


class EvidenceTier(str, Enum):
    """
    Five-tier evidence classification per project spec.
    """
    DATABASE_DERIVED = "DATABASE_DERIVED"  # Tier 1: IMPPAT, PDB, ChEMBL curated data
    DOCKING_RESULT = "DOCKING_RESULT"  # Tier 2: AutoDock Vina / physics-based scoring
    ML_PREDICTION = "ML_PREDICTION"  # Tier 3: Supervised binding affinity predictions
    XAI_INTERPRETATION = "XAI_INTERPRETATION"  # Tier 4: SHAP/LIME explanations
    LITERATURE_DERIVED = "LITERATURE_DERIVED"  # Tier 5: RAG / LLM-synthesized literature

    @property
    def disclaimer(self) -> str:
        disclaimers = {
            self.DATABASE_DERIVED: "Curated database entry. Verify provenance and version.",
            self.DOCKING_RESULT: "Computational docking estimate. Requires experimental validation. NOT clinical proof.",
            self.ML_PREDICTION: "ML-predicted affinity. Applicability domain limited. Requires wet-lab validation. NOT clinical proof.",
            self.XAI_INTERPRETATION: "Explainability interpretation of model behavior, not causal biological mechanism. NOT clinical proof.",
            self.LITERATURE_DERIVED: "Literature-mined / LLM-synthesized evidence. Verify primary sources. NOT clinical proof.",
        }
        return disclaimers[self]

    @property
    def confidence_guidance(self) -> str:
        return {
            self.DATABASE_DERIVED: "High if source DB version documented",
            self.DOCKING_RESULT: "Medium; sensitive to pose, protonation, receptor flexibility",
            self.ML_PREDICTION: "Medium; check applicability domain & training distribution",
            self.XAI_INTERPRETATION: "Interpretive; triangulate multiple explainers",
            self.LITERATURE_DERIVED: "Variable; cross-check citations",
        }[self]


@dataclass
class EvidenceTaggedOutput:
    """
    Wrapper for all pipeline outputs to enforce tier tagging.
    """
    tier: EvidenceTier
    data: Any
    disclaimer: str = field(init=False)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)
    provenance_hash: Optional[str] = None

    def __post_init__(self):
        self.disclaimer = self.tier.disclaimer
        if self.provenance_hash is None and self.data is not None:
            try:
                self.provenance_hash = hashlib.sha256(
                    str(self.data).encode()[:10000]
                ).hexdigest()[:16]
            except Exception:
                self.provenance_hash = "unknown"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "evidentiary_tier": self.tier.value,
            "disclaimer": self.disclaimer,
            "confidence_guidance": self.tier.confidence_guidance,
            "timestamp": self.timestamp,
            "provenance_hash": self.provenance_hash,
            "metadata": self.metadata,
            "data": self.data,
        }

    def assert_not_clinical(self) -> None:
        """
        Guardrail: ensure no clinical claim is made.
        """
        forbidden = [
            "clinically proven",
            "efficacious in patients",
            "therapeutic dose",
            "cures",
            "treats disease",
            "clinical efficacy",
        ]
        data_str = str(self.data).lower() + str(self.metadata).lower()
        for phrase in forbidden:
            if phrase in data_str:
                raise ValueError(
                    f"Output violates HARD CONSTRAINT: contains clinical claim '{phrase}'. "
                    f"Tier {self.tier.value} cannot present computational prediction as clinical proof. "
                    f"AYUSH-64 justification: repurposing required experimental validation."
                )


# Singleton validator
class EvidenceValidator:
    @staticmethod
    def validate(output: EvidenceTaggedOutput) -> EvidenceTaggedOutput:
        output.assert_not_clinical()
        return output


# AYUSH-64 case study reference metadata
AYUSH64_JUSTIFICATION = {
    "case_study": "AYUSH-64",
    "context": (
        "Ayurvedic polyherbal formulation initially for malaria, repurposed for COVID-19 "
        "via computational screening and Ayurvedic textual inference. Demonstrates need "
        "for tiered evidence: in-silico predictions (Tier 3/4) must NOT be conflated with "
        "clinical proof. Required subsequent in-vitro, in-vivo, and controlled trials."
    ),
    "lesson": (
        "Computational pipeline outputs are hypotheses for prioritization, not clinical "
        "recommendations. Every output must carry tier tag and disclaimer."
    ),
    "reference_tiers": [t.value for t in EvidenceTier],
}
