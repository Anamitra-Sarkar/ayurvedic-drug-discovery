
"""
Agents package - exports all agents for orchestrator
"""
from .evidence_tiers import EvidenceTier, TieredOutput, Citation, EvidenceTierRegistry, global_registry
# NOTE: this used to import from .other_agents, a leftover set of fabricated
# stub classes (random.seed-based fake docking/predictions) that predates
# this session's real-agent integration. Nothing in the live app imports
# from this package root today (every route imports the real modules
# directly, e.g. `from app.agents.database_agent import DatabaseAgent`), so
# it was dead code - but it silently shadowed the real agent names here,
# ready to trap any future `from app.agents import DatabaseAgent`. Fixed to
# point at the real, verified modules.
from .database_agent import DatabaseAgent
from .cheminformatics_agent import CheminformaticsAgent
from .docking_agent import DockingAgent
from .ml_agent import MLAgent
from .xai_agent import XAIAgent
from .interaction_agent import InteractionAnalysisAgent
from .literature_agent import LiteratureAgent
from .validation_agent import ValidationAgent
from .report_agent import ReportAgent
from .orchestrator import AyurvedicDiscoveryOrchestrator

__all__ = [
    "EvidenceTier",
    "TieredOutput",
    "Citation",
    "EvidenceTierRegistry",
    "global_registry",
    "DatabaseAgent",
    "CheminformaticsAgent",
    "DockingAgent",
    "MLAgent",
    "XAIAgent",
    "InteractionAnalysisAgent",
    "LiteratureAgent",
    "ValidationAgent",
    "ReportAgent",
    "AyurvedicDiscoveryOrchestrator"
]
