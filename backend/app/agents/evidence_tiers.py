"""
Central Evidence Tier Enforcement Module
========================================
Implements the HARD CONSTRAINT that every pipeline output must map to one of
five evidentiary tiers and MUST NOT present computational prediction as clinical proof.

Tiers (as per project specification):
1. DATABASE_DERIVED       - info from curated databases (IMPPAT, etc.)
2. DOCKING_RESULT         - structure-based protein-ligand docking
3. ML_PREDICTION          - supervised ML binding-affinity prediction
4. XAI_INTERPRETATION     - explainable AI (SHAP etc.)
5. LITERATURE_DERIVED     - RAG-grounded literature / LLM synthesis

AYUSH-64 Case Study Justification:
AYUSH-64 (Alstonia scholaris, Picrorhiza kurroa, Swertia chirata, Caesalpinia crista)
was computationally predicted to bind SARS-CoV-2 Mpro, then validated via in vitro
and clinical studies. Computational predictions alone were NEVER claimed as clinical
proof; they served as hypothesis prioritization. This pipeline enforces same principle.

Includes Tippy safety guardrail pattern: validate -> sanitize -> enforce.
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field, asdict
from datetime import datetime
import re
import logging

logger = logging.getLogger(__name__)


class EvidenceTier(str, Enum):
    """Five evidentiary tiers - exhaustive, mutually exclusive."""
    DATABASE_DERIVED = "database_derived"
    DOCKING_RESULT = "molecular_docking_result"
    ML_PREDICTION = "machine_learning_prediction"
    XAI_INTERPRETATION = "explainable_ai_interpretation"
    LITERATURE_DERIVED = "literature_derived_llm_synthesized"

    @property
    def tier_number(self) -> int:
        mapping = {
            EvidenceTier.DATABASE_DERIVED: 1,
            EvidenceTier.DOCKING_RESULT: 2,
            EvidenceTier.ML_PREDICTION: 3,
            EvidenceTier.XAI_INTERPRETATION: 4,
            EvidenceTier.LITERATURE_DERIVED: 5,
        }
        return mapping[self]

    @property
    def description(self) -> str:
        return {
            EvidenceTier.DATABASE_DERIVED: "Information derived from curated phytochemical / traditional medicine databases (IMPPAT primary)",
            EvidenceTier.DOCKING_RESULT: "Structure-based protein-ligand molecular docking result (AutoDock Vina style)",
            EvidenceTier.ML_PREDICTION: "Supervised ML binding-affinity prediction",
            EvidenceTier.XAI_INTERPRETATION: "Explainable AI interpretation (SHAP values)",
            EvidenceTier.LITERATURE_DERIVED: "Scientific literature mining via RAG, LLM-synthesized with citations",
        }[self]

    @property
    def confidence_ceiling(self) -> str:
        """Maximum claim strength allowed per tier - prevents clinical overclaim."""
        return {
            EvidenceTier.DATABASE_DERIVED: "database record - requires experimental validation",
            EvidenceTier.DOCKING_RESULT: "computational docking prediction - NOT clinical proof - requires wet-lab validation",
            EvidenceTier.ML_PREDICTION: "ML predicted affinity - computational hypothesis - NOT clinical efficacy",
            EvidenceTier.XAI_INTERPRETATION: "model explanation - feature importance - NOT mechanistic proof",
            EvidenceTier.LITERATURE_DERIVED: "literature-synthesized evidence - requires critical appraisal - NOT direct clinical proof unless source is clinical trial",
        }[self]


# Clinical overclaim patterns - MUST be blocked
CLINICAL_OVERCLAIM_PATTERNS = [
    r"\bclinically proven\b",
    r"\bproven to cure\b",
    r"\bproven to treat\b",
    r"\beffective treatment\b.*\bfor patients\b",
    r"\bclinical efficacy\b.*\bdemonstrated\b",
    r"\bwill cure\b",
    r"\bguaranteed to work\b",
    r"\bsafe and effective\b.*\bin humans\b",
    r"\btherapeutic effect\b.*\bconfirmed\b",
    r"\bcan be used to treat patients\b",
    r"\bclinical proof\b",
]

# Allowed disclaimer templates
SAFETY_DISCLAIMER_TEMPLATE = (
    "[{tier_label}] This is a {tier_desc}. "
    "This computational/literature-derived result is a hypothesis for prioritization "
    "and does NOT constitute clinical proof of safety or efficacy. "
    "Requires experimental validation. Inspired by AYUSH-64 development pathway: "
    "in silico -> in vitro -> clinical studies."
)


@dataclass
class Citation:
    """Structured citation to prevent hallucination."""
    id: str  # must map to corpus id
    title: str
    authors: List[str]
    year: int
    doi: Optional[str] = None
    journal: Optional[str] = None
    evidence_type: str = "literature"  # literature, database, etc.
    snippet: Optional[str] = None  # grounded text span


@dataclass
class TieredOutput:
    """Every agent output MUST be wrapped in this with an evidence tier."""
    tier: EvidenceTier
    content: Any
    citations: List[Citation] = field(default_factory=list)
    confidence: float = 0.0  # 0-1
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    safety_disclaimer: str = ""
    validated: bool = False

    def __post_init__(self):
        if not self.safety_disclaimer:
            self.safety_disclaimer = SAFETY_DISCLAIMER_TEMPLATE.format(
                tier_label=self.tier.name,
                tier_desc=self.tier.confidence_ceiling
            )
        # Enforce confidence ceiling check
        if self.tier in [EvidenceTier.DOCKING_RESULT, EvidenceTier.ML_PREDICTION]:
            if self.confidence > 0.95:
                logger.warning(f"Confidence capped for {self.tier}: {self.confidence} -> 0.95 (computational cannot be 100%)")
                self.confidence = min(self.confidence, 0.95)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d['tier'] = self.tier.value
        d['tier_number'] = self.tier.tier_number
        return d

    def add_citation(self, citation: Citation):
        self.citations.append(citation)

    def is_compliant(self) -> bool:
        """Check compliance internally."""
        if not self.tier:
            return False
        # LITERATURE_DERIVED must have citations
        if self.tier == EvidenceTier.LITERATURE_DERIVED and len(self.citations) == 0:
            logger.warning("LITERATURE_DERIVED output without citations")
            return False
        return True


def enforce_evidence_tier(tier: EvidenceTier):
    """Decorator to enforce tier tagging on agent methods."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            if isinstance(result, TieredOutput):
                if result.tier != tier:
                    logger.warning(f"Tier mismatch: expected {tier}, got {result.tier}")
                return result
            # Wrap raw dict/list into TieredOutput
            if isinstance(result, dict):
                return TieredOutput(
                    tier=tier,
                    content=result,
                    confidence=result.get('confidence', 0.5),
                    metadata=result.get('metadata', {})
                )
            return TieredOutput(tier=tier, content=result, confidence=0.5)
        return wrapper
    return decorator


def validate_no_clinical_overclaim(text: str) -> tuple[bool, List[str]]:
    """
    Safety guardrail pattern from Tippy:
    Detects if text presents computational prediction as clinical proof.
    Returns (is_safe, violations)
    """
    violations = []
    text_lower = text.lower()
    for pattern in CLINICAL_OVERCLAIM_PATTERNS:
        matches = re.findall(pattern, text_lower, flags=re.IGNORECASE)
        if matches:
            violations.append(f"Pattern '{pattern}' matched: {matches}")
    # Additional heuristic: if computational tier language + "treats/cures patients"
    if any(w in text_lower for w in ["docking score", "predicted affinity", "ml model"]) and \
       any(w in text_lower for w in ["cures covid", "treats patients effectively", "proven effective in humans"]):
        violations.append("Computational term combined with clinical efficacy claim")
    is_safe = len(violations) == 0
    return is_safe, violations


class EvidenceTierRegistry:
    """Central registry tracking all outputs."""
    def __init__(self):
        self.outputs: List[TieredOutput] = []

    def register(self, output: TieredOutput):
        if not isinstance(output, TieredOutput):
            raise ValueError(f"All outputs must be TieredOutput, got {type(output)}")
        if not output.is_compliant():
            raise ValueError(f"Non-compliant TieredOutput: tier={output.tier}")
        self.outputs.append(output)
        logger.info(f"Registered output: tier={output.tier.value} confidence={output.confidence}")

    def get_by_tier(self, tier: EvidenceTier) -> List[TieredOutput]:
        return [o for o in self.outputs if o.tier == tier]

    def generate_tier_summary(self) -> Dict[str, Any]:
        summary = {}
        for tier in EvidenceTier:
            tier_outputs = self.get_by_tier(tier)
            summary[tier.value] = {
                "tier_number": tier.tier_number,
                "count": len(tier_outputs),
                "avg_confidence": sum(o.confidence for o in tier_outputs) / len(tier_outputs) if tier_outputs else 0,
                "description": tier.description,
                "confidence_ceiling": tier.confidence_ceiling
            }
        return summary


# Global registry instance
global_registry = EvidenceTierRegistry()
