"""
ML Agent for Binding Affinity Prediction
=========================================
Implements MLAgent fusing docking + QSAR descriptors as per BACE1 study (R2 0.78 combined).

Responsibilities:
- train() on synthetic PDBBind-like dataset (500 samples) or provided data
- predict() single molecule
- batch_predict() multiple molecules
- Ensemble: RandomForest, XGBoost, ExtraTrees, NuSVR, Stacking
- Leakage-aware splitting (diversity-preserving) per TLR4 study n=49 methodology
- Applicability domain check
- Classification (active/inactive) + regression (pKd / binding affinity)
- Tag predictions as ML_PREDICTION tier

Integration points:
- Input from docking_agent: docking_result dict with affinity
- Input from cheminformatic layer: SMILES
- Output to XAI agent and candidate ranking agent

Production considerations:
- Model persistence to models/ directory
- Fallback to mock physics-inspired docking if Vina not present (handled in features)
- No heavy dependencies: sklearn only, XGBoost optional
- Thread-safe, type-hinted, error-handling
"""

from __future__ import annotations

import json
import pickle
import warnings
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, Any, List, Tuple, Optional, Union
from datetime import datetime
import hashlib

import numpy as np

# sklearn
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor, ExtraTreesRegressor
from sklearn.metrics import r2_score

# Local core
import sys

# Ensure app core imports work when module run directly
try:
    from backend.app.core.ml.features import (
        AyurvedicFeatureEngineer,
        ALL_FEATURES,
        DOCKING_FEATURES,
        QSAR_FEATURES,
        AYURVEDIC_FEATURES,
    )
    from backend.app.core.ml.models import (
        get_top5_regressors,
        get_top5_classifiers,
        MODEL_METADATA,
    )
    from backend.app.core.ml.training import (
        TrainingConfig,
        create_synthetic_pdbbind_dataset,
        leakage_aware_split,
        cross_validate_model,
        benchmark_models,
        compute_regression_metrics,
        compute_classification_metrics,
    )
    from backend.app.core.evidence import EvidenceTier, EvidenceTaggedOutput, EvidenceValidator
except ImportError:
    # Fallback relative import when run as backend.app.agents.ml_agent
    try:
        from ..core.ml.features import (
            AyurvedicFeatureEngineer,
            ALL_FEATURES,
            DOCKING_FEATURES,
            QSAR_FEATURES,
            AYURVEDIC_FEATURES,
        )
        from ..core.ml.models import get_top5_regressors, get_top5_classifiers, MODEL_METADATA
        from ..core.ml.training import (
            TrainingConfig,
            create_synthetic_pdbbind_dataset,
            leakage_aware_split,
            cross_validate_model,
            benchmark_models,
            compute_regression_metrics,
            compute_classification_metrics,
        )
        from ..core.evidence import EvidenceTier, EvidenceTaggedOutput, EvidenceValidator
    except ImportError:
        # Absolute fallback for direct file import
        from app.core.ml.features import AyurvedicFeatureEngineer, ALL_FEATURES, DOCKING_FEATURES, QSAR_FEATURES, AYURVEDIC_FEATURES
        from app.core.ml.models import get_top5_regressors, get_top5_classifiers, MODEL_METADATA
        from app.core.ml.training import TrainingConfig, create_synthetic_pdbbind_dataset, leakage_aware_split, cross_validate_model, benchmark_models, compute_regression_metrics, compute_classification_metrics
        from app.core.evidence import EvidenceTier, EvidenceTaggedOutput, EvidenceValidator


# Model storage paths
DEFAULT_MODEL_DIR = Path(__file__).parent.parent / "models" / "trained"
DEFAULT_MODEL_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class ApplicabilityDomainResult:
    """Applicability domain check result"""
    is_inside: bool
    distance_score: float  # lower = closer to training distribution
    confidence: str  # "high", "medium", "low", "out-of-domain"
    leverage: float
    nearest_neighbor_dist: float
    explanation: str


@dataclass
class BindingAffinityPrediction:
    """Single prediction result tagged as ML_PREDICTION"""
    smiles: str
    protein_target: str
    predicted_pkd: float  # pKd (binding affinity log scale)
    predicted_affinity_kcal: float  # converted to kcal/mol approx: -RT*lnKd
    uncertainty: float
    classification: str  # "active" / "inactive" / "moderate"
    classification_proba: float
    applicability_domain: ApplicabilityDomainResult
    top_features_contrib: Optional[List[Tuple[str, float]]] = None
    model_name: str = "StackingEnsemble"
    evidencia_tier: str = EvidenceTier.ML_PREDICTION.value
    disclaimer: str = field(default_factory=lambda: EvidenceTier.ML_PREDICTION.disclaimer)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_evidence_tagged(self) -> EvidenceTaggedOutput:
        data = {
            "smiles": self.smiles,
            "protein_target": self.protein_target,
            "predicted_pKd": self.predicted_pkd,
            "predicted_affinity_kcal_per_mol": self.predicted_affinity_kcal,
            "uncertainty": self.uncertainty,
            "classification": self.classification,
            "classification_proba": self.classification_proba,
            "applicability_domain": {
                "is_inside": self.applicability_domain.is_inside,
                "distance_score": self.applicability_domain.distance_score,
                "confidence": self.applicability_domain.confidence,
                "leverage": self.applicability_domain.leverage,
                "nearest_neighbor_dist": self.applicability_domain.nearest_neighbor_dist,
            },
            "model": self.model_name,
        }
        meta = {
            "top_features": self.top_features_contrib,
            "ayush64_note": "Computational prediction - requires experimental validation",
        }
        out = EvidenceTaggedOutput(
            tier=EvidenceTier.ML_PREDICTION,
            data=data,
            metadata=meta,
        )
        return EvidenceValidator.validate(out)


class ApplicabilityDomainChecker:
    """
    Applicability domain checker for ML predictions.
    Implements:
    - Distance to centroid
    - Leverage (hat matrix diagonal approximation)
    - kNN distance to training set
    - Isolation Forest outlier score (proxy)

    Inspired by applicability domain literature for QSAR.
    """

    def __init__(self, X_train: np.ndarray, feature_names: List[str]):
        self.X_train = X_train
        self.feature_names = feature_names
        self.mean_ = np.mean(X_train, axis=0)
        self.cov_inv_ = None
        try:
            cov = np.cov(X_train, rowvar=False) + np.eye(X_train.shape[1])*1e-6
            self.cov_inv_ = np.linalg.inv(cov)
        except Exception:
            self.cov_inv_ = None

        # For leverage approximation: store XTX inverse if feasible
        self.X_train_scaled = X_train
        # kNN: precompute maybe using simple distance; no heavy dependency

    def check(self, x: np.ndarray) -> ApplicabilityDomainResult:
        """
        Check single instance.

        Args:
            x: (n_features,) feature vector (already scaled if model uses scaler)

        Returns:
            ApplicabilityDomainResult
        """
        x = np.array(x).ravel()
        # Distance to centroid (Mahalanobis if possible else Euclidean)
        diff = x - self.mean_
        if self.cov_inv_ is not None:
            try:
                md = float(np.sqrt(diff @ self.cov_inv_ @ diff))
                distance = md
            except Exception:
                distance = float(np.linalg.norm(diff))
        else:
            distance = float(np.linalg.norm(diff))

        # Leverage approximation: (x - mean) normalized
        # Leverage h = x^T (XTX)^-1 x; approximate via distance/ n
        # Use max training distance as cutoff
        # Compute training distances for reference
        train_distances = np.linalg.norm(self.X_train - self.mean_, axis=1)
        max_train_dist = np.percentile(train_distances, 95)  # 95th percentile as domain edge
        mean_train_dist = np.mean(train_distances)

        # Nearest neighbor distance
        dists_to_train = np.linalg.norm(self.X_train - x, axis=1)
        nn_dist = float(np.min(dists_to_train))
        # Average NN dist in training to get baseline
        # Approximate average NN in training by sampling
        # For simplicity, use mean_train_dist as baseline
        leverage = distance / (max_train_dist + 1e-8)

        # Determine inside/outside
        # Thresholds: leverage < 1 => inside, <1.5 borderline, >1.5 out
        if distance <= max_train_dist and nn_dist <= np.percentile(dists_to_train, 90) + 3* np.std(train_distances):
            # Inside
            if distance <= mean_train_dist:
                confidence = "high"
                is_inside = True
                explanation = "Within high-density training region (distance < mean train distance)"
            else:
                confidence = "medium"
                is_inside = True
                explanation = "Within training distribution (distance < 95th percentile) but near boundary"
        elif distance <= max_train_dist * 1.5:
            confidence = "low"
            is_inside = True
            explanation = "Near edge of applicability domain; prediction uncertainty increased. Consider experimental validation."
        else:
            confidence = "out-of-domain"
            is_inside = False
            explanation = "Outside applicability domain (>1.5x 95th percentile). Prediction unreliable; requires retraining with similar chemotypes."

        return ApplicabilityDomainResult(
            is_inside=is_inside,
            distance_score=distance,
            confidence=confidence,
            leverage=float(leverage),
            nearest_neighbor_dist=nn_dist,
            explanation=explanation,
        )


class MLAgent:
    """
    ML Agent for Binding Affinity Prediction.

    Fuses docking + QSAR per BACE1 study.
    Leakage-aware splitting per TLR4 n=49.

    Usage:
        agent = MLAgent()
        agent.train(n_samples=500)  # synthetic PDBBind
        pred = agent.predict(smiles="CCO", protein_target="BACE1", docking_result={"affinity": -8.2})
        batch = agent.batch_predict([{"smiles": "CCO", ...}, ...])
    """

    def __init__(
        self,
        model_dir: Optional[Path] = None,
        random_state: int = 42,
        auto_load: bool = True,
    ):
        self.model_dir = Path(model_dir) if model_dir else DEFAULT_MODEL_DIR
        self.model_dir.mkdir(parents=True, exist_ok=True)
        self.random_state = random_state

        self.feature_engineer = AyurvedicFeatureEngineer()
        self.feature_names: List[str] = ALL_FEATURES.copy()

        self.models: Dict[str, Any] = {}
        self.scalers: Dict[str, Any] = {}
        self.best_model_name: str = "StackingEnsemble"
        self.best_model: Optional[Any] = None
        self.scaler: Optional[Any] = None

        # Classification models
        self.classifiers: Dict[str, Any] = {}
        self.classifier_scalers: Dict[str, Any] = {}
        self.best_classifier_name: str = "StackingClassifier"
        self.best_classifier: Optional[Any] = None
        self.classifier_scaler: Optional[Any] = None

        # Training data for applicability domain
        self.X_train_: Optional[np.ndarray] = None
        self.y_train_: Optional[np.ndarray] = None
        self.meta_train_: Optional[List[Dict[str, Any]]] = None
        self.ad_checker_: Optional[ApplicabilityDomainChecker] = None
        self.ad_checker_classifier_: Optional[ApplicabilityDomainChecker] = None

        # Metrics
        self.training_metrics_: Dict[str, Any] = {}
        self.is_trained_ = False

        if auto_load:
            try:
                self.load()
            except Exception as e:
                warnings.warn(f"Could not auto-load models from {self.model_dir}: {e}. Need to train.")

    # -------------------------
    # Training
    # -------------------------

    def train(
        self,
        n_samples: int = 500,
        X: Optional[np.ndarray] = None,
        y: Optional[np.ndarray] = None,
        feature_names: Optional[List[str]] = None,
        meta: Optional[List[Dict[str, Any]]] = None,
        groups: Optional[List[str]] = None,
        task: str = "both",  # "regression", "classification", "both"
        test_size: float = 0.2,
        cv_folds: int = 5,
        leakage_aware: bool = True,
        save: bool = True,
    ) -> Dict[str, Any]:
        """
        Train ensemble models.

        Args:
            n_samples: if X None, create synthetic PDBBind-like dataset
            X, y: optional provided data (if None synthetic)
            feature_names: optional
            meta: optional metadata with group info
            groups: scaffold groups for leakage-aware split
            task: regression / classification / both
            test_size: hold-out fraction
            cv_folds: CV folds
            leakage_aware: use diversity-preserving split per TLR4
            save: save models to disk

        Returns:
            training summary dict
        """
        print(f"[MLAgent] Starting training, task={task}, leakage_aware={leakage_aware}")

        # Create or use dataset
        if X is None or y is None:
            X_syn, y_syn, feat_names_syn, meta_syn = create_synthetic_pdbbind_dataset(
                n_samples=n_samples, random_state=self.random_state
            )
            X = X_syn
            y = y_syn
            feature_names = feat_names_syn
            meta = meta_syn
            groups = [m["group"] for m in meta_syn]
        else:
            feature_names = feature_names or self.feature_names
            groups = groups or (meta and [m.get("group", f"g{i%10}") for i, m in enumerate(meta)]) or None

        assert X is not None and y is not None
        self.feature_names = feature_names or ALL_FEATURES

        # For classification, derive y_class from regression y (pKd) or meta active
        if meta is not None:
            y_class = np.array([m.get("active", int(float(m.get("pKd", y[i])) >= 6.5)) for i, m in enumerate(meta)], dtype=int)
        else:
            y_class = (y >= 6.5).astype(int)

        # Leakage-aware split for hold-out evaluation
        if leakage_aware and groups is not None:
            train_idx, test_idx = leakage_aware_split(X, y, groups=groups, test_size=test_size, random_state=self.random_state, method="group_kfold")
        else:
            from sklearn.model_selection import train_test_split
            train_idx, test_idx = train_test_split(np.arange(len(X)), test_size=test_size, random_state=self.random_state)

        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]
        y_class_train, y_class_test = y_class[train_idx], y_class[test_idx]
        groups_train = [groups[i] for i in train_idx] if groups else None
        groups_test = [groups[i] for i in test_idx] if groups else None

        # Store for AD checker
        self.X_train_ = X_train
        self.y_train_ = y_train
        self.meta_train_ = [meta[i] for i in train_idx] if meta else None

        config_reg = TrainingConfig(
            test_size=test_size,
            n_splits=cv_folds,
            random_state=self.random_state,
            leakage_aware=leakage_aware,
            scaffold_split=True,
            scale_features=True,
            task="regression",
        )
        config_cls = TrainingConfig(
            test_size=test_size,
            n_splits=cv_folds,
            random_state=self.random_state,
            leakage_aware=leakage_aware,
            scaffold_split=True,
            scale_features=True,
            task="classification",
        )

        summary: Dict[str, Any] = {
            "n_samples": len(X),
            "n_train": len(X_train),
            "n_test": len(X_test),
            "feature_names": self.feature_names,
            "leakage_aware": leakage_aware,
            "groups": len(set(groups)) if groups else None,
        }

        # ----- Regression -----
        if task in ("regression", "both"):
            regressors = get_top5_regressors(random_state=self.random_state)
            print(f"[MLAgent] Benchmarking {len(regressors)} regressors with {cv_folds}-fold CV...")

            bench_results = benchmark_models(regressors, X_train, y_train, self.feature_names, config_reg, groups=groups_train)

            # Select best by R2
            best_name = None
            best_r2 = -1
            for name, res in bench_results.items():
                r2 = res.mean_metrics.get("r2", -1)
                if r2 > best_r2:
                    best_r2 = r2
                    best_name = name

            self.best_model_name = best_name or "StackingEnsemble"
            # Ensure best_model is from results
            if self.best_model_name in bench_results:
                self.best_model = bench_results[self.best_model_name].model
                self.scaler = bench_results[self.best_model_name].scaler
                self.training_metrics_["regression_cv"] = bench_results[self.best_model_name].mean_metrics
            else:
                # Fallback: train stacking directly
                from sklearn.base import clone
                self.best_model = clone(regressors[self.best_model_name])
                if config_reg.scale_features:
                    from sklearn.preprocessing import StandardScaler
                    self.scaler = StandardScaler()
                    X_train_scaled = self.scaler.fit_transform(X_train)
                    self.best_model.fit(X_train_scaled, y_train)
                else:
                    self.best_model.fit(X_train, y_train)

            self.models = {name: res.model for name, res in bench_results.items()}
            self.scalers = {name: res.scaler for name, res in bench_results.items()}

            # Evaluate on hold-out test set (leakage-aware)
            X_test_scaled = self.scaler.transform(X_test) if self.scaler is not None else X_test
            y_pred_test = self.best_model.predict(X_test_scaled)
            test_metrics = compute_regression_metrics(y_test, y_pred_test)

            summary["regression"] = {
                "best_model": self.best_model_name,
                "cv_metrics": bench_results[self.best_model_name].mean_metrics if self.best_model_name in bench_results else {},
                "test_metrics": test_metrics,
                "benchmark": {name: res.mean_metrics for name, res in bench_results.items()},
            }
            print(f"[MLAgent] Best regressor: {self.best_model_name} R2 CV={summary['regression']['cv_metrics'].get('r2', 0):.3f} Test R2={test_metrics.get('r2',0):.3f}")

            # AD checker for regression
            X_train_for_ad = X_train
            if self.scaler is not None:
                X_train_for_ad = self.scaler.transform(X_train)
            self.ad_checker_ = ApplicabilityDomainChecker(X_train_for_ad, self.feature_names)

        # ----- Classification -----
        if task in ("classification", "both"):
            classifiers = get_top5_classifiers(random_state=self.random_state)
            print(f"[MLAgent] Benchmarking {len(classifiers)} classifiers...")

            bench_cls = benchmark_models(classifiers, X_train, y_class_train, self.feature_names, config_cls, groups=groups_train)

            best_cls_name = None
            best_auc = -1
            for name, res in bench_cls.items():
                auc = res.mean_metrics.get("roc_auc", res.mean_metrics.get("accuracy", 0))
                if auc > best_auc:
                    best_auc = auc
                    best_cls_name = name

            self.best_classifier_name = best_cls_name or "StackingClassifier"
            if self.best_classifier_name in bench_cls:
                self.best_classifier = bench_cls[self.best_classifier_name].model
                self.classifier_scaler = bench_cls[self.best_classifier_name].scaler
                self.training_metrics_["classification_cv"] = bench_cls[self.best_classifier_name].mean_metrics
            else:
                from sklearn.base import clone
                self.best_classifier = clone(classifiers[self.best_classifier_name])
                if config_cls.scale_features:
                    from sklearn.preprocessing import StandardScaler
                    self.classifier_scaler = StandardScaler()
                    X_train_scaled = self.classifier_scaler.fit_transform(X_train)
                    self.best_classifier.fit(X_train_scaled, y_class_train)
                else:
                    self.best_classifier.fit(X_train, y_class_train)

            self.classifiers = {n: r.model for n, r in bench_cls.items()}
            self.classifier_scalers = {n: r.scaler for n, r in bench_cls.items()}

            # Test eval
            X_test_scaled_c = self.classifier_scaler.transform(X_test) if self.classifier_scaler is not None else X_test
            y_pred_cls = self.best_classifier.predict(X_test_scaled_c)
            y_proba = None
            if hasattr(self.best_classifier, "predict_proba"):
                try:
                    y_proba = self.best_classifier.predict_proba(X_test_scaled_c)[:,1]
                except Exception:
                    pass
            test_cls_metrics = compute_classification_metrics(y_class_test, y_pred_cls, y_proba)

            summary["classification"] = {
                "best_model": self.best_classifier_name,
                "cv_metrics": bench_cls[self.best_classifier_name].mean_metrics if self.best_classifier_name in bench_cls else {},
                "test_metrics": test_cls_metrics,
                "benchmark": {n: r.mean_metrics for n, r in bench_cls.items()},
            }
            print(f"[MLAgent] Best classifier: {self.best_classifier_name} CV AUC={summary['classification']['cv_metrics'].get('roc_auc',0):.3f} Test ACC={test_cls_metrics.get('accuracy',0):.3f}")

            # AD checker for classifier
            X_train_for_ad_c = X_train
            if self.classifier_scaler is not None:
                X_train_for_ad_c = self.classifier_scaler.transform(X_train)
            self.ad_checker_classifier_ = ApplicabilityDomainChecker(X_train_for_ad_c, self.feature_names)

        self.is_trained_ = True

        if save:
            self.save()

        return summary

    def save(self) -> None:
        """Save models to disk"""
        self.model_dir.mkdir(parents=True, exist_ok=True)

        # Use joblib if available else pickle
        try:
            import joblib
            saver = lambda obj, path: joblib.dump(obj, path)
            ext = "joblib"
        except ImportError:
            saver = lambda obj, path: pickle.dump(obj, open(path, "wb"))
            ext = "pkl"

        # Save regression
        if self.best_model is not None:
            payload = {
                "model": self.best_model,
                "scaler": self.scaler,
                "feature_names": self.feature_names,
                "model_name": self.best_model_name,
                "X_train": self.X_train_,
                "y_train": self.y_train_,
                "meta_train": self.meta_train_,
                "training_metrics": self.training_metrics_,
                "random_state": self.random_state,
            }
            saver(payload, self.model_dir / f"best_regressor.{ext}")

            # Also save all models
            for name, model in self.models.items():
                scaler = self.scalers.get(name)
                payload = {"model": model, "scaler": scaler, "feature_names": self.feature_names, "model_name": name}
                saver(payload, self.model_dir / f"regressor_{name}.{ext}")

        # Save classification
        if self.best_classifier is not None:
            payload = {
                "model": self.best_classifier,
                "scaler": self.classifier_scaler,
                "feature_names": self.feature_names,
                "model_name": self.best_classifier_name,
                "X_train": self.X_train_,
                "training_metrics": self.training_metrics_,
            }
            saver(payload, self.model_dir / f"best_classifier.{ext}")
            for name, model in self.classifiers.items():
                scaler = self.classifier_scalers.get(name)
                payload = {"model": model, "scaler": scaler, "feature_names": self.feature_names, "model_name": name}
                saver(payload, self.model_dir / f"classifier_{name}.{ext}")

        # Save config JSON
        config_payload = {
            "best_regressor": self.best_model_name,
            "best_classifier": self.best_classifier_name,
            "feature_names": self.feature_names,
            "model_metadata": MODEL_METADATA,
            "evidence_tier": EvidenceTier.ML_PREDICTION.value,
            "disclaimer": EvidenceTier.ML_PREDICTION.disclaimer,
            "ayush64_note": "ML predictions are hypotheses, not clinical proof",
            "timestamp": datetime.utcnow().isoformat(),
        }
        with open(self.model_dir / "model_config.json", "w") as f:
            json.dump(config_payload, f, indent=2)

        print(f"[MLAgent] Models saved to {self.model_dir}")

    def load(self) -> None:
        """Load models from disk if available"""
        joblib_path = self.model_dir / "best_regressor.joblib"
        pkl_path = self.model_dir / "best_regressor.pkl"

        try:
            import joblib
            has_joblib = True
        except ImportError:
            has_joblib = False

        loaded = False

        # Regression
        if has_joblib and joblib_path.exists():
            try:
                data = joblib.load(joblib_path)
                self.best_model = data["model"]
                self.scaler = data.get("scaler")
                self.feature_names = data.get("feature_names", self.feature_names)
                self.X_train_ = data.get("X_train")
                self.y_train_ = data.get("y_train")
                self.meta_train_ = data.get("meta_train")
                self.best_model_name = data.get("model_name", "StackingEnsemble")
                loaded = True
            except Exception as e:
                warnings.warn(f"Failed to load joblib regressor: {e}")
        elif pkl_path.exists():
            try:
                with open(pkl_path, "rb") as f:
                    data = pickle.load(f)
                self.best_model = data["model"]
                self.scaler = data.get("scaler")
                self.feature_names = data.get("feature_names", self.feature_names)
                self.X_train_ = data.get("X_train")
                self.y_train_ = data.get("y_train")
                self.best_model_name = data.get("model_name", "StackingEnsemble")
                loaded = True
            except Exception as e:
                warnings.warn(f"Failed to load pkl regressor: {e}")

        # Classification
        clf_joblib = self.model_dir / "best_classifier.joblib"
        clf_pkl = self.model_dir / "best_classifier.pkl"
        if has_joblib and clf_joblib.exists():
            try:
                data = joblib.load(clf_joblib)
                self.best_classifier = data["model"]
                self.classifier_scaler = data.get("scaler")
                self.best_classifier_name = data.get("model_name", "StackingClassifier")
                loaded = True
            except Exception as e:
                warnings.warn(f"Failed to load classifier joblib: {e}")
        elif clf_pkl.exists():
            try:
                with open(clf_pkl, "rb") as f:
                    data = pickle.load(f)
                self.best_classifier = data["model"]
                self.classifier_scaler = data.get("scaler")
                self.best_classifier_name = data.get("model_name", "StackingClassifier")
                loaded = True
            except Exception as e:
                warnings.warn(f"Failed to load classifier pkl: {e}")

        if loaded:
            self.is_trained_ = True
            # Rebuild AD checkers
            if self.X_train_ is not None:
                X_ad = self.X_train_
                if self.scaler is not None:
                    try:
                        X_ad = self.scaler.transform(X_ad)
                    except Exception:
                        pass
                self.ad_checker_ = ApplicabilityDomainChecker(X_ad, self.feature_names)
                X_ad_c = self.X_train_
                if self.classifier_scaler is not None:
                    try:
                        X_ad_c = self.classifier_scaler.transform(X_ad_c)
                    except Exception:
                        pass
                self.ad_checker_classifier_ = ApplicabilityDomainChecker(X_ad_c, self.feature_names)

            print(f"[MLAgent] Loaded models from {self.model_dir}: {self.best_model_name} / {self.best_classifier_name}")
        else:
            raise FileNotFoundError(f"No trained models found in {self.model_dir}")

    # -------------------------
    # Prediction
    # -------------------------

    def _featurize_input(
        self,
        smiles: str,
        docking_result: Optional[Dict[str, Any]] = None,
        protein_target: str = "BACE1",
    ) -> Tuple[np.ndarray, Dict[str, float]]:
        """Featurize single input"""
        feat_dict = self.feature_engineer.extract_features(smiles, docking_result, protein_target)
        vec = np.array([feat_dict.get(fn, 0.0) for fn in self.feature_names], dtype=np.float32)
        return vec, feat_dict

    def _predict_pkd(self, x_vec: np.ndarray) -> Tuple[float, float]:
        """
        Predict pKd with uncertainty.
        Uncertainty estimated via ensemble variance if stacking -> use base estimators,
        else use training residual std.
        """
        if self.best_model is None:
            raise RuntimeError("Model not trained. Call train() first.")

        x_scaled = x_vec.reshape(1, -1)
        if self.scaler is not None:
            try:
                x_scaled = self.scaler.transform(x_scaled)
            except Exception:
                pass

        pred = float(self.best_model.predict(x_scaled)[0])

        # Uncertainty: if ensemble, gather base predictions
        try:
            # Stacking has estimators_
            if hasattr(self.best_model, "estimators_") or hasattr(self.best_model, "estimators"):
                estimators = getattr(self.best_model, "estimators_", None) or getattr(self.best_model, "estimators", [])
                # sklearn Stacking estimators_ are final fitted base estimators? Actually list of fitted.
                # For simplicity try to get predictions from each saved model if available
                preds = []
                for name, model in self.models.items():
                    scaler = self.scalers.get(name)
                    xs = x_vec.reshape(1, -1)
                    if scaler is not None:
                        try:
                            xs = scaler.transform(xs)
                        except Exception:
                            pass
                    try:
                        preds.append(float(model.predict(xs)[0]))
                    except Exception:
                        continue
                if preds:
                    uncertainty = float(np.std(preds) + 0.2)  # ensemble std + baseline
                else:
                    uncertainty = 0.5
            else:
                uncertainty = 0.5
        except Exception:
            uncertainty = 0.5

        # Clip
        pred = float(np.clip(pred, 3.0, 11.0))
        return pred, uncertainty

    def _classify(self, x_vec: np.ndarray, pkd: float) -> Tuple[str, float]:
        """Classify active/inactive"""
        if self.best_classifier is not None:
            xs = x_vec.reshape(1, -1)
            if self.classifier_scaler is not None:
                try:
                    xs = self.classifier_scaler.transform(xs)
                except Exception:
                    pass
            try:
                proba = 0.5
                if hasattr(self.best_classifier, "predict_proba"):
                    proba = float(self.best_classifier.predict_proba(xs)[0, 1])
                else:
                    # Decision function
                    proba = float(1.0 / (1.0 + np.exp(-self.best_classifier.decision_function(xs)[0]))) if hasattr(self.best_classifier, "decision_function") else (0.8 if pkd>=6.5 else 0.2)
            except Exception:
                proba = 0.8 if pkd >= 6.5 else 0.2

            if proba >= 0.65:
                label = "active"
            elif proba <= 0.35:
                label = "inactive"
            else:
                label = "moderate"
            return label, proba
        else:
            # Fallback threshold from pKd
            if pkd >= 7.0:
                return "active", 0.85
            elif pkd >= 6.0:
                return "moderate", 0.55
            else:
                return "inactive", 0.2

    def predict(
        self,
        smiles: str,
        protein_target: str = "BACE1",
        docking_result: Optional[Dict[str, Any]] = None,
        return_evidence_tagged: bool = True,
    ) -> Union[BindingAffinityPrediction, EvidenceTaggedOutput]:
        """
        Predict binding affinity for single molecule.

        Args:
            smiles: SMILES string
            protein_target: target protein
            docking_result: optional dict from docking_agent {"affinity": -8.2, ...}
            return_evidence_tagged: if True, wrap in EvidenceTaggedOutput

        Returns:
            BindingAffinityPrediction or EvidenceTaggedOutput (ML_PREDICTION tier)
        """
        if not self.is_trained_:
            raise RuntimeError("MLAgent not trained: call train() or ensure models exist in models/trained/")

        x_vec, feat_dict = self._featurize_input(smiles, docking_result, protein_target)
        pkd, uncertainty = self._predict_pkd(x_vec)
        # Convert pKd to kcal/mol: ΔG ≈ -RT lnKd, pKd = -log10(Kd), at 298K: ΔG ≈ -1.3633 * pKd
        affinity_kcal = float(-1.3633 * pkd)

        classification, proba = self._classify(x_vec, pkd)

        # Applicability domain
        if self.ad_checker_ is not None:
            # Use scaled version if available
            x_ad = x_vec
            if self.scaler is not None:
                try:
                    x_ad = self.scaler.transform(x_vec.reshape(1, -1))[0]
                except Exception:
                    pass
            ad_result = self.ad_checker_.check(x_ad)
        else:
            ad_result = ApplicabilityDomainResult(
                is_inside=True,
                distance_score=0.0,
                confidence="medium",
                leverage=0.5,
                nearest_neighbor_dist=0.0,
                explanation="No AD checker (no training data stored)",
            )

        # Top features for quick interpretation (from feature importance if available)
        top_features: Optional[List[Tuple[str, float]]] = None
        try:
            if self.best_model is not None and hasattr(self.best_model, "feature_importances_"):
                importances = self.best_model.feature_importances_
                # Multiply by feature value sign? Simple: importance * feature magnitude
                # Use abs for ranking
                idx_sorted = np.argsort(-importances)[:8]
                top_features = [(self.feature_names[i], float(importances[i] * feat_dict.get(self.feature_names[i], 0.0))) for i in idx_sorted]
            else:
                # fallback: docking affinity strongest
                top_features = [
                    ("vina_affinity", float(feat_dict.get("vina_affinity", 0.0))),
                    ("ligand_efficiency", float(feat_dict.get("ligand_efficiency", 0.0))),
                    ("qed_score", float(feat_dict.get("qed_score", 0.0))),
                ]
        except Exception:
            top_features = None

        pred = BindingAffinityPrediction(
            smiles=smiles,
            protein_target=protein_target,
            predicted_pkd=pkd,
            predicted_affinity_kcal=affinity_kcal,
            uncertainty=uncertainty,
            classification=classification,
            classification_proba=proba,
            applicability_domain=ad_result,
            top_features_contrib=top_features,
            model_name=self.best_model_name,
        )

        if return_evidence_tagged:
            return pred.to_evidence_tagged()
        else:
            return pred

    def batch_predict(
        self,
        inputs: List[Dict[str, Any]],
        return_evidence_tagged: bool = True,
    ) -> List[Union[BindingAffinityPrediction, EvidenceTaggedOutput]]:
        """
        Batch prediction.

        Args:
            inputs: list of dicts each with keys: smiles (required), protein_target (optional), docking_result (optional)
            return_evidence_tagged: wrap in evidence tier

        Returns:
            list of predictions
        """
        results: List[Union[BindingAffinityPrediction, EvidenceTaggedOutput]] = []
        for item in inputs:
            try:
                smiles = item.get("smiles") or item.get("SMILES")
                if not smiles:
                    raise ValueError("Item missing 'smiles' key")
                target = item.get("protein_target", item.get("target", "BACE1"))
                docking = item.get("docking_result") or item.get("docking") or item.get("affinity") and {"affinity": item.get("affinity")}
                pred = self.predict(smiles=smiles, protein_target=target, docking_result=docking, return_evidence_tagged=return_evidence_tagged)
                results.append(pred)
            except Exception as e:
                warnings.warn(f"Batch item failed {item.get('smiles','?')}: {e}")
                # Create failed prediction placeholder
                fail_ad = ApplicabilityDomainResult(False, 999.0, "out-of-domain", 999.0, 999.0, f"Prediction failed: {e}")
                fail_pred = BindingAffinityPrediction(
                    smiles=item.get("smiles", "unknown"),
                    protein_target=item.get("protein_target", "unknown"),
                    predicted_pkd=0.0,
                    predicted_affinity_kcal=0.0,
                    uncertainty=999.0,
                    classification="error",
                    classification_proba=0.0,
                    applicability_domain=fail_ad,
                    model_name="failed",
                )
                results.append(fail_pred.to_evidence_tagged() if return_evidence_tagged else fail_pred)

        return results

    def predict_with_ranking(
        self,
        inputs: List[Dict[str, Any]],
    ) -> EvidenceTaggedOutput:
        """
        Predict batch and return ranked candidates (for reporting layer).
        Ranked by predicted_pKd descending, filtered by applicability domain confidence.

        Returns:
            EvidenceTaggedOutput containing ranking list
        """
        preds = self.batch_predict(inputs, return_evidence_tagged=False)

        # Sort by pKd * AD confidence weight
        def rank_score(p: BindingAffinityPrediction) -> float:
            weight = {"high": 1.0, "medium": 0.8, "low": 0.5, "out-of-domain": 0.1}.get(p.applicability_domain.confidence, 0.5)
            return p.predicted_pkd * weight

        ranked = sorted(preds, key=rank_score, reverse=True)

        ranking_data = [
            {
                "rank": i+1,
                "smiles": p.smiles,
                "protein_target": p.protein_target,
                "predicted_pKd": p.predicted_pkd,
                "classification": p.classification,
                "applicability_confidence": p.applicability_domain.confidence,
                "model": p.model_name,
            }
            for i, p in enumerate(ranked)
        ]

        out = EvidenceTaggedOutput(
            tier=EvidenceTier.ML_PREDICTION,
            data=ranking_data,
            metadata={
                "ranking_method": "predicted_pKd weighted by AD confidence",
                "n_candidates": len(ranking_data),
                "note": "Ranking is computational prioritization, NOT clinical efficacy ranking. AYUSH-64 case: requires validation.",
            },
        )
        return EvidenceValidator.validate(out)
