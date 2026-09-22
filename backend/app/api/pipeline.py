
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import logging
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.agents.evidence_tiers import EvidenceTier

router = APIRouter()
logger = logging.getLogger(__name__)

class PipelineRequest(BaseModel):
    plant_names: Optional[List[str]] = None
    phytochemical_names: Optional[List[str]] = None
    protein_target: str = "7E9G"  # mGluR2 default
    top_n: int = 10
    include_xai: bool = True
    include_literature: bool = True
    therapeutic_area: Optional[str] = None

class PipelineResponse(BaseModel):
    request_id: str
    status: str
    candidates: List[Dict[str, Any]]
    evidence_summary: Dict[str, int]
    validation_report: Dict[str, Any]
    report_path: Optional[str] = None
    warning: str = "⚠️ COMPUTATIONAL ONLY - Must not present as clinical proof"

@router.post("/pipeline/run", response_model=PipelineResponse)
async def run_pipeline(request: PipelineRequest, background_tasks: BackgroundTasks):
    """
    Run full 6-layer pipeline:
    Database -> Cheminformatics -> Docking -> ML -> XAI -> Literature -> Validation -> Report
    
    Every output tagged with 5-tier evidence system.
    AYUSH-64 justification enforced.
    """
    try:
        import asyncio
        from app.agents.orchestrator import AyurvedicDiscoveryOrchestrator
        orchestrator = AyurvedicDiscoveryOrchestrator()
        target_plant = (request.plant_names or ["Withania somnifera"])[0]
        summary = await asyncio.to_thread(
            orchestrator.run_pipeline,
            target_plant=target_plant,
            target_protein=request.protein_target,
        )
        final_state = summary.get("final_state", {})
        # The real orchestrator's evidence_tier_summary is {tier: {tier_number,
        # count, disclaimer, ...}} (rich per-tier detail), but this endpoint's
        # response model expects a simple {tier: count} map - previously passed
        # the raw dict straight through, which failed Pydantic validation on
        # every single real (successful!) pipeline run and silently fell into a
        # fabricated-mock-candidates fallback that ALSO no longer worked
        # (create_mock_candidates doesn't exist in evidence_tiers.py), causing
        # a 500 either way. Found via live testing - logs showed the real
        # 9-node orchestrator completing successfully every time, the response
        # serialization was the only real bug.
        raw_summary = summary.get("evidence_tier_summary", {}) or {}
        evidence_summary = {
            tier: (v.get("count", 0) if isinstance(v, dict) else v)
            for tier, v in raw_summary.items()
        }
        return PipelineResponse(
            request_id=summary["pipeline_id"],
            status=summary["status"],
            candidates=final_state.get("ranked_candidates", [])[: request.top_n],
            evidence_summary=evidence_summary,
            validation_report=final_state.get("validation_report", {}),
            report_path=summary.get("final_output_path"),
        )
    except Exception as e:
        # Honest failure - never fabricate candidates. The old fallback here
        # imported a function (create_mock_candidates) that doesn't exist in
        # this codebase; even if it had, presenting fabricated candidates as
        # pipeline output would violate this project's core anti-overclaim
        # requirement. Real failures surface as a real error instead.
        logger.error(f"Pipeline run failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Pipeline run failed: {e}")

@router.get("/pipeline/status/{request_id}")
async def get_status(request_id: str):
    return {"request_id": request_id, "status": "completed", "warning": "Computational only"}

@router.get("/pipeline/targets")
async def list_targets():
    """List protein targets - 10 targets including mGluR, TLR4, Factor Xa, BACE1, Mpro"""
    from pathlib import Path
    import json
    targets_path = Path(__file__).parent.parent / "data" / "proteins" / "targets.json"
    if targets_path.exists():
        return json.loads(targets_path.read_text())
    return [
        {"pdb_id": "7E9G", "name": "mGluR2", "disease": "Epilepsy", "source": "63 anti-epileptic herbs study [5]"},
        {"pdb_id": "6LU7", "name": "SARS-CoV-2 Mpro", "disease": "COVID-19", "source": "AYUSH-64 repurposing [3]"},
        {"pdb_id": "3FXI", "name": "TLR4", "disease": "Inflammation", "source": "TLR4 ML study n=49 [16]"},
    ]
