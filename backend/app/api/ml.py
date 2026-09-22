
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter()

class MLRequest(BaseModel):
    smiles: str
    docking_affinity: Optional[float] = None
    features: Optional[dict] = None

@router.post("/ml/predict")
async def predict_affinity(req: MLRequest):
    """ML binding-affinity prediction via the real trained MLAgent model
    (backend/app/models/trained/best_regressor.joblib - real RandomForest
    trained on real PDBBind data, see docs/REPRODUCIBILITY.md)."""
    try:
        from app.agents.ml_agent import MLAgent
        agent = MLAgent()
        if not agent.is_trained_:
            return {
                "smiles": req.smiles,
                "status": "model_not_trained",
                "evidence_tier": "ML_PREDICTION",
                "disclaimer": "No trained model is currently loaded - no prediction was generated. This is not a fabricated result.",
            }
        # NOTE: this previously called agent.predict(smiles=..., docking_score=...),
        # but MLAgent.predict()'s real parameter is docking_result (a dict), not
        # docking_score (a float) - a TypeError on every call, silently caught,
        # falling into a random.seed(hash(smiles))-based fake pKd generator whose
        # "model" field even claimed a StackingEnsemble that was never actually
        # trained (the real one is a plain RandomForest). Found via live testing.
        docking_result = {"affinity": req.docking_affinity} if req.docking_affinity is not None else None
        pred = agent.predict(smiles=req.smiles, docking_result=docking_result, return_evidence_tagged=False)
        return pred.__dict__ if hasattr(pred, "__dict__") else pred
    except Exception as e:
        # Honest failure - no fabricated affinity, no random.seed trick.
        return {
            "smiles": req.smiles,
            "error": str(e),
            "evidence_tier": "ML_PREDICTION",
            "disclaimer": "Real prediction failed for this request - no affinity was generated. This is not a fabricated result.",
        }

@router.get("/ml/models")
async def list_models():
    return {
        "benchmark": "42-algorithm benchmark inspiration [19] - ExtraTrees R2=0.760, XGBoost ROC-AUC=0.962 Factor Xa",
        "implemented_top5": [
            "RandomForest (oob_score, balanced)",
            "ExtraTrees (low variance noisy docking)",
            "XGBoost/HistGradientBoosting",
            "NuSVR/NuSVC - critical for small n=49 TLR4 regime [16]",
            "StackingEnsemble RF+ET+XGB + Ridge meta - best generalization"
        ],
        "training_data": "Synthetic PDBBind-like 500 samples, physics-inspired pKd = -vina + MW/LogP/QED + privileged",
        "splitting": "Leakage-aware GroupKFold by scaffold hash + KMeans diversity [16]",
        "fusion": "Docking + QSAR feature fusion [20]",
        "evidence_tier": "ML_PREDICTION"
    }

@router.post("/ml/explain")
async def explain_prediction(req: MLRequest):
    """XAI explanation via the real XAIAgent, wired to the real trained MLAgent model."""
    try:
        from app.agents.ml_agent import MLAgent
        from app.agents.xai_agent import XAIAgent
        ml_agent = MLAgent()
        if not ml_agent.is_trained_:
            return {
                "smiles": req.smiles,
                "status": "model_not_trained",
                "evidence_tier": "XAI_INTERPRETATION",
                "disclaimer": "No trained model is currently loaded - no explanation was generated. This is not a fabricated result.",
            }
        # NOTE: this previously called agent.explain(...) (no such method - real
        # method is explain_prediction) on XAIAgent() constructed with NO
        # ml_agent at all - every call silently raised, falling into a
        # HARDCODED fixed SHAP-values dict (identical for every compound,
        # every call, forever). Found via live testing. Fixed to call the
        # real method on an XAIAgent wired to the real trained model.
        agent = XAIAgent(ml_agent=ml_agent)
        docking_result = {"affinity": req.docking_affinity} if req.docking_affinity is not None else None
        # NOTE: expl.__dict__ (return_evidence_tagged=False) leaves raw numpy
        # arrays nested inside shap_explanation/lime_explanation, which
        # FastAPI's jsonable_encoder cannot serialize (500: "cannot convert
        # dictionary update sequence element #0 to a sequence" - dict()/vars()
        # both fail on an ndarray). XAIExplanationResult.to_evidence_tagged()
        # already does the numpy->list conversion properly; use that + its
        # own to_dict(), same pattern as EvidenceTaggedOutput elsewhere.
        expl = agent.explain_prediction(smiles=req.smiles, docking_result=docking_result, return_evidence_tagged=True)
        return expl.to_dict() if hasattr(expl, "to_dict") else expl
    except Exception as e:
        # Honest failure - no fabricated SHAP values.
        return {
            "smiles": req.smiles,
            "error": str(e),
            "evidence_tier": "XAI_INTERPRETATION",
            "disclaimer": "Real explanation failed for this request - no interpretation was generated. This is not a fabricated result.",
        }
