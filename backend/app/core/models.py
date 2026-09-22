"""
Pydantic Models for API
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from enum import Enum

class EvidenceTierEnum(str, Enum):
    database_derived = "database_derived"
    molecular_docking_result = "molecular_docking_result"
    machine_learning_prediction = "machine_learning_prediction"
    explainable_ai_interpretation = "explainable_ai_interpretation"
    literature_derived_llm_synthesized = "literature_derived_llm_synthesized"

class CompoundRequest(BaseModel):
    plant: Optional[str] = "Withania somnifera"
    protein: str = "6LU7"
    literature_queries: Optional[List[str]] = None

class PipelineResponse(BaseModel):
    pipeline_id: str
    status: str
    completed_nodes: List[str]
    validation_passed: bool
    ranked_candidates: List[Dict[str, Any]] = Field(default_factory=list)
    report_path: Optional[str] = None

class LiteratureQueryRequest(BaseModel):
    query: str
    top_k: int = 5

class ValidationRequest(BaseModel):
    tiered_outputs: List[Dict[str, Any]]
    corpus_ids: Optional[List[str]] = None
