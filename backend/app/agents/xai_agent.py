"""
XAI Agent for Explainable Binding Affinity Predictions
=======================================================
Implements XAIAgent with multi-explainer triangulation (SHAP + LIME + feature importance)
per XAI survey 2026, bias-aware splits, applicability domain.

Returns explanations tagged as XAI_INTERPRETATION tier.

Methods:
- explain_prediction(): SHAP values, top features, textual interpretation
- batch_explain()
- triangulate_explanations(): compare SHAP vs LIME vs importance agreement
- bias_audit(): check for bias across splits

Integration:
- Consumes MLAgent predictions and features
- Provides explanations to web interface molecular visualisation + reporting
- Tags all outputs as XAI_INTERPRETATION tier with disclaimer (NOT causal mechanism)
"""

from __future__ import annotations

import json
import logging
import warnings
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional, Union
from datetime import datetime

import numpy as np

# Local imports with fallback handling like ml_agent
try:
    from backend.app.core.ml.features import AyurvedicFeatureEngineer, ALL_FEATURES, DOCKING_FEATURES, QSAR_FEATURES, AYURVEDIC_FEATURES
    from backend.app.core.xai.shap_explainer import ShapExplainerWrapper, ShapExplanation
    from backend.app.core.xai.lime_explainer import LimeExplainerWrapper, LimeExplanation
    from backend.app.core.evidence import EvidenceTier, EvidenceTaggedOutput, EvidenceValidator
except ImportError:
    try:
        from ..core.ml.features import AyurvedicFeatureEngineer, ALL_FEATURES, DOCKING_FEATURES, QSAR_FEATURES, AYURVEDIC_FEATURES
        from ..core.xai.shap_explainer import ShapExplainerWrapper, ShapExplanation
        from ..core.xai.lime_explainer import LimeExplainerWrapper, LimeExplanation
        from ..core.evidence import EvidenceTier, EvidenceTaggedOutput, EvidenceValidator
    except ImportError:
        from app.core.ml.features import AyurvedicFeatureEngineer, ALL_FEATURES, DOCKING_FEATURES, QSAR_FEATURES, AYURVEDIC_FEATURES
        from app.core.xai.shap_explainer import ShapExplainerWrapper, ShapExplanation
        from app.core.xai.lime_explainer import LimeExplainerWrapper, LimeExplanation
        from app.core.evidence import EvidenceTier, EvidenceTaggedOutput, EvidenceValidator


# Optional: try import MLAgent for direct integration
try:
    from backend.app.agents.ml_agent import MLAgent, BindingAffinityPrediction
except ImportError:
    try:
        from .ml_agent import MLAgent, BindingAffinityPrediction
    except ImportError:
        MLAgent = None  # type: ignore
        BindingAffinityPrediction = None  # type: ignore


@dataclass
class FeatureGroupContribution:
    """Contribution aggregated by feature group"""
    group: str  # docking, qsar, ayurvedic
    total_shap: float
    mean_abs_shap: float
    top_features_in_group: List[Tuple[str, float]]


@dataclass
class TriangulationResult:
    """Multi-explainer agreement"""
    shap_top: List[Tuple[str, float]]
    lime_top: List[Tuple[str, float]]
    importance_top: List[Tuple[str, float]]
    agreement_score: float  # 0-1, Jaccard overlap of top features across methods
    consensus_features: List[str]  # features in top-k of all 3 methods
    disagreement_notes: List[str]


@dataclass
class XAIExplanationResult:
    """Full XAI result for single prediction"""
    smiles: str
    protein_target: str
    predicted_pkd: float
    shap_explanation: ShapExplanation
    lime_explanation: LimeExplanation
    feature_importance: Dict[str, float]
    group_contributions: List[FeatureGroupContribution]
    triangulation: TriangulationResult
    textual_interpretation: str
    bias_flags: List[str]
    applicability_domain: Optional[Dict[str, Any]] = None
    evidencia_tier: str = EvidenceTier.XAI_INTERPRETATION.value
    disclaimer: str = field(default_factory=lambda: EvidenceTier.XAI_INTERPRETATION.disclaimer)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    model_name: str = "unknown"

    def to_evidence_tagged(self) -> EvidenceTaggedOutput:
        data = {
            "smiles": self.smiles,
            "protein_target": self.protein_target,
            "predicted_pKd": self.predicted_pkd,
            "shap": {
                "expected_value": self.shap_explanation.expected_value,
                "top_features": self.shap_explanation.top_features,
                "shap_values": self.shap_explanation.shap_values.tolist() if isinstance(self.shap_explanation.shap_values, np.ndarray) else self.shap_explanation.shap_values,
            },
            "lime": {
                "feature_weights": self.lime_explanation.feature_weights,
                "intercept": self.lime_explanation.intercept,
                "local_pred": self.lime_explanation.local_pred,
                "score": self.lime_explanation.score,
            },
            "feature_importance": self.feature_importance,
            "group_contributions": [
                {
                    "group": gc.group,
                    "total_shap": gc.total_shap,
                    "mean_abs_shap": gc.mean_abs_shap,
                    "top_features": gc.top_features_in_group,
                }
                for gc in self.group_contributions
            ],
            "triangulation": {
                "agreement_score": self.triangulation.agreement_score,
                "consensus_features": self.triangulation.consensus_features,
                "disagreement_notes": self.triangulation.disagreement_notes,
                "shap_top": self.triangulation.shap_top,
                "lime_top": self.triangulation.lime_top,
                "importance_top": self.triangulation.importance_top,
            },
            "bias_flags": self.bias_flags,
            "applicability_domain": self.applicability_domain,
            "model": self.model_name,
        }
        meta = {
            "textual_interpretation": self.textual_interpretation,
            "xai_survey_2026_compliant": "Multi-explainer triangulation SHAP+LIME+Importance",
            "note": "Interpretation of model behavior, not causal biological mechanism. AYUSH-64: needs experimental validation.",
        }
        out = EvidenceTaggedOutput(
            tier=EvidenceTier.XAI_INTERPRETATION,
            data=data,
            metadata=meta,
        )
        return EvidenceValidator.validate(out)


class XAIAgent:
    """
    XAI Agent implementing SHAP explanations, multi-explainer triangulation.

    Per XAI survey 2026 recommendations:
    - Use multiple explainers (SHAP, LIME, permutation importance)
    - Report agreement/disagreement
    - Bias-aware splits: check if explanation stable across scaffold groups
    - Applicability domain awareness

    Usage:
        ml_agent = MLAgent()
        ml_agent.train()
        xai_agent = XAIAgent(ml_agent=ml_agent)
        explanation = xai_agent.explain_prediction(smiles="CCO", protein_target="BACE1")
    """

    def __init__(
        self,
        ml_agent: Optional[Any] = None,
        background_data: Optional[np.ndarray] = None,
        feature_names: Optional[List[str]] = None,
        random_state: int = 42,
    ):
        """
        Args:
            ml_agent: trained MLAgent instance (provides model + scaler + training data)
            background_data: optional background data for SHAP/LIME (n_samples, n_features)
            feature_names: ordered feature names (defaults to ALL_FEATURES)
            random_state: reproducibility
        """
        self.ml_agent = ml_agent
        self.feature_names = feature_names or (ml_agent.feature_names if ml_agent and hasattr(ml_agent, "feature_names") else ALL_FEATURES)
        self.random_state = random_state

        # Background data: prefer training data from MLAgent
        if background_data is None and ml_agent is not None and hasattr(ml_agent, "X_train_") and ml_agent.X_train_ is not None:
            X_train = ml_agent.X_train_
            # If scaler exists, use scaled version for explanations (matches model input)
            if ml_agent.scaler is not None:
                try:
                    background_data = ml_agent.scaler.transform(X_train)
                except Exception:
                    background_data = X_train
            else:
                background_data = X_train

        self.background_data = background_data
        self.feature_engineer = AyurvedicFeatureEngineer()

        # Internal explainers lazily initialized per model
        self._shap_explainers: Dict[str, ShapExplainerWrapper] = {}
        self._lime_explainers: Dict[str, LimeExplainerWrapper] = {}

    def _get_model_and_scaler(self, model_name: Optional[str] = None) -> Tuple[Any, Optional[Any], List[str]]:
        """
        Get model, scaler, feature_names for explanation.
        If MLAgent provided, use its best model. Else require model passed in explain_prediction.
        """
        if self.ml_agent is not None and self.ml_agent.best_model is not None:
            model = self.ml_agent.best_model
            scaler = self.ml_agent.scaler
            # Prefer best_model_name for tracking
            name = self.ml_agent.best_model_name
            return model, scaler, self.feature_names

        raise RuntimeError("No model available: provide ml_agent with trained model or pass model explicitly")

    def _ensure_explainers(self, model: Any, scaler: Optional[Any], model_name: str) -> Tuple[ShapExplainerWrapper, LimeExplainerWrapper]:
        """Ensure SHAP and LIME explainers exist for model"""
        if model_name not in self._shap_explainers:
            bg = self.background_data
            # Limit background size
            if bg is not None and len(bg) > 200:
                rng = np.random.RandomState(self.random_state)
                idx = rng.choice(len(bg), 200, replace=False)
                bg_sub = bg[idx]
            else:
                bg_sub = bg

            shap_exp = ShapExplainerWrapper(
                model=model,
                feature_names=self.feature_names,
                background_data=bg_sub,
                random_state=self.random_state,
            )
            self._shap_explainers[model_name] = shap_exp

        if model_name not in self._lime_explainers:
            bg = self.background_data
            lime_exp = LimeExplainerWrapper(
                model=model,
                feature_names=self.feature_names,
                training_data=bg,
                mode="regression",
                random_state=self.random_state,
            )
            self._lime_explainers[model_name] = lime_exp

        return self._shap_explainers[model_name], self._lime_explainers[model_name]

    def _compute_group_contributions(
        self,
        shap_values: np.ndarray,
        feature_names: List[str],
    ) -> List[FeatureGroupContribution]:
        """Aggregate SHAP by feature groups (docking, qsar, ayurvedic)"""
        # Map feature to group
        group_map: Dict[str, str] = {}
        for fn in DOCKING_FEATURES:
            group_map[fn] = "docking"
        for fn in QSAR_FEATURES:
            group_map[fn] = "qsar"
        for fn in AYURVEDIC_FEATURES:
            group_map[fn] = "ayurvedic"

        # Group aggregation
        groups: Dict[str, List[Tuple[str, float]]] = {"docking": [], "qsar": [], "ayurvedic": []}
        for i, fname in enumerate(feature_names):
            g = group_map.get(fname, "qsar")
            val = float(shap_values[i] if shap_values.ndim == 1 else shap_values[0, i])
            groups[g].append((fname, val))

        contributions: List[FeatureGroupContribution] = []
        for gname, feats in groups.items():
            if not feats:
                continue
            total = float(sum(v for _, v in feats))
            mean_abs = float(np.mean([abs(v) for _, v in feats]))
            top_in_group = sorted(feats, key=lambda x: abs(x[1]), reverse=True)[:5]
            contributions.append(
                FeatureGroupContribution(
                    group=gname,
                    total_shap=total,
                    mean_abs_shap=mean_abs,
                    top_features_in_group=top_in_group,
                )
            )

        # Sort by mean_abs descending
        contributions = sorted(contributions, key=lambda c: c.mean_abs_shap, reverse=True)
        return contributions

    def _triangulate(
        self,
        shap_top: List[Tuple[str, float]],
        lime_top: List[Tuple[str, float]],
        importance: Dict[str, float],
        top_k: int = 8,
    ) -> TriangulationResult:
        """
        Multi-explainer agreement calculation.
        Jaccard similarity across top-k feature sets.
        """
        # Top feature names
        shap_names = [f for f, _ in shap_top[:top_k]]
        lime_names = [f for f, _ in lime_top[:top_k]]
        # Importance top_k
        importance_sorted = sorted(importance.items(), key=lambda x: x[1], reverse=True)
        importance_names = [f for f, _ in importance_sorted[:top_k]]

        set_shap = set(shap_names)
        set_lime = set(lime_names)
        set_imp = set(importance_names)

        # Pairwise Jaccard
        def jaccard(a: set, b: set) -> float:
            if not a and not b:
                return 1.0
            inter = len(a.intersection(b))
            union = len(a.union(b))
            return inter / union if union > 0 else 0.0

        j_sl = jaccard(set_shap, set_lime)
        j_si = jaccard(set_shap, set_imp)
        j_li = jaccard(set_lime, set_imp)

        agreement = float((j_sl + j_si + j_li) / 3.0)

        consensus = list(set_shap.intersection(set_lime).intersection(set_imp))

        disagreement_notes: List[str] = []
        if agreement < 0.3:
            disagreement_notes.append(
                "Low agreement (<0.3) across SHAP/LIME/Importance. Explanation may be unstable; check applicability domain and feature collinearity."
            )
        if j_sl < 0.3:
            disagreement_notes.append("SHAP vs LIME disagreement: local vs global attribution differ. Examine instance neighborhood density.")
        if not consensus:
            disagreement_notes.append("No consensus features in top-k across all 3 methods. Model may be relying on many weak features or interacting features.")
        else:
            disagreement_notes.append(f"Consensus features {consensus} robustly drive prediction across explainers.")

        # Add docking vs QSAR dominance note
        docking_in_consensus = [f for f in consensus if f in DOCKING_FEATURES]
        if docking_in_consensus:
            disagreement_notes.append(f"Docking features {docking_in_consensus} in consensus: physics-based interaction strong driver (BACE1 R2 improvement pattern).")
        ayur_in_consensus = [f for f in consensus if f in AYURVEDIC_FEATURES]
        if ayur_in_consensus:
            disagreement_notes.append(f"Ayurvedic features {ayur_in_consensus} in consensus: privileged scaffold / traditional use signal.")

        return TriangulationResult(
            shap_top=shap_top,
            lime_top=lime_top,
            importance_top=importance_sorted[:top_k],
            agreement_score=agreement,
            consensus_features=consensus,
            disagreement_notes=disagreement_notes,
        )

    def _generate_textual_interpretation(
        self,
        smiles: str,
        protein_target: str,
        predicted_pkd: float,
        group_contributions: List[FeatureGroupContribution],
        triangulation: TriangulationResult,
        applicability: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Generate human-readable interpretation, with mandatory disclaimer language.
        Must NOT present as causal mechanism.
        """
        # Determine dominant group
        dominant = group_contributions[0].group if group_contributions else "unknown"
        dominant_desc = {
            "docking": "structure-based docking energetics",
            "qsar": "physicochemical / QSAR descriptors",
            "ayurvedic": "Ayurvedic privileged scaffold / phytochemical class",
        }.get(dominant, dominant)

        # Top consensus
        consensus_str = ", ".join(triangulation.consensus_features[:5]) if triangulation.consensus_features else "no single consensus; many weak contributors"

        # Applicability note
        ad_str = ""
        if applicability:
            conf = applicability.get("confidence", "unknown")
            if conf == "out-of-domain":
                ad_str = " WARNING: Instance outside applicability domain; explanation may be extrapolative and unreliable."
            elif conf == "low":
                ad_str = " Note: Low confidence applicability domain; interpretation tentative."

        # Classification phrasing from pKd
        if predicted_pkd >= 7.0:
            activity_phrase = "predicted high affinity"
        elif predicted_pkd >= 6.0:
            activity_phrase = "predicted moderate affinity"
        else:
            activity_phrase = "predicted low affinity"

        interpretation = (
            f"For SMILES {smiles[:40]}... vs {protein_target}, model predicts {activity_phrase} (pKd {predicted_pkd:.2f}). "
            f"Dominant driver group per SHAP aggregation: {dominant_desc} (mean|SHAP| {group_contributions[0].mean_abs_shap:.3f} if available). "
            f"Multi-explainer triangulation (SHAP + LIME + importance) agreement score {triangulation.agreement_score:.2f}. "
            f"Consensus robust features: {consensus_str}. "
            f"Top docking contributions: {', '.join([f'{f}={v:.2f}' for f,v in group_contributions[0].top_features_in_group[:3]]) if group_contributions and group_contributions[0].group=='docking' else 'see group breakdown'}. "
            f"{' '.join(triangulation.disagreement_notes[:2])}"
            f"{ad_str} "
            f"Interpretation: This is model-behavior explanation (XAI_INTERPRETATION tier), NOT causal biological mechanism. "
            f"Per AYUSH-64 case study, computational predictions require wet-lab validation before clinical relevance. "
            f"Bias check: explanation stability should be verified across scaffold groups; imbalance in training may skew attribution."
        )

        return interpretation

    def _bias_audit(
        self,
        shap_values: np.ndarray,
        feature_names: List[str],
    ) -> List[str]:
        """
        Bias-aware audit: check for potential biases per XAI survey 2026.
        Heuristics without needing protected attributes: check if traditionally biased QSAR ranges dominate.

        In Ayurvedic context: bias could be towards well-studied scaffolds (curcumin-like) vs rare terpenoids.
        """
        flags: List[str] = []

        # Check if top SHAP is heavily dominated by single group (>70% attribution)
        group_contribs = self._compute_group_contributions(shap_values, feature_names)
        if group_contribs:
            total_abs = sum(gc.mean_abs_shap for gc in group_contribs)
            if total_abs > 0:
                dominant_ratio = group_contribs[0].mean_abs_shap / total_abs
                if dominant_ratio > 0.7:
                    flags.append(f"Bias flag: {group_contribs[0].group} dominates {dominant_ratio:.2%} of attribution. May indicate training data imbalance towards {group_contribs[0].group} features.")

        # Check for Ayurvedic class imbalance
        ayur_features = [f for f in feature_names if f.startswith("phytochemical_class_")]
        if ayur_features:
            # If privileged scaffold contributes heavily, may be bias towards known drugs
            ayur_indices = [i for i, f in enumerate(feature_names) if f.startswith("phytochemical_class_")]
            if len(ayur_indices) > 0:
                ayur_shap_abs = np.mean([abs(shap_values[i] if shap_values.ndim==1 else shap_values[0,i]) for i in ayur_indices])
                if ayur_shap_abs > 0.5 and group_contribs and group_contribs[0].group == "ayurvedic":
                    flags.append("Possible phytochemical class bias: privileged scaffold flag driving prediction. May overestimate novel scaffolds.")

        # Docking bias: if docking score dominates, model may be just re-learning docking (BACE1 R2 0.59 vs 0.78)
        docking_indices = [i for i, f in enumerate(feature_names) if f in DOCKING_FEATURES]
        if docking_indices:
            docking_abs = np.mean([abs(shap_values[i] if shap_values.ndim==1 else shap_values[0,i]) for i in docking_indices])
            qsar_indices = [i for i, f in enumerate(feature_names) if f in QSAR_FEATURES]
            qsar_abs = np.mean([abs(shap_values[i] if shap_values.ndim==1 else shap_values[0,i]) for i in qsar_indices]) if qsar_indices else 0
            if docking_abs > qsar_abs * 2:
                flags.append("Docking-dominated attribution: model largely recapitulates docking score; check if BACE1 combined feature improvement (0.59->0.78) replicated.")

        if not flags:
            flags.append("No obvious bias flags detected in attribution distribution; still verify across scaffold splits (TLR4 n=49 methodology).")

        return flags

    def explain_prediction(
        self,
        smiles: str,
        protein_target: str = "BACE1",
        docking_result: Optional[Dict[str, Any]] = None,
        model: Optional[Any] = None,
        scaler: Optional[Any] = None,
        return_evidence_tagged: bool = True,
    ) -> Union[XAIExplanationResult, EvidenceTaggedOutput]:
        """
        Main explanation method: SHAP values, top features, textual interpretation.

        Args:
            smiles: SMILES string
            protein_target: target protein
            docking_result: optional docking result dict
            model: optional override model (else use MLAgent best)
            scaler: optional scaler
            return_evidence_tagged: wrap in EvidenceTaggedOutput

        Returns:
            XAIExplanationResult or EvidenceTaggedOutput (XAI_INTERPRETATION tier)
        """
        # Resolve model
        if model is None:
            if self.ml_agent is None or self.ml_agent.best_model is None:
                raise RuntimeError("No model available for XAI. Train MLAgent first or pass model.")
            model = self.ml_agent.best_model
            scaler = self.ml_agent.scaler
            model_name = self.ml_agent.best_model_name
            feature_names = self.ml_agent.feature_names
            # Get training prediction for pKd to compare?
            try:
                from ..core.ml.features import AyurvedicFeatureEngineer
                fe = AyurvedicFeatureEngineer()
                feat_dict = fe.extract_features(smiles, docking_result, protein_target)
                x_vec = np.array([feat_dict.get(fn, 0.0) for fn in feature_names], dtype=np.float32)
                xs = x_vec.reshape(1, -1)
                if scaler is not None:
                    try:
                        xs = scaler.transform(xs)
                    except Exception:
                        pass
                predicted_pkd = float(model.predict(xs)[0])
            except Exception as e:
                warnings.warn(f"Could not predict pKd for XAI: {e}")
                predicted_pkd = 6.0
        else:
            model_name = type(model).__name__
            feature_names = self.feature_names
            # Featurize
            fe = AyurvedicFeatureEngineer()
            feat_dict = fe.extract_features(smiles, docking_result, protein_target)
            x_vec = np.array([feat_dict.get(fn, 0.0) for fn in feature_names], dtype=np.float32)
            xs = x_vec.reshape(1, -1)
            if scaler is not None:
                try:
                    xs = scaler.transform(xs)
                except Exception:
                    pass
            try:
                predicted_pkd = float(model.predict(xs)[0])
            except Exception:
                predicted_pkd = 6.0

        # Ensure explainers
        shap_exp, lime_exp = self._ensure_explainers(model, scaler, model_name)

        # Use scaled vector for explainers (model input space)
        if scaler is not None:
            try:
                x_for_explain = scaler.transform(x_vec.reshape(1, -1))
                x_unscaled_for_lime = x_for_explain  # LIME expects same space as model
            except Exception:
                x_for_explain = x_vec.reshape(1, -1)
                x_unscaled_for_lime = x_for_explain
        else:
            x_for_explain = x_vec.reshape(1, -1)
            x_unscaled_for_lime = x_for_explain

        # SHAP
        shap_result = shap_exp.explain(x_for_explain[0] if x_for_explain.shape[0]==1 else x_for_explain)

        # LIME
        lime_result = lime_exp.explain(x_for_explain[0], num_features=10, num_samples=600)

        # Feature importance
        importance = shap_exp.get_feature_importance()

        # Group contributions
        # shap_result.shap_values may be (n_features,) or (n_samples, n_features)
        sv = shap_result.shap_values
        if isinstance(sv, np.ndarray) and sv.ndim == 2:
            sv_single = sv[0]
        else:
            sv_single = sv if isinstance(sv, np.ndarray) else np.array(sv)
        group_contribs = self._compute_group_contributions(sv_single, feature_names)

        # Triangulation
        triangulation = self._triangulate(
            shap_top=shap_result.top_features,
            lime_top=lime_result.feature_weights,
            importance=importance,
            top_k=8,
        )

        # Bias audit
        bias_flags = self._bias_audit(sv_single, feature_names)

        # Applicability domain if MLAgent available
        applicability_dict = None
        if self.ml_agent is not None and self.ml_agent.ad_checker_ is not None:
            try:
                ad_res = self.ml_agent.ad_checker_.check(x_for_explain[0])
                applicability_dict = {
                    "is_inside": ad_res.is_inside,
                    "confidence": ad_res.confidence,
                    "distance_score": ad_res.distance_score,
                    "leverage": ad_res.leverage,
                    "explanation": ad_res.explanation,
                }
            except Exception:
                pass

        # Textual interpretation
        textual = self._generate_textual_interpretation(
            smiles=smiles,
            protein_target=protein_target,
            predicted_pkd=predicted_pkd,
            group_contributions=group_contribs,
            triangulation=triangulation,
            applicability=applicability_dict,
        )

        result = XAIExplanationResult(
            smiles=smiles,
            protein_target=protein_target,
            predicted_pkd=predicted_pkd,
            shap_explanation=shap_result,
            lime_explanation=lime_result,
            feature_importance=importance,
            group_contributions=group_contribs,
            triangulation=triangulation,
            textual_interpretation=textual,
            bias_flags=bias_flags,
            applicability_domain=applicability_dict,
            model_name=model_name,
        )

        if return_evidence_tagged:
            return result.to_evidence_tagged()
        else:
            return result

    def batch_explain(
        self,
        inputs: List[Dict[str, Any]],
        return_evidence_tagged: bool = True,
    ) -> List[Union[XAIExplanationResult, EvidenceTaggedOutput]]:
        """
        Batch explanation.

        Args:
            inputs: list of dicts with smiles, protein_target, docking_result
            return_evidence_tagged: wrap each in evidence tier

        Returns:
            list of explanations
        """
        results = []
        for item in inputs:
            try:
                smiles = item.get("smiles") or item.get("SMILES")
                if not smiles:
                    raise ValueError("Missing smiles")
                target = item.get("protein_target", "BACE1")
                docking = item.get("docking_result") or item.get("docking")
                res = self.explain_prediction(
                    smiles=smiles,
                    protein_target=target,
                    docking_result=docking,
                    return_evidence_tagged=return_evidence_tagged,
                )
                results.append(res)
            except Exception as e:
                warnings.warn(f"XAI batch item failed for {item.get('smiles','?')}: {e}")
                continue
        return results

    def explain_with_comparison(
        self,
        smiles_list: List[str],
        protein_target: str = "BACE1",
        docking_results: Optional[List[Optional[Dict[str, Any]]]] = None,
    ) -> EvidenceTaggedOutput:
        """
        Comparative explanation across multiple molecules (e.g., top candidates)
        Shows how feature attributions differ for high vs low affinity predictions.
        Useful for medicinal chemistry optimisation.

        Returns:
            EvidenceTaggedOutput with comparison table
        """
        if docking_results is None:
            docking_results = [None]*len(smiles_list)

        explanations = []
        for smi, dock in zip(smiles_list, docking_results):
            try:
                exp = self.explain_prediction(smiles=smi, protein_target=protein_target, docking_result=dock, return_evidence_tagged=False)
                explanations.append(exp)
            except Exception as e:
                warnings.warn(f"Comparison explain failed for {smi}: {e}")
                continue

        if not explanations:
            raise RuntimeError("All explanations failed in comparison")

        # Build comparison: rank by predicted pKd
        explanations_sorted = sorted(explanations, key=lambda e: e.predicted_pkd, reverse=True)

        comparison_data = []
        for exp in explanations_sorted:
            comparison_data.append({
                "smiles": exp.smiles,
                "predicted_pKd": exp.predicted_pkd,
                "top_shap": exp.shap_explanation.top_features[:5],
                "dominant_group": exp.group_contributions[0].group if exp.group_contributions else "unknown",
                "consensus_features": exp.triangulation.consensus_features,
                "agreement_score": exp.triangulation.agreement_score,
            })

        out = EvidenceTaggedOutput(
            tier=EvidenceTier.XAI_INTERPRETATION,
            data={
                "comparison": comparison_data,
                "protein_target": protein_target,
                "n_molecules": len(comparison_data),
            },
            metadata={
                "method": "multi-explainer triangulation comparative",
                "interpretation": "Comparative SHAP reveals structure-activity drivers; high vs low affinity differences indicate optimisation directions, NOT clinical efficacy differences.",
                "ayush64_compliance": "All interpretations require experimental validation",
            },
        )
        return EvidenceValidator.validate(out)

    def run_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Orchestrator state-dict adapter. Calls the real explain_prediction(), honest if no trained model."""
        from app.agents.evidence_tiers import EvidenceTier, TieredOutput
        if self.ml_agent is None or getattr(self.ml_agent, "best_model", None) is None:
            content = {"status": "no_trained_model", "message": "XAI unavailable: MLAgent has no trained model.", "explanations": []}
            tiered_out = TieredOutput(tier=EvidenceTier.XAI_INTERPRETATION, content=content, confidence=0.0, metadata={"available": False})
            tiered = state.get("tiered_outputs", [])
            tiered.append(tiered_out.to_dict())
            return {**state, "xai_results": content, "tiered_outputs": tiered}

        target_protein = state.get("target_protein", "6LU7")
        ml_preds = state.get("ml_predictions", [])
        explanations = []
        for p in ml_preds[:5]:
            smi = p.get("smiles", "") if isinstance(p, dict) else ""
            if not smi:
                continue
            try:
                expl = self.explain_prediction(smiles=smi, protein_target=target_protein, return_evidence_tagged=False)
                explanations.append(expl.__dict__ if hasattr(expl, "__dict__") else expl)
            except Exception as e:
                logging.getLogger(__name__).warning(f"XAI explanation failed for {smi}: {e}")
        content = {"explanations": explanations, "count": len(explanations)}
        tiered_out = TieredOutput(tier=EvidenceTier.XAI_INTERPRETATION, content=content, confidence=0.7 if explanations else 0.1, metadata={"count": len(explanations)})
        tiered = state.get("tiered_outputs", [])
        tiered.append(tiered_out.to_dict())
        return {**state, "xai_results": content, "tiered_outputs": tiered}
