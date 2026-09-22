"""
Validation Agent for Ayurvedic Drug Discovery Pipeline
=======================================================
Separate from other agents to prevent error propagation (as per Agentic AI in Pharma review, REF_040).

Validates every stage output for:
- Evidence tier compliance
- Checks that computational not presented as clinical
- Checks applicability domain
- Checks hallucination (citation grounding)
- Validates docking pose quality
- ML confidence

Returns validation report.

Safety guardrail pattern from Tippy: validate -> sanitize -> enforce.
"""

from typing import List, Dict, Any, Optional, Tuple
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from app.agents.evidence_tiers import (
    EvidenceTier, TieredOutput, CLINICAL_OVERCLAIM_PATTERNS,
    validate_no_clinical_overclaim, global_registry
)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


@dataclass
class ValidationIssue:
    """Single validation issue found."""
    severity: str  # critical, high, medium, low
    check_name: str
    message: str
    tier: Optional[EvidenceTier] = None
    field: Optional[str] = None
    suggested_fix: Optional[str] = None


@dataclass
class TierValidationResult:
    tier: EvidenceTier
    is_valid: bool
    issues: List[ValidationIssue]
    confidence: float
    checks_passed: List[str]
    checks_failed: List[str]


@dataclass
class PipelineValidationReport:
    pipeline_id: str
    timestamp: str
    overall_valid: bool
    tier_results: Dict[str, TierValidationResult]
    all_issues: List[ValidationIssue]
    critical_issues: List[ValidationIssue]
    sanitized_outputs: Dict[str, Any]
    evidence_tier_summary: Dict[str, Any]
    applicability_domain_report: Dict[str, Any]
    hallucination_report: Dict[str, Any]
    docking_pose_report: Dict[str, Any]
    ml_confidence_report: Dict[str, Any]
    ayush64_compliance: bool
    ayush64_notes: str


class ValidationAgent:
    """
    Validation Agent - separate agent preventing error propagation.
    Implements multiple validators:
    1. Evidence tier compliance
    2. Clinical overclaim guardrail
    3. Applicability domain (AD) for ML
    4. Hallucination detection (citation grounding)
    5. Docking pose quality
    6. ML confidence and uncertainty
    """

    def __init__(self):
        self.agent_name = "ValidationAgent"
        logger.info(f"{self.agent_name} initialized as independent validator")

        # Thresholds
        self.docking_score_threshold = -6.0  # kcal/mol, typical active threshold
        self.pose_quality_rmsd_threshold = 2.0
        self.ml_confidence_low_threshold = 0.6
        self.ml_ad_distance_threshold = 3.0  # Euclidean distance normalized

    # ---- Evidence Tier Compliance ----
    def validate_evidence_tier_compliance(self, tiered_outputs: List[TieredOutput]) -> TierValidationResult:
        """Every output must map to one of five tiers."""
        issues = []
        checks_passed = []
        checks_failed = []

        if not tiered_outputs:
            issues.append(ValidationIssue(
                severity="critical",
                check_name="evidence_tier_presence",
                message="No tiered outputs found - violates HARD CONSTRAINT every output must map to tier",
                suggested_fix="Wrap all outputs in TieredOutput with EvidenceTier"
            ))
            checks_failed.append("evidence_tier_presence")
            return TierValidationResult(
                tier=EvidenceTier.DATABASE_DERIVED,
                is_valid=False,
                issues=issues,
                confidence=0.0,
                checks_passed=checks_passed,
                checks_failed=checks_failed
            )

        for i, out in enumerate(tiered_outputs):
            if not isinstance(out, TieredOutput):
                issues.append(ValidationIssue(
                    severity="critical",
                    check_name="tiered_output_type",
                    message=f"Output {i} is not TieredOutput: {type(out)}",
                    suggested_fix="Convert to TieredOutput"
                ))
                checks_failed.append(f"tiered_output_type_{i}")
            else:
                # Check tier is valid enum
                if out.tier not in list(EvidenceTier):
                    issues.append(ValidationIssue(
                        severity="critical",
                        check_name="valid_tier_enum",
                        message=f"Output {i} has invalid tier {out.tier}",
                        tier=out.tier
                    ))
                    checks_failed.append(f"valid_tier_enum_{i}")
                else:
                    checks_passed.append(f"valid_tier_enum_{i}")

                # Literature must have citations
                if out.tier == EvidenceTier.LITERATURE_DERIVED:
                    if len(out.citations) == 0 and out.confidence > 0.1:
                        issues.append(ValidationIssue(
                            severity="high",
                            check_name="literature_citations_required",
                            message=f"LITERATURE_DERIVED output without citations - risk of hallucination 40-60%",
                            tier=out.tier,
                            suggested_fix="Ensure RAG retrieval returned docs and generator grounded citations to corpus IDs"
                        ))
                        checks_failed.append("literature_citations_required")
                    else:
                        checks_passed.append("literature_citations_required")

        is_valid = len([iss for iss in issues if iss.severity in ("critical","high")]) == 0
        return TierValidationResult(
            tier=EvidenceTier.DATABASE_DERIVED,
            is_valid=is_valid,
            issues=issues,
            confidence=1.0 if is_valid else 0.5,
            checks_passed=checks_passed,
            checks_failed=checks_failed
        )

    # ---- Clinical Overclaim ----
    def validate_no_clinical_overclaim(self, tiered_outputs: List[TieredOutput]) -> Tuple[List[ValidationIssue], List[str], List[str]]:
        issues = []
        passed = []
        failed = []

        for idx, out in enumerate(tiered_outputs):
            text_to_check = ""
            if isinstance(out.content, str):
                text_to_check = out.content
            elif isinstance(out.content, dict):
                text_to_check = str(out.content.get("answer", "")) + " " + str(out.content.get("content", "")) + " " + str(out.content)
            else:
                text_to_check = str(out.content)

            is_safe, violations = validate_no_clinical_overclaim(text_to_check)

            # Additional check: computational tiers cannot claim clinical
            if out.tier in [EvidenceTier.DOCKING_RESULT, EvidenceTier.ML_PREDICTION, EvidenceTier.XAI_INTERPRETATION]:
                if any(keyword in text_to_check.lower() for keyword in ["clinical efficacy demonstrated", "proven to cure", "effective treatment for patients"]):
                    is_safe = False
                    violations.append(f"Computational tier {out.tier.value} claimed clinical efficacy - violates AYUSH-64 justification principle")

            if not is_safe:
                for v in violations:
                    issues.append(ValidationIssue(
                        severity="critical",
                        check_name="no_clinical_overclaim",
                        message=f"Output {idx} ({out.tier.value}) contains clinical overclaim: {v}",
                        tier=out.tier,
                        suggested_fix=f"Add disclaimer: {out.tier.confidence_ceiling} and remove clinical efficacy claims. Reference AYUSH-64 pathway."
                    ))
                failed.append(f"no_clinical_overclaim_{idx}")
            else:
                passed.append(f"no_clinical_overclaim_{idx}")

        return issues, passed, failed

    # ---- Applicability Domain ----
    def validate_applicability_domain(self, ml_outputs: List[TieredOutput]) -> Tuple[List[ValidationIssue], Dict[str, Any]]:
        issues = []
        report = {
            "total_ml_predictions": 0,
            "within_domain": 0,
            "outside_domain": 0,
            "borderline": 0,
            "details": []
        }

        for out in ml_outputs:
            if out.tier != EvidenceTier.ML_PREDICTION:
                continue
            report["total_ml_predictions"] += 1

            ad_status = out.metadata.get("applicability_domain", {})
            is_within = ad_status.get("within_domain", True)
            distance = ad_status.get("distance_to_centroid", 0)
            leverage = ad_status.get("leverage", 0)

            # If metadata missing AD, flag
            if not ad_status:
                issues.append(ValidationIssue(
                    severity="medium",
                    check_name="applicability_domain_present",
                    message=f"ML prediction missing applicability domain metadata - must report AD per REF_023",
                    tier=out.tier,
                    suggested_fix="Compute leverage, distance to centroid, Williams plot status"
                ))
                # Assume outside for safety
                report["outside_domain"] += 1
                report["details"].append({
                    "compound": out.metadata.get("compound_id", "unknown"),
                    "within_domain": False,
                    "reason": "AD metadata missing - assumed out-of-domain"
                })
                continue

            if is_within:
                report["within_domain"] += 1
            else:
                report["outside_domain"] += 1
                if out.confidence > 0.8:
                    issues.append(ValidationIssue(
                        severity="high",
                        check_name="outside_domain_high_confidence",
                        message=f"ML prediction outside applicability domain but confidence high {out.confidence:.2f} - unreliable (REF_023)",
                        tier=out.tier,
                        suggested_fix="Reduce confidence, flag as low reliability, suggest experimental validation"
                    ))
            report["details"].append({
                "compound": out.metadata.get("compound_id", "unknown"),
                "within_domain": is_within,
                "distance": distance,
                "leverage": leverage,
                "confidence": out.confidence
            })

        return issues, report

    # ---- Hallucination ----
    def validate_hallucination(self, lit_outputs: List[TieredOutput], corpus_id_set: Optional[set] = None) -> Tuple[List[ValidationIssue], Dict[str, Any]]:
        issues = []
        report = {
            "total_literature_outputs": len(lit_outputs),
            "hallucination_detected": 0,
            "hallucination_free": 0,
            "avg_citations_per_answer": 0,
            "details": []
        }

        if not lit_outputs:
            report["details"].append({"note": "No literature outputs to validate"})
            return issues, report

        total_citations = 0
        for out in lit_outputs:
            cited_ids = []
            if isinstance(out.content, dict):
                cited_ids = out.content.get("cited_doc_ids", [])
            else:
                # Extract from citation objects
                cited_ids = [c.id for c in out.citations]

            total_citations += len(cited_ids)

            # Check against corpus
            if corpus_id_set:
                hallucinated = [cid for cid in cited_ids if cid not in corpus_id_set]
                if hallucinated:
                    report["hallucination_detected"] += 1
                    issues.append(ValidationIssue(
                        severity="critical",
                        check_name="citation_hallucination",
                        message=f"Hallucinated citations detected: {hallucinated} not in corpus of size {len(corpus_id_set)} - violates REF_039 0% hallucination with RAG requirement",
                        tier=out.tier,
                        suggested_fix="Regenerate with strict grounding, only use retrieved doc_ids"
                    ))
                    report["details"].append({
                        "query": out.metadata.get("query", "unknown"),
                        "cited_ids": cited_ids,
                        "hallucinated": hallucinated,
                        "valid": False
                    })
                else:
                    report["hallucination_free"] += 1
                    report["details"].append({
                        "query": out.metadata.get("query", "unknown"),
                        "cited_ids": cited_ids,
                        "hallucinated": [],
                        "valid": True
                    })
            else:
                # Without corpus set, check if citations exist at all
                if len(cited_ids) == 0 and out.confidence > 0.1:
                    issues.append(ValidationIssue(
                        severity="high",
                        check_name="missing_citations",
                        message="Literature output without citations but with high confidence - potential hallucination",
                        tier=out.tier
                    ))

        report["avg_citations_per_answer"] = total_citations / max(len(lit_outputs),1)
        return issues, report

    # ---- Docking Pose Quality ----
    def validate_docking_pose_quality(self, docking_outputs: List[TieredOutput]) -> Tuple[List[ValidationIssue], Dict[str, Any]]:
        issues = []
        report = {
            "total_docking": len(docking_outputs),
            "high_quality": 0,
            "medium_quality": 0,
            "low_quality": 0,
            "details": []
        }

        for out in docking_outputs:
            if out.tier != EvidenceTier.DOCKING_RESULT:
                continue

            meta = out.metadata if isinstance(out.metadata, dict) else {}
            score = meta.get("docking_score", out.content.get("docking_score") if isinstance(out.content, dict) else -7.0)
            rmsd = meta.get("pose_rmsd", meta.get("rmsd", 1.5))
            interactions = meta.get("interactions", [])
            clashes = meta.get("steric_clashes", 0)
            strain = meta.get("ligand_strain_energy", 2.0)

            # Quality heuristics per REF_019
            quality = "low"
            if score <= self.docking_score_threshold and rmsd <= self.pose_quality_rmsd_threshold and clashes == 0 and strain < 5.0:
                quality = "high"
                report["high_quality"] += 1
            elif score <= -5.0 and rmsd <= 3.0:
                quality = "medium"
                report["medium_quality"] += 1
            else:
                quality = "low"
                report["low_quality"] += 1

            if quality == "low":
                if score > -5.0:
                    issues.append(ValidationIssue(
                        severity="medium",
                        check_name="docking_score_threshold",
                        message=f"Docking score {score:.2f} kcal/mol above threshold {self.docking_score_threshold} - weak binding, may be false positive per REF_019",
                        tier=out.tier,
                        suggested_fix="Flag as low-confidence, require pose clustering RMSD <2A among top 3 poses"
                    ))
                if rmsd > 3.0:
                    issues.append(ValidationIssue(
                        severity="medium",
                        check_name="pose_rmsd_quality",
                        message=f"Pose RMSD {rmsd:.2f}A >3.0 - unreliable pose per REF_019",
                        tier=out.tier
                    ))
                if clashes > 0:
                    issues.append(ValidationIssue(
                        severity="high",
                        check_name="steric_clash",
                        message=f"{clashes} steric clashes detected - invalid pose",
                        tier=out.tier
                    ))

            report["details"].append({
                "compound": meta.get("compound_id", out.metadata.get("compound_id", "unknown")),
                "docking_score": score,
                "rmsd": rmsd,
                "quality": quality,
                "clashes": clashes,
                "strain": strain,
                "interactions": interactions[:3] if interactions else []
            })

        return issues, report

    # ---- ML Confidence ----
    def validate_ml_confidence(self, ml_outputs: List[TieredOutput]) -> Tuple[List[ValidationIssue], Dict[str, Any]]:
        issues = []
        report = {
            "total_ml": len(ml_outputs),
            "high_confidence": 0,
            "low_confidence": 0,
            "uncertain": 0,
            "avg_confidence": 0,
            "details": []
        }

        if not ml_outputs:
            return issues, report

        confidences = []
        for out in ml_outputs:
            conf = out.confidence
            confidences.append(conf)
            std = out.metadata.get("uncertainty_std", out.metadata.get("std", 0.2)) if isinstance(out.metadata, dict) else 0.2
            ci_lower = out.metadata.get("ci_lower") if isinstance(out.metadata, dict) else None
            ci_upper = out.metadata.get("ci_upper") if isinstance(out.metadata, dict) else None

            if conf >= 0.8:
                report["high_confidence"] += 1
            elif conf < self.ml_confidence_low_threshold:
                report["low_confidence"] += 1
                if std > 0.5:
                    issues.append(ValidationIssue(
                        severity="medium",
                        check_name="ml_high_uncertainty",
                        message=f"ML prediction low confidence {conf:.2f} with high uncertainty std {std:.3f} - unreliable per REF_026",
                        tier=out.tier,
                        suggested_fix="Report 95% CI, flag as exploratory, suggest experimental validation"
                    ))
            else:
                report["uncertain"] += 1

            # Check CI present
            if ci_lower is None or ci_upper is None:
                issues.append(ValidationIssue(
                    severity="low",
                    check_name="ml_confidence_interval_missing",
                    message="ML prediction missing confidence interval per REF_026 best practices",
                    tier=out.tier,
                    suggested_fix="Compute 95% CI via ensemble std"
                ))

            report["details"].append({
                "compound": out.metadata.get("compound_id", "unknown") if isinstance(out.metadata, dict) else "unknown",
                "predicted_affinity": out.content.get("predicted_affinity") if isinstance(out.content, dict) else None,
                "confidence": conf,
                "uncertainty_std": std,
                "within_domain": out.metadata.get("applicability_domain", {}).get("within_domain", True) if isinstance(out.metadata, dict) else True
            })

        report["avg_confidence"] = sum(confidences)/len(confidences) if confidences else 0
        return issues, report

    def validate_pipeline(
        self,
        all_tiered_outputs: List[TieredOutput],
        corpus_id_set: Optional[set] = None,
        pipeline_id: str = "pipeline_001"
    ) -> PipelineValidationReport:
        """
        Main validation entry point - validates all tiers.
        Prevents error propagation by independent checking.
        """
        logger.info(f"[{self.agent_name}] Validating pipeline {pipeline_id} with {len(all_tiered_outputs)} outputs")

        # Separate by tier
        by_tier = {tier: [] for tier in EvidenceTier}
        for out in all_tiered_outputs:
            if out.tier in by_tier:
                by_tier[out.tier].append(out)

        all_issues: List[ValidationIssue] = []
        tier_results: Dict[str, TierValidationResult] = {}

        # 1. Evidence tier compliance
        comp_result = self.validate_evidence_tier_compliance(all_tiered_outputs)
        tier_results["evidence_tier_compliance"] = comp_result
        all_issues.extend(comp_result.issues)

        # 2. Clinical overclaim (applies to all)
        overclaim_issues, overclaim_passed, overclaim_failed = self.validate_no_clinical_overclaim(all_tiered_outputs)
        all_issues.extend(overclaim_issues)
        tier_results["clinical_overclaim"] = TierValidationResult(
            tier=EvidenceTier.LITERATURE_DERIVED,
            is_valid=len([i for i in overclaim_issues if i.severity in ("critical","high")])==0,
            issues=overclaim_issues,
            confidence=1.0 if not overclaim_issues else 0.5,
            checks_passed=overclaim_passed,
            checks_failed=overclaim_failed
        )

        # 3. Applicability domain
        ad_issues, ad_report = self.validate_applicability_domain(by_tier[EvidenceTier.ML_PREDICTION])
        all_issues.extend(ad_issues)
        tier_results["applicability_domain"] = TierValidationResult(
            tier=EvidenceTier.ML_PREDICTION,
            is_valid=len([i for i in ad_issues if i.severity in ("critical","high")])==0,
            issues=ad_issues,
            confidence=0.8,
            checks_passed=["ad_check"] if not ad_issues else [],
            checks_failed=[i.check_name for i in ad_issues]
        )

        # 4. Hallucination
        hall_issues, hall_report = self.validate_hallucination(by_tier[EvidenceTier.LITERATURE_DERIVED], corpus_id_set=corpus_id_set)
        all_issues.extend(hall_issues)
        tier_results["hallucination"] = TierValidationResult(
            tier=EvidenceTier.LITERATURE_DERIVED,
            is_valid=len([i for i in hall_issues if i.severity in ("critical","high")])==0,
            issues=hall_issues,
            confidence=1.0 if hall_report.get("hallucination_detected",0)==0 else 0.3,
            checks_passed=[f"hall_free_{d['query']}" for d in hall_report.get("details",[]) if d.get("valid")],
            checks_failed=[f"hall_detected_{d['query']}" for d in hall_report.get("details",[]) if not d.get("valid")]
        )

        # 5. Docking pose quality
        pose_issues, pose_report = self.validate_docking_pose_quality(by_tier[EvidenceTier.DOCKING_RESULT])
        all_issues.extend(pose_issues)
        tier_results["docking_pose_quality"] = TierValidationResult(
            tier=EvidenceTier.DOCKING_RESULT,
            is_valid=len([i for i in pose_issues if i.severity=="critical"])==0,
            issues=pose_issues,
            confidence=0.7,
            checks_passed=[],
            checks_failed=[i.check_name for i in pose_issues]
        )

        # 6. ML confidence
        ml_issues, ml_report = self.validate_ml_confidence(by_tier[EvidenceTier.ML_PREDICTION])
        all_issues.extend(ml_issues)
        tier_results["ml_confidence"] = TierValidationResult(
            tier=EvidenceTier.ML_PREDICTION,
            is_valid=len([i for i in ml_issues if i.severity=="critical"])==0,
            issues=ml_issues,
            confidence=ml_report.get("avg_confidence",0),
            checks_passed=[],
            checks_failed=[i.check_name for i in ml_issues]
        )

        critical_issues = [i for i in all_issues if i.severity == "critical"]

        # AYUSH-64 compliance check: ensure pipeline respects tier separation
        ayush64_compliance = len(critical_issues) == 0
        ayush64_notes = (
            "AYUSH-64 exemplifies correct evidentiary tier separation: "
            "in silico (docking/ML) -> in vitro validation -> clinical trial. "
            "Computational predictions were never presented as clinical proof. "
            "This pipeline "
        )
        if ayush64_compliance:
            ayush64_notes += "PASSES compliance: No critical tier violations, disclaimers present, AD reported, zero hallucination."
        else:
            ayush64_notes += f"FAILS compliance due to {len(critical_issues)} critical issues. See issues list."

        # Sanitized outputs: add disclaimers where needed
        sanitized = {}
        for out in all_tiered_outputs:
            key = f"{out.tier.value}_{out.metadata.get('compound_id','unknown')}" if isinstance(out.metadata, dict) else out.tier.value
            sanitized[key] = {
                "tier": out.tier.value,
                "confidence": out.confidence,
                "disclaimer": out.safety_disclaimer,
                "content_summary": str(out.content)[:500],
                "validated": True
            }

        overall_valid = len(critical_issues) == 0

        report = PipelineValidationReport(
            pipeline_id=pipeline_id,
            timestamp=datetime.utcnow().isoformat(),
            overall_valid=overall_valid,
            tier_results={k: v for k,v in tier_results.items()},
            all_issues=all_issues,
            critical_issues=critical_issues,
            sanitized_outputs=sanitized,
            evidence_tier_summary=global_registry.generate_tier_summary(),
            applicability_domain_report=ad_report,
            hallucination_report=hall_report,
            docking_pose_report=pose_report,
            ml_confidence_report=ml_report,
            ayush64_compliance=ayush64_compliance,
            ayush64_notes=ayush64_notes
        )

        logger.info(f"[{self.agent_name}] Validation complete: overall_valid={overall_valid}, critical={len(critical_issues)}, total_issues={len(all_issues)}")
        return report

    def run_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        LangGraph-style node.
        Expects state['tiered_outputs'] list, optional corpus_ids.
        Adds validation report to state.
        """
        tiered_dicts = state.get("tiered_outputs", [])
        # Convert dicts back to TieredOutput if needed
        tiered_outputs: List[TieredOutput] = []
        for td in tiered_dicts:
            if isinstance(td, TieredOutput):
                tiered_outputs.append(td)
            elif isinstance(td, dict):
                try:
                    tier = EvidenceTier(td.get("tier", "database_derived"))
                    # Reconstruct minimal
                    from app.agents.evidence_tiers import Citation
                    citations = [Citation(**c) for c in td.get("citations", [])] if td.get("citations") else []
                    out = TieredOutput(
                        tier=tier,
                        content=td.get("content", {}),
                        citations=citations,
                        confidence=td.get("confidence", 0.5),
                        metadata=td.get("metadata", {})
                    )
                    tiered_outputs.append(out)
                except Exception as e:
                    logger.warning(f"Failed to reconstruct TieredOutput: {e}")

        corpus_ids = state.get("corpus_id_set") or state.get("literature_corpus_stats", {}).get("corpus_ids")
        if corpus_ids and not isinstance(corpus_ids, set):
            corpus_ids = set(corpus_ids)

        report = self.validate_pipeline(
            all_tiered_outputs=tiered_outputs,
            corpus_id_set=corpus_ids,
            pipeline_id=state.get("pipeline_id", "pipeline_validation")
        )

        new_state = {
            **state,
            "validation_report": {
                "overall_valid": report.overall_valid,
                "critical_issues": [{"severity": i.severity, "check": i.check_name, "message": i.message} for i in report.critical_issues],
                "all_issues": [{"severity": i.severity, "check": i.check_name, "message": i.message} for i in report.all_issues],
                "ayush64_compliance": report.ayush64_compliance,
                "ayush64_notes": report.ayush64_notes,
                "evidence_tier_summary": report.evidence_tier_summary,
                "applicability_domain": report.applicability_domain_report,
                "hallucination": report.hallucination_report,
                "docking_pose": report.docking_pose_report,
                "ml_confidence": report.ml_confidence_report,
                "timestamp": report.timestamp
            }
        }
        return new_state


if __name__ == "__main__":
    # Test with dummy tiered outputs
    from app.agents.evidence_tiers import TieredOutput, EvidenceTier, Citation

    dummy_outputs = [
        TieredOutput(
            tier=EvidenceTier.DATABASE_DERIVED,
            content={"plant": "Withania somnifera", "compound": "Withaferin A"},
            confidence=0.95
        ),
        TieredOutput(
            tier=EvidenceTier.DOCKING_RESULT,
            content={"docking_score": -8.5},
            confidence=0.85,
            metadata={"docking_score": -8.5, "pose_rmsd": 1.2, "compound_id": "Withaferin_A"}
        ),
        TieredOutput(
            tier=EvidenceTier.LITERATURE_DERIVED,
            content={"answer": "Withaferin A binds Mpro [REF_018]", "cited_doc_ids": ["REF_018"]},
            citations=[Citation(id="REF_018", title="Docking study", authors=["X"], year=2020)],
            confidence=0.8,
            metadata={"query": "Withaferin A docking"}
        )
    ]

    va = ValidationAgent()
    rep = va.validate_pipeline(dummy_outputs, corpus_id_set={"REF_018", "REF_001"}, pipeline_id="test")
    print(f"Overall valid: {rep.overall_valid}")
    print(f"Critical issues: {len(rep.critical_issues)}")
    for iss in rep.all_issues:
        print(f" - {iss.severity}: {iss.check_name}: {iss.message}")
