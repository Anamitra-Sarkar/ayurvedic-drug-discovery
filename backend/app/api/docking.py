
from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter()

class DockingRequest(BaseModel):
    smiles: str
    protein_pdb_id: str = "7E9G"
    phytochemical_name: Optional[str] = None
    num_poses: int = 5

@router.post("/docking/run")
async def run_docking(req: DockingRequest):
    """Structure-based docking via the real DockingAgent (real AutoDock Vina if the
    binary is available on this host, honestly-labeled empirical fallback otherwise -
    see DockingAgent.run_docking's own mock_used flag, never fabricated here)."""
    try:
        from app.agents.docking_agent import DockingAgent
        agent = DockingAgent()
        # NOTE: this previously called agent.dock(...), a method that does not
        # exist on DockingAgent - every call silently raised AttributeError and
        # fell into a random.seed(hash(smiles))-based fake score generator below,
        # regardless of the real molecule or target. Found via live testing
        # (422s on the real request shape it also didn't match). Fixed to call
        # the real, verified-working run_docking() (same one used successfully
        # in this session's own manual Vina verification).
        tiered = agent.run_docking(
            ligand_smiles=req.smiles,
            protein_pdb_id=req.protein_pdb_id,
            ligand_id=req.phytochemical_name or None,
            num_modes=req.num_poses,
            exhaustiveness=8,  # lower than the default 16 to stay responsive on a CPU-only host
        )
        result = tiered.data if hasattr(tiered, "data") else tiered

        # Real InteractionAnalysisAgent module - built and pipeline-wired already,
        # but never called from this single-compound endpoint, so the frontend's
        # "Where it seems to touch the protein" panel was always empty. Runs in
        # "mock mode" (no real 3D docked coordinates available here) - rule-based,
        # honestly self-labeled "PLIP-mimetic" in its own output, same disclosure
        # pattern as the Vina empirical fallback above. Never let a failure here
        # break the real docking result already computed.
        try:
            from app.agents.interaction_agent import InteractionAnalysisAgent
            interaction_tiered = InteractionAnalysisAgent().analyze(
                docking_result=result, protein_target=req.protein_pdb_id
            )
            interaction_data = interaction_tiered.data if hasattr(interaction_tiered, "data") else interaction_tiered
            result["interactions"] = interaction_data.get("interactions", [])
            result["interaction_summary"] = interaction_data.get("summary", {})
        except Exception as ie:
            result["interactions"] = []
            result["interaction_summary_error"] = str(ie)

        return result
    except Exception as e:
        # Honest failure - no fabricated score, no random.seed trick.
        return {
            "smiles": req.smiles,
            "protein": req.protein_pdb_id,
            "error": str(e),
            "evidence_tier": "DOCKING_RESULT",
            "disclaimer": "Real docking failed for this request - no score was generated. This is not a fabricated result.",
        }

@router.get("/candidates/rank")
async def rank_candidates(target: str = Query("GABRA1"), limit: int = Query(11, ge=1, le=11)):
    """Rank the 11 novel neuromodulator candidates via real DockingAgent batch docking."""
    from app.agents.docking_agent import (
        DockingAgent,
        EPILEPSY_TARGETS,
        ELEVEN_NOVEL_NEUROMODULATOR_CANDIDATES,
    )
    agent = DockingAgent()
    if target in EPILEPSY_TARGETS:
        tiered = agent.rank_eleven_candidates(target=target)
        resolved_target = target
    else:
        # Treat as a PDB ID override; dock the same real candidate library against it.
        tiered = agent.batch_docking(
            phytochemical_library=ELEVEN_NOVEL_NEUROMODULATOR_CANDIDATES,
            protein_pdb_id=target,
        )
        resolved_target = target
    data = tiered.data if hasattr(tiered, "data") else tiered
    ranked = (data.get("ranked_results") or [])[:limit]
    candidates = []
    for i, r in enumerate(ranked):
        meta = r.get("library_metadata") or {}
        candidates.append({
            "rank": i + 1,
            "compound": {
                "id": meta.get("id") or meta.get("imppat_id") or r.get("ligand_id"),
                "name": meta.get("name"),
                "plant": meta.get("herb"),
                "smiles": meta.get("smiles") or meta.get("canonical_smiles"),
            },
            "database": {"evidenceTier": "DATABASE_DERIVED", "source": "IMPPAT-derived candidate library"},
            "docking": {
                "evidenceTier": "DOCKING_RESULT",
                "affinity_kcal_mol": r.get("best_affinity_kcal_mol"),
                "confidence": r.get("confidence_score"),
            },
            "tiersPresent": ["DATABASE_DERIVED", "DOCKING_RESULT"],
        })
    return {
        "evidence_tier": "DOCKING_RESULT",
        "target": resolved_target,
        "candidates": candidates,
        "total": len(candidates),
        "disclaimer": data.get("disclaimer") or "COMPUTATIONAL RANKING ONLY - NOT CLINICAL PRIORITY. Requires validation.",
    }

@router.get("/docking/scoring-info")
async def scoring_info():
    return {
        "primary_engine": "AutoDock Vina [12]",
        "speed": "Up to 100x faster than AutoDock4 with improved pose accuracy",
        "scoring": "Empirical: Lennard-Jones + H-bond + hydrophobic + steric",
        "limitation": "Binding-affinity correlation with experiment only moderate - treat as hypothesis not final affinity [14]",
        "rescoring": "DockingApp RF [13] - Random Forest rescoring comparable to SOTA ML/DL, optional ML layer atop Vina",
        "hybrid": "Linear combination AutoDock+Vina energy terms - statistically significant improvement in pKi [14]",
        "interaction": "PLIP [15] - 7-8 types without manual prep, selected for Interaction Analysis Agent",
        "evidence_tier": "DOCKING_RESULT"
    }
