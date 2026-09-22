"""
LangGraph-style Orchestrator for Ayurvedic Drug Discovery Pipeline
===================================================================
Coordinates all 7 agents in pipeline:
Database -> Cheminformatics -> Docking -> Interaction -> ML -> XAI -> Literature -> Validation -> Report

Implemented as state machine with:
- Error handling, checkpointing, parallel execution where possible
- Provide run_pipeline() method as main entry point

Design inspirations:
- LangGraph state management (StateGraph style but lightweight dependency-free)
- Checkpointing via JSON serialization
- Supports both sequential and parallel node execution
- Evidence tier enforcement via central module
"""

from typing import List, Dict, Any, Optional, Callable
import logging
import os
import sys
import json
import time
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from app.agents.evidence_tiers import EvidenceTier, TieredOutput, global_registry
from app.agents.database_agent import DatabaseAgent
from app.agents.cheminformatics_agent import CheminformaticsAgent
from app.agents.docking_agent import DockingAgent
from app.agents.interaction_agent import InteractionAnalysisAgent
from app.agents.ml_agent import MLAgent
from app.agents.xai_agent import XAIAgent
from app.agents.literature_agent import LiteratureAgent
from app.agents.validation_agent import ValidationAgent
from app.agents.report_agent import ReportAgent

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


@dataclass
class PipelineState:
    """LangGraph-style state - dict-like with checkpoint support."""
    pipeline_id: str = field(default_factory=lambda: f"pipeline_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}")
    target_plant: str = "Withania somnifera"
    target_protein: str = "6LU7"  # SARS-CoV-2 Mpro
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    # Intermediate results
    database_results: Dict[str, Any] = field(default_factory=dict)
    cheminformatics_results: Dict[str, Any] = field(default_factory=dict)
    docking_results: Dict[str, Any] = field(default_factory=dict)
    ml_predictions: List[Dict[str, Any]] = field(default_factory=list)
    ml_results: Dict[str, Any] = field(default_factory=dict)
    xai_results: Dict[str, Any] = field(default_factory=dict)
    literature_results: Dict[str, Any] = field(default_factory=dict)
    literature_corpus_stats: Dict[str, Any] = field(default_factory=dict)

    # Tiered outputs aggregate (for validation & reporting)
    tiered_outputs: List[Dict[str, Any]] = field(default_factory=list)  # serialized TieredOutput dicts

    # Validation & Reporting
    validation_report: Dict[str, Any] = field(default_factory=dict)
    report: Dict[str, Any] = field(default_factory=dict)
    ranked_candidates: List[Dict[str, Any]] = field(default_factory=list)
    final_output: Dict[str, Any] = field(default_factory=dict)

    # Orchestration meta
    current_node: str = "START"
    completed_nodes: List[str] = field(default_factory=list)
    failed_nodes: List[Dict[str, Any]] = field(default_factory=list)
    checkpoints: List[str] = field(default_factory=list)
    corpus_id_set: Optional[List[str]] = None
    literature_queries: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pipeline_id": self.pipeline_id,
            "target_plant": self.target_plant,
            "target_protein": self.target_protein,
            "created_at": self.created_at,
            "database_results": self.database_results,
            "cheminformatics_results": self.cheminformatics_results,
            "docking_results": self.docking_results,
            "ml_predictions": self.ml_predictions,
            "ml_results": self.ml_results,
            "xai_results": self.xai_results,
            "literature_results": self.literature_results,
            "literature_corpus_stats": self.literature_corpus_stats,
            "tiered_outputs": self.tiered_outputs,
            "validation_report": self.validation_report,
            "report": self.report,
            "ranked_candidates": self.ranked_candidates,
            "final_output": self.final_output,
            "current_node": self.current_node,
            "completed_nodes": self.completed_nodes,
            "failed_nodes": self.failed_nodes,
            "checkpoints": self.checkpoints,
            "corpus_id_set": self.corpus_id_set,
            "literature_queries": self.literature_queries
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PipelineState":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class NodeDefinition:
    """Definition of a LangGraph node."""
    name: str
    agent: Any
    run_method: str = "run_node"
    dependencies: List[str] = field(default_factory=list)  # nodes that must complete before
    can_parallel: bool = False
    retries: int = 2
    timeout_sec: int = 300


class AyurvedicDiscoveryOrchestrator:
    """
    Main orchestrator - LangGraph style state machine.
    Main entry point for full pipeline via run_pipeline()
    """

    def __init__(
        self,
        checkpoint_dir: Optional[str] = None,
        enable_parallel: bool = True
    ):
        self.orchestrator_name = "AyurvedicDiscoveryOrchestrator"
        base = Path(__file__).parent.parent.parent
        self.checkpoint_dir = Path(checkpoint_dir) if checkpoint_dir else base / "data" / "checkpoints"
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

        self.enable_parallel = enable_parallel

        # Initialize all 7+ agents
        logger.info(f"[{self.orchestrator_name}] Initializing agents...")
        self.agents = {}
        self.agents["database"] = DatabaseAgent()
        self.agents["cheminformatics"] = CheminformaticsAgent()
        self.agents["docking"] = DockingAgent()
        self.agents["interaction"] = InteractionAnalysisAgent()
        self.agents["ml"] = MLAgent()
        self.agents["xai"] = XAIAgent(ml_agent=self.agents["ml"])
        self.agents["literature"] = LiteratureAgent()
        self.agents["validation"] = ValidationAgent()
        self.agents["report"] = ReportAgent()

        # Define graph - LangGraph style nodes and edges
        self.nodes: Dict[str, NodeDefinition] = {
            "database": NodeDefinition(name="database", agent=self.agents["database"], dependencies=[], can_parallel=False),
            "cheminformatics": NodeDefinition(name="cheminformatics", agent=self.agents["cheminformatics"], dependencies=["database"], can_parallel=False),
            "docking": NodeDefinition(name="docking", agent=self.agents["docking"], dependencies=["cheminformatics"], can_parallel=False),
            "interaction": NodeDefinition(name="interaction", agent=self.agents["interaction"], dependencies=["docking"], can_parallel=True),
            "ml": NodeDefinition(name="ml", agent=self.agents["ml"], dependencies=["docking"], can_parallel=False),
            "xai": NodeDefinition(name="xai", agent=self.agents["xai"], dependencies=["ml"], can_parallel=False),
            "literature": NodeDefinition(name="literature", agent=self.agents["literature"], dependencies=["ml"], can_parallel=True),  # parallel with XAI
            "validation": NodeDefinition(name="validation", agent=self.agents["validation"], dependencies=["xai", "literature"], can_parallel=False),
            "report": NodeDefinition(name="report", agent=self.agents["report"], dependencies=["validation"], can_parallel=False),
        }

        # Ingest literature corpus early
        logger.info(f"[{self.orchestrator_name}] Ingesting literature corpus...")
        self.agents["literature"].ingest_corpus(rebuild=False)

        logger.info(f"[{self.orchestrator_name}] Initialized with nodes: {list(self.nodes.keys())}")

    def _save_checkpoint(self, state: PipelineState, node_name: str):
        """Checkpoint state to JSON for resuming."""
        checkpoint_path = self.checkpoint_dir / f"{state.pipeline_id}_{node_name}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        try:
            with open(checkpoint_path, 'w') as f:
                json.dump(state.to_dict(), f, indent=2, default=str)
            state.checkpoints.append(str(checkpoint_path))
            logger.info(f"[Checkpoint] Saved after {node_name}: {checkpoint_path}")
        except Exception as e:
            logger.warning(f"Checkpoint save failed after {node_name}: {e}")

    def _run_single_node(self, node: NodeDefinition, state: PipelineState) -> PipelineState:
        """Run a single node with retry and error handling."""
        logger.info(f"[{self.orchestrator_name}] >>> Running node: {node.name}")

        start_time = time.time()
        state.current_node = node.name
        attempt = 0
        last_error = None

        while attempt <= node.retries:
            try:
                # Call agent's run_node method
                run_method = getattr(node.agent, node.run_method)
                state_dict = state.to_dict()
                new_state_dict = run_method(state_dict)

                # Merge result back into PipelineState
                for k, v in new_state_dict.items():
                    if hasattr(state, k):
                        setattr(state, k, v)
                    else:
                        # Add extra keys to state dict dynamic
                        pass

                state.completed_nodes.append(node.name)
                elapsed = time.time() - start_time
                logger.info(f"[{self.orchestrator_name}] <<< Node {node.name} completed in {elapsed:.2f}s (attempt {attempt+1})")

                # Checkpoint
                self._save_checkpoint(state, node.name)
                return state

            except Exception as e:
                last_error = e
                attempt += 1
                logger.error(f"[{self.orchestrator_name}] Node {node.name} failed attempt {attempt}/{node.retries+1}: {e}", exc_info=True)
                if attempt <= node.retries:
                    time.sleep(2 ** attempt)  # exponential backoff

        # All retries exhausted
        logger.error(f"[{self.orchestrator_name}] Node {node.name} failed after {node.retries+1} attempts: {last_error}")
        state.failed_nodes.append({"node": node.name, "error": str(last_error), "timestamp": datetime.utcnow().isoformat()})
        # Continue anyway with degraded state to prevent full pipeline failure - skip blocker
        return state

    def _can_run(self, node: NodeDefinition, state: PipelineState) -> bool:
        """Check if dependencies satisfied."""
        for dep in node.dependencies:
            if dep not in state.completed_nodes:
                return False
        if node.name in state.completed_nodes:
            return False
        return True

    def run_pipeline(
        self,
        target_plant: str = "Withania somnifera",
        target_protein: str = "6LU7",
        pipeline_id: Optional[str] = None,
        literature_queries: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Main entry point for full pipeline.
        Implements state machine with error handling, checkpointing, parallel execution where possible.

        Flow:
        Database -> Cheminformatics -> Docking -> ML -> (XAI parallel Literature) -> Validation -> Report
        """
        pipeline_id = pipeline_id or f"pipeline_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        logger.info(f"[{self.orchestrator_name}] ========= Starting pipeline {pipeline_id} =========")
        logger.info(f"Target plant: {target_plant}, protein: {target_protein}")

        state = PipelineState(
            pipeline_id=pipeline_id,
            target_plant=target_plant,
            target_protein=target_protein,
            literature_queries=literature_queries or [
                "AYUSH-64 formulation mechanism and clinical evidence",
                f"{target_plant} phytochemicals docking against {target_protein}",
                "IMPPAT database curation and druggability",
                "Withaferin A toxicity and safety",
                "RAG hallucination reduction from 60% to 0% with grounding",
                "Agentic AI validation agent prevents error propagation"
            ]
        )

        # Set corpus IDs for hallucination validation
        corpus_stats = self.agents["literature"].get_corpus_stats()
        state.literature_corpus_stats = corpus_stats
        # We'll fill corpus_id_set after literature ingestion
        state.corpus_id_set = list(self.agents["literature"].corpus_id_set) if hasattr(self.agents["literature"], 'corpus_id_set') else []

        # State machine execution loop
        pending_nodes = set(self.nodes.keys())
        loop_guard = 0
        max_loops = 20

        while pending_nodes and loop_guard < max_loops:
            loop_guard += 1
            runnable = [self.nodes[n] for n in pending_nodes if self._can_run(self.nodes[n], state)]

            if not runnable:
                if pending_nodes:
                    # Check if deadlock due to failed dependencies
                    remaining_deps = {n: self.nodes[n].dependencies for n in pending_nodes}
                    logger.warning(f"Deadlock? Pending {pending_nodes}, dependencies {remaining_deps}, completed {state.completed_nodes}")
                    # Break deadlock by skipping failed nodes if possible (skip blockers)
                    # For validation, allow partial completion
                    for node_name in list(pending_nodes):
                        deps = self.nodes[node_name].dependencies
                        if any(d in [f["node"] for f in state.failed_nodes] for d in deps):
                            logger.warning(f"Skipping node {node_name} due to failed dependencies - marking as completed with warning")
                            state.completed_nodes.append(node_name)
                            pending_nodes.remove(node_name)
                    continue
                break

            # Separate parallelizable vs sequential
            parallel_nodes = [n for n in runnable if n.can_parallel and self.enable_parallel]
            sequential_nodes = [n for n in runnable if not n.can_parallel or not self.enable_parallel]

            # Run parallel nodes together
            if parallel_nodes:
                logger.info(f"[{self.orchestrator_name}] Running in parallel: {[n.name for n in parallel_nodes]}")
                with ThreadPoolExecutor(max_workers=len(parallel_nodes)) as executor:
                    future_to_node = {executor.submit(self._run_single_node, node, PipelineState(**state.to_dict())): node for node in parallel_nodes}
                    # Collect results - merge tiered_outputs and other fields
                    merged_tiered = list(state.tiered_outputs)
                    merged_dict_updates = {}
                    for future in as_completed(future_to_node):
                        node = future_to_node[future]
                        try:
                            new_state: PipelineState = future.result()
                            # Merge
                            for k in ["database_results","cheminformatics_results","docking_results","ml_predictions","ml_results","xai_results","literature_results","literature_corpus_stats"]:
                                if getattr(new_state, k):
                                    # Merge logic: if dict, update; if list, extend
                                    existing = getattr(state, k)
                                    new_val = getattr(new_state, k)
                                    if isinstance(existing, dict) and isinstance(new_val, dict):
                                        existing.update(new_val)
                                    elif isinstance(existing, list) and isinstance(new_val, list):
                                        # For ml_predictions list etc, dedup later
                                        if new_val and existing != new_val:
                                            # Extend if not already
                                            for item in new_val:
                                                if item not in existing:
                                                    existing.append(item)
                                    else:
                                        setattr(state, k, new_val)

                            # Merge tiered outputs dedup by tier+content hash
                            for td in new_state.tiered_outputs:
                                if td not in merged_tiered:
                                    merged_tiered.append(td)

                            state.completed_nodes.append(node.name)
                            pending_nodes.remove(node.name)
                            logger.info(f"Parallel node {node.name} merged")

                        except Exception as e:
                            logger.error(f"Parallel node {node.name} failed: {e}", exc_info=True)
                            state.failed_nodes.append({"node": node.name, "error": str(e), "parallel": True})
                            pending_nodes.remove(node.name)

                    state.tiered_outputs = merged_tiered
                # Checkpoint after parallel batch
                self._save_checkpoint(state, f"parallel_batch_{'_'.join([n.name for n in parallel_nodes])}")

            # Run sequential nodes one by one (topological order)
            for node in sorted(sequential_nodes, key=lambda n: len(n.dependencies)):
                if node.name not in pending_nodes:
                    continue
                if not self._can_run(node, state):
                    continue
                state = self._run_single_node(node, state)
                pending_nodes.remove(node.name)

        logger.info(f"[{self.orchestrator_name}] Pipeline execution finished loop guard {loop_guard}")
        logger.info(f"Completed nodes: {state.completed_nodes}, Failed: {state.failed_nodes}")

        # Final state dict
        final_state = state.to_dict()

        # Generate summary
        summary = {
            "pipeline_id": pipeline_id,
            "status": "completed" if len(state.failed_nodes) == 0 else "completed_with_failures",
            "completed_nodes": state.completed_nodes,
            "failed_nodes": state.failed_nodes,
            "target_plant": target_plant,
            "target_protein": target_protein,
            "num_tiered_outputs": len(state.tiered_outputs),
            "num_ranked_candidates": len(state.ranked_candidates),
            "validation_passed": state.validation_report.get("overall_valid", False) if state.validation_report else False,
            "report_paths": state.report.get("json_path") and state.report.get("markdown_path"),
            "evidence_tier_summary": state.validation_report.get("evidence_tier_summary") if state.validation_report else {},
            "final_output_path": state.report.get("json_path"),
            "final_state": final_state
        }

        logger.info(f"[{self.orchestrator_name}] ========= Pipeline {pipeline_id} finished: {summary['status']} =========")
        return summary

    def resume_from_checkpoint(self, checkpoint_path: str) -> Dict[str, Any]:
        """Resume pipeline from a checkpoint JSON."""
        logger.info(f"[{self.orchestrator_name}] Resuming from checkpoint {checkpoint_path}")
        try:
            with open(checkpoint_path, 'r') as f:
                state_dict = json.load(f)
            state = PipelineState.from_dict(state_dict)
            pipeline_id = state.pipeline_id

            # Re-run remaining nodes
            remaining = [n for n in self.nodes.keys() if n not in state.completed_nodes]
            logger.info(f"Remaining nodes to run: {remaining}")

            pending_nodes = set(remaining)
            loop_guard = 0
            while pending_nodes and loop_guard < 20:
                loop_guard += 1
                runnable = [self.nodes[n] for n in pending_nodes if self._can_run(self.nodes[n], state)]
                for node in runnable:
                    state = self._run_single_node(node, state)
                    pending_nodes.remove(node.name)

            return {
                "pipeline_id": pipeline_id,
                "status": "resumed_completed",
                "completed_nodes": state.completed_nodes,
                "final_state": state.to_dict()
            }
        except Exception as e:
            logger.error(f"Resume failed: {e}", exc_info=True)
            return {"status": "resume_failed", "error": str(e)}


# Main entry point
def main():
    orchestrator = AyurvedicDiscoveryOrchestrator(enable_parallel=True)
    result = orchestrator.run_pipeline(
        target_plant="Withania somnifera",
        target_protein="6LU7"
    )
    print(json.dumps(result, indent=2, default=str))

if __name__ == "__main__":
    main()
