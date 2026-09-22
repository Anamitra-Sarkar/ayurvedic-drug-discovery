"""
Model Definitions - 42-Algorithm Benchmark Inspired
===================================================
Inspired by comprehensive benchmark of 42 ML algorithms for binding affinity.
Implements top 5 performers identified in literature for BACE1/TLR4 studies:

Top 5 ensemble (per meta-analysis):
1. RandomForest (RF) - robust to small data, feature importance built-in
2. ExtraTrees (ET) - lower bias variance than RF, good for noisy docking scores
3. XGBoost / HistGradientBoosting (XGB) - best in BACE1 combined feature R2=0.78 study
4. NuSVR / SVR (support vector regression) - strong in small n=49 TLR4 regime
5. StackingRegressor (RF+ET+XGB+NuSVR meta-learner) - ensemble generalization

All models expose unified interface per scikit-learn.
Fallbacks: If xgboost not installed, uses sklearn GradientBoosting/HistGradientBoosting.

Includes both regressors (pKd / binding affinity) and classifiers (active/inactive).
"""

from __future__ import annotations

import warnings
from typing import Dict, Any, List, Tuple, Optional, Union
from dataclasses import dataclass
import numpy as np

# sklearn imports
from sklearn.ensemble import (
    RandomForestRegressor,
    RandomForestClassifier,
    ExtraTreesRegressor,
    ExtraTreesClassifier,
    GradientBoostingRegressor,
    GradientBoostingClassifier,
    HistGradientBoostingRegressor,
    HistGradientBoostingClassifier,
    StackingRegressor,
    StackingClassifier,
)
from sklearn.svm import NuSVR, SVR, SVC, NuSVC
from sklearn.linear_model import Ridge, Lasso, ElasticNet, LogisticRegression
from sklearn.neighbors import KNeighborsRegressor, KNeighborsClassifier
from sklearn.tree import DecisionTreeRegressor, DecisionTreeClassifier

# Optional XGBoost
try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False

# Optional LightGBM
try:
    import lightgbm as lgb
    LGBM_AVAILABLE = True
except ImportError:
    LGBM_AVAILABLE = False


# Full 42-algorithm list (documented for provenance, not all instantiated)
BENCHMARK_42_ALGORITHMS = [
    # Tree Ensembles (12)
    "RandomForestRegressor", "RandomForestClassifier",
    "ExtraTreesRegressor", "ExtraTreesClassifier",
    "GradientBoostingRegressor", "GradientBoostingClassifier",
    "HistGradientBoostingRegressor", "HistGradientBoostingClassifier",
    "XGBoostRegressor", "XGBoostClassifier",
    "LightGBMRegressor", "LightGBMClassifier",
    # Support Vector (4)
    "SVR-RBF", "SVR-Linear", "NuSVR", "SVC",
    # Linear Models (8)
    "Ridge", "Lasso", "ElasticNet", "BayesianRidge",
    "HuberRegressor", "LinearSVR", "LogisticRegression", "SGDRegressor",
    # Neighbors (2)
    "KNeighborsRegressor", "KNeighborsClassifier",
    # Decision Tree (2)
    "DecisionTreeRegressor", "DecisionTreeClassifier",
    # Naive Bayes, etc (4)
    "GaussianProcessRegressor", "AdaBoostRegressor", "AdaBoostClassifier", "BaggingRegressor",
    # Neural/Network inspired (2)
    "MLPRegressor", "MLPClassifier",
    # Stacking / Voting (8)
    "StackingRegressor-RF-ET-XGB",
    "VotingRegressor",
    "StackingClassifier",
    "WeightedEnsemble",
    "CatBoost-like-ensemble",
    "ExtraTrees+RF Stack",
    "SVR+RF Stack",
    "XGB+RF Stack",
]


@dataclass
class ModelConfig:
    """Configuration for a single model"""
    name: str
    model_type: str  # "regression" or "classification"
    params: Dict[str, Any]
    description: str
    literature_r2: Optional[float] = None  # reported R2 from benchmark
    evidence_tier: str = "ML_PREDICTION"


def get_top5_regressors(random_state: int = 42) -> Dict[str, Any]:
    """
    Return top 5 regressors instantiated with production-quality params.
    Args:
        random_state: for reproducibility

    Returns:
        dict name -> sklearn regressor instance
    """
    models: Dict[str, Any] = {}

    # 1. RandomForest - robust baseline, best feature importance stability in TLR4 n=49
    models["RandomForest"] = RandomForestRegressor(
        n_estimators=200,
        max_depth=12,
        min_samples_split=4,
        min_samples_leaf=2,
        max_features="sqrt",
        bootstrap=True,
        oob_score=True,
        random_state=random_state,
        n_jobs=-1,
    )

    # 2. ExtraTrees - lower variance, handles noisy docking features well
    models["ExtraTrees"] = ExtraTreesRegressor(
        n_estimators=250,
        max_depth=15,
        min_samples_split=3,
        min_samples_leaf=2,
        max_features="sqrt",
        bootstrap=False,
        random_state=random_state,
        n_jobs=-1,
    )

    # 3. XGBoost or fallback HistGradientBoosting (BACE1 study: combined features R2 0.78)
    if XGBOOST_AVAILABLE:
        models["XGBoost"] = xgb.XGBRegressor(
            n_estimators=300,
            max_depth=6,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            reg_alpha=0.1,
            reg_lambda=1.0,
            random_state=random_state,
            n_jobs=-1,
            eval_metric="rmse",
        )
    else:
        # Fallback: HistGradientBoosting is close to XGBoost performance
        models["XGBoost"] = HistGradientBoostingRegressor(
            max_iter=300,
            max_depth=6,
            learning_rate=0.05,
            l2_regularization=1.0,
            random_state=random_state,
        )

    # 4. NuSVR - crucial for small dataset n=49 TLR4 study, good generalization
    # Nu controls fraction of support vectors; good for applicability domain small n
    models["NuSVR"] = NuSVR(
        nu=0.5,
        C=1.0,
        kernel="rbf",
        gamma="scale",
        shrinking=True,
    )

    # 5. Stacking ensemble meta-learner - best overall generalization
    # Base estimators: RF + ET + XGB/HGB + NuSVR
    base_estimators = [
        ("rf", RandomForestRegressor(n_estimators=100, max_depth=10, random_state=random_state, n_jobs=-1)),
        ("et", ExtraTreesRegressor(n_estimators=100, max_depth=12, random_state=random_state, n_jobs=-1)),
    ]
    if XGBOOST_AVAILABLE:
        base_estimators.append(
            ("xgb", xgb.XGBRegressor(n_estimators=100, max_depth=5, learning_rate=0.08, random_state=random_state, n_jobs=-1))
        )
    else:
        base_estimators.append(
            ("hgb", HistGradientBoostingRegressor(max_iter=150, learning_rate=0.08, random_state=random_state))
        )

    # Meta-learner: Ridge for stability (avoid overfit in small data)
    models["StackingEnsemble"] = StackingRegressor(
        estimators=base_estimators,
        final_estimator=Ridge(alpha=1.0, random_state=random_state),
        cv=5,
        passthrough=False,  # don't pass original features to meta-learner in small n regime to avoid leakage
        n_jobs=-1,
    )

    return models


def get_top5_classifiers(random_state: int = 42) -> Dict[str, Any]:
    """
    Top 5 classifiers for active/inactive classification.
    Threshold: pIC50 > 5 / docking affinity < -7 kcal/mol => active
    """
    models: Dict[str, Any] = {}

    models["RandomForestClassifier"] = RandomForestClassifier(
        n_estimators=200,
        max_depth=12,
        min_samples_split=4,
        class_weight="balanced",
        random_state=random_state,
        n_jobs=-1,
    )

    models["ExtraTreesClassifier"] = ExtraTreesClassifier(
        n_estimators=250,
        max_depth=15,
        class_weight="balanced",
        random_state=random_state,
        n_jobs=-1,
    )

    if XGBOOST_AVAILABLE:
        models["XGBoostClassifier"] = xgb.XGBClassifier(
            n_estimators=300,
            max_depth=6,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            eval_metric="logloss",
            use_label_encoder=False,
            random_state=random_state,
            n_jobs=-1,
        )
    else:
        models["XGBoostClassifier"] = HistGradientBoostingClassifier(
            max_iter=300,
            learning_rate=0.05,
            random_state=random_state,
        )

    models["NuSVC"] = NuSVC(
        nu=0.5,
        kernel="rbf",
        gamma="scale",
        class_weight="balanced",
        probability=True,  # needed for ROC-AUC
    )

    base_clf = [
        ("rf", RandomForestClassifier(n_estimators=100, max_depth=10, class_weight="balanced", random_state=random_state, n_jobs=-1)),
        ("et", ExtraTreesClassifier(n_estimators=100, max_depth=12, class_weight="balanced", random_state=random_state, n_jobs=-1)),
    ]
    if XGBOOST_AVAILABLE:
        base_clf.append(("xgb", xgb.XGBClassifier(n_estimators=100, max_depth=5, learning_rate=0.08, use_label_encoder=False, eval_metric="logloss", random_state=random_state, n_jobs=-1)))
    else:
        base_clf.append(("hgb", HistGradientBoostingClassifier(max_iter=150, random_state=random_state)))

    models["StackingClassifier"] = StackingClassifier(
        estimators=base_clf,
        final_estimator=LogisticRegression(C=1.0, max_iter=500, random_state=random_state, class_weight="balanced"),
        cv=5,
        stack_method="predict_proba",
        n_jobs=-1,
    )

    return models


def get_full_benchmark_suite(random_state: int = 42) -> Dict[str, Any]:
    """
    Full 42-algorithm benchmark suite inspired list, instantiated where feasible.
    For production, we provide representative subset of 15 that run without heavy deps.
    Documented for literature provenance.
    """
    suite = {}

    # Add top 5 regressors
    suite.update(get_top5_regressors(random_state=random_state))

    # Additional regressors for benchmark completeness (selected, lightweight)
    suite["Ridge"] = Ridge(alpha=1.0, random_state=random_state)
    suite["Lasso"] = Lasso(alpha=0.01, max_iter=2000, random_state=random_state)
    suite["ElasticNet"] = ElasticNet(alpha=0.01, l1_ratio=0.5, max_iter=2000, random_state=random_state)
    suite["KNN"] = KNeighborsRegressor(n_neighbors=5, weights="distance")
    suite["DecisionTree"] = DecisionTreeRegressor(max_depth=10, random_state=random_state)
    suite["GradientBoosting"] = GradientBoostingRegressor(
        n_estimators=150, max_depth=4, learning_rate=0.1, random_state=random_state
    )
    # SVR variants
    suite["SVR_RBF"] = SVR(kernel="rbf", C=1.0, gamma="scale")
    suite["SVR_Linear"] = SVR(kernel="linear", C=1.0)

    return suite


def select_best_model_by_cv(
    cv_results: Dict[str, Dict[str, float]],
    metric: str = "r2",
) -> str:
    """
    Select best model based on CV metric.

    Args:
        cv_results: dict model_name -> {metric: score, ...}
        metric: metric to optimize (r2, rmse, etc)

    Returns:
        best model name
    """
    if metric in ["rmse", "mse", "mae"]:
        # Lower is better
        best = min(cv_results.items(), key=lambda kv: kv[1].get(metric, float("inf")))
    else:
        # Higher is better (r2, roc_auc)
        best = max(cv_results.items(), key=lambda kv: kv[1].get(metric, float("-inf")))
    return best[0]


# Metadata for documentation & XAI
MODEL_METADATA = {
    "RandomForest": {
        "family": "tree_ensemble",
        "bias": "low variance, built-in feature importance",
        "literature": "Consistently top-3 in BACE1/TLR4 benchmarks",
        "interpretability": "high (feature_importances_)",
        "applicability_domain": "requires >50 samples for stability; oob_score available",
    },
    "ExtraTrees": {
        "family": "tree_ensemble_extremely_randomized",
        "bias": "even lower variance than RF; good for noisy docking",
        "literature": "Best in small-n studies due to regularization via randomization",
        "interpretability": "high",
        "applicability_domain": "robust to outliers",
    },
    "XGBoost": {
        "family": "gradient_boosting",
        "bias": "high capacity but regularization via subsample/colsample; R2 0.78 in BACE1 combined study",
        "literature": "BACE1 hybrid model: docking+QSAR => 0.78 R2",
        "interpretability": "medium (gain/cover, SHAP friendly)",
        "applicability_domain": "sensitive to hyperparams; hist fallback when XGB NA",
    },
    "NuSVR": {
        "family": "kernel_method",
        "bias": "excellent for small n=49 (TLR4); nu controls support vector fraction",
        "literature": "TLR4 study n=49 used diversity-aware SVR for low data regime",
        "interpretability": "low; needs SHAP/LIME",
        "applicability_domain": "RBF kernel requires scaling; distance-based applicability check critical",
    },
    "StackingEnsemble": {
        "family": "meta-ensemble",
        "bias": "best generalization via wisdom of crowds; Ridge meta-learner prevents overfit",
        "literature": "Meta-analysis of 42 algorithms shows stacking > single model",
        "interpretability": "medium via base learners",
        "applicability_domain": "computationally heavier; CV ensures robustness",
    },
}
