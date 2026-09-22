"""
Config module for Ayurvedic Drug Discovery Pipeline
- Settings, paths, evidence tier definitions, constants.
"""
from pathlib import Path
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field, validator
import os

# Base paths
BACKEND_ROOT = Path(__file__).resolve().parent.parent
APP_ROOT = BACKEND_ROOT / "app"
DATA_ROOT = BACKEND_ROOT / "data"
MODELS_ROOT = DATA_ROOT / "models"
DB_ROOT = DATA_ROOT / "databases"
LITERATURE_ROOT = DATA_ROOT / "literature"
UPLOADS_ROOT = DATA_ROOT / "uploads"

# Ensure directories exist
for p in [DATA_ROOT, MODELS_ROOT, DB_ROOT, LITERATURE_ROOT, UPLOADS_ROOT]:
    p.mkdir(parents=True, exist_ok=True)

class Settings(BaseSettings):
    """Application settings with environment overrides."""

    # App
    APP_NAME: str = "Ayurvedic Drug Discovery Pipeline"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = (
        "AI-Driven Computational Pipeline for Ayurvedic Drug Discovery: "
        "IMPPAT phytochemical DB -> RDKit -> Vina Docking -> ML Affinity -> SHAP XAI -> RAG Literature"
    )
    DEBUG: bool = Field(default=False, description="Debug mode")
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    LOG_LEVEL: str = "INFO"

    # CORS
    CORS_ORIGINS: List[str] = ["*"]
    CORS_METHODS: List[str] = ["*"]
    CORS_HEADERS: List[str] = ["*"]

    # Evidence Tier System - HARD CONSTRAINT
    EVIDENCE_TIERS: List[str] = [
        "DATABASE_DERIVED",
        "DOCKING_RESULT",
        "ML_PREDICTION",
        "XAI_INTERPRETATION",
        "LITERATURE_DERIVED"
    ]
    ENFORCE_EVIDENCE_TIER: bool = True
    BLOCK_CLINICAL_OVERCLAIM: bool = True

    # AYUSH-64 Justification (stored in config for global access)
    AYUSH64_CASE_STUDY: str = (
        "AYUSH-64 is a polyherbal formulation (Alstonia scholaris, Picrorhiza kurroa, "
        "Swertia chirayita, Caesalpinia crista) traditionally used for malaria and repurposed "
        "for COVID-19 via computational screening. Computational predictions of Mpro binding "
        "were treated as hypotheses for prioritization and validated through in-vitro, in-vivo, "
        "and clinical trials. This establishes the precedent that Tier 2-4 outputs "
        "(docking, ML, XAI) MUST NOT be presented as clinical proof."
    )

    # Database
    IMPPAT_DATA_PATH: Path = DB_ROOT / "imppat_sample.json"
    PHYTOCHEMICAL_DB_PATH: Path = DB_ROOT / "phytochemicals.json"
    PROTEIN_TARGETS_PATH: Path = DB_ROOT / "protein_targets.json"

    # Docking
    VINA_BINARY_PATH: Optional[str] = Field(default=None, description="Path to vina binary, if available")
    DOCKING_EXHAUSTIVENESS: int = 8
    DOCKING_NUM_POSES: int = 9
    DOCKING_FALLBACK_ENABLED: bool = True  # Use physics-inspired mock if Vina not present
    DOCKING_BOX_SIZE: float = 20.0  # Angstrom

    # ML
    ML_MODEL_PATH: Path = MODELS_ROOT / "affinity_predictor.pkl"
    ML_SCALER_PATH: Path = MODELS_ROOT / "feature_scaler.pkl"
    ML_FEATURES: List[str] = [
        "molecular_weight", "logp", "hbd", "hba", "tpsa", "rotatable_bonds",
        "aromatic_rings", "heavy_atoms", "formal_charge", "num_heteroatoms",
        "fingerprint_density", "fraction_csp3", "qed_score"
    ]
    ML_TRAIN_ON_STARTUP_IF_MISSING: bool = True

    # XAI
    SHAP_BACKGROUND_SAMPLES: int = 100
    SHAP_ENABLED: bool = True

    # RAG / Literature
    LITERATURE_CORPUS_PATH: Path = LITERATURE_ROOT / "corpus.json"
    FAISS_INDEX_PATH: Path = LITERATURE_ROOT / "faiss_index.bin"
    EMBEDDING_MODEL_NAME: str = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_FALLBACK_TFIDF: bool = True
    RAG_TOP_K: int = 5
    RAG_CHUNK_SIZE: int = 512
    RAG_CHUNK_OVERLAP: int = 50

    # Chem
    RDKIT_ENABLED: bool = True
    MAX_COMPOUNDS_PER_REQUEST: int = 100

    # Pipeline
    PIPELINE_TIMEOUT_SECONDS: int = 300
    ENABLE_LANGGRAPH_ORCHESTRATION: bool = True

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "allow"

    @validator("VINA_BINARY_PATH")
    def check_vina_path(cls, v):
        if v and not Path(v).exists():
            # Don't fail, just warn - fallback will be used
            print(f"[WARNING] Vina binary not found at {v}, using mock docking")
            return None
        # Auto-detect vina in common locations
        if v is None:
            for candidate in ["/usr/bin/vina", "/usr/local/bin/vina", "/opt/vina/bin/vina", "vina"]:
                if Path(candidate).exists():
                    return candidate
        return v

# Global settings instance
settings = Settings()

# Evidence Tier definitions for quick import (mirrored from evidence.py to avoid circular import)
EVIDENCE_TIER_DEFINITIONS = {
    1: {
        "name": "DATABASE_DERIVED",
        "description": "Curated phytochemical and traditional-medicine databases (IMPPAT primary)",
        "examples": ["IMPPAT entry", "PubChem properties", "ChEMBL bioactivity", "Ayurvedic text reference"],
        "confidence_ceiling": "High if curated, but requires provenance versioning",
        "mandatory_citations": True,
        "is_computational": False,
        "disclaimer": "Database-derived information. Verify source DB version and primary botanical literature."
    },
    2: {
        "name": "DOCKING_RESULT",
        "description": "Structure-based protein-ligand molecular docking (AutoDock Vina style)",
        "examples": ["Vina score", "pose", "RMSD", "binding pocket residues"],
        "confidence_ceiling": "Computational hypothesis - NOT clinical proof",
        "mandatory_citations": False,
        "is_computational": True,
        "disclaimer": "DISCLAIMER: Computational docking estimate (-kcal/mol). Requires experimental validation (SPR/ITC/cellular assay). NOT clinical proof."
    },
    3: {
        "name": "ML_PREDICTION",
        "description": "Supervised ML for binding-affinity prediction",
        "examples": ["pKd prediction", "RMSE", "applicability domain flag"],
        "confidence_ceiling": "Statistical inference - NOT causal or clinical",
        "mandatory_citations": False,
        "is_computational": True,
        "disclaimer": "DISCLAIMER: ML-predicted affinity is statistical inference limited by training domain. Requires wet-lab validation. NOT clinical proof."
    },
    4: {
        "name": "XAI_INTERPRETATION",
        "description": "Explainable AI (SHAP) interpretation of model predictions",
        "examples": ["SHAP values", "feature importance", "dependence plot"],
        "confidence_ceiling": "Explains model behavior, not biological ground truth",
        "mandatory_citations": False,
        "is_computational": True,
        "disclaimer": "DISCLAIMER: XAI interprets model, not biology. May reflect dataset bias. Requires domain expert validation. NOT clinical proof."
    },
    5: {
        "name": "LITERATURE_DERIVED",
        "description": "Scientific literature mining via RAG, coordinated by agentic layer and LLM-synthesized",
        "examples": ["RAG retrieved snippets", "PMID/DOI citations", "LLM summary with grounding"],
        "confidence_ceiling": "Subject to retrieval quality and LLM hallucination - verify DOI/PMID",
        "mandatory_citations": True,
        "is_computational": True,
        "disclaimer": "DISCLAIMER: Literature-mined / LLM-synthesized. Verify primary sources. Hallucination risk. NOT direct clinical recommendation unless source is clinical trial."
    }
}

# Clinical overclaim blocklist
CLINICAL_OVERCLAIM_PHRASES = [
    "clinically proven",
    "proven to cure",
    "proven to treat",
    "effective treatment for patients",
    "clinical efficacy demonstrated",
    "will cure",
    "guaranteed to work",
    "safe and effective in humans",
    "therapeutic effect confirmed",
    "can be used to treat patients",
    "clinical proof",
    "cures disease",
    "treats disease in humans",
    "approved drug based on this",
    "safe for human use based on this result",
    "efficacious in patients",
]

# Pipeline layer definitions (six functional layers)
PIPELINE_LAYERS = {
    "i": {"name": "Curated Databases", "primary": "IMPPAT", "tier": 1},
    "ii": {"name": "Cheminformatic Processing", "primary": "RDKit", "tier": 1},
    "iii": {"name": "Molecular Docking", "primary": "AutoDock Vina", "tier": 2},
    "iv": {"name": "ML Binding Affinity", "primary": "scikit-learn", "tier": 3},
    "v": {"name": "Explainable AI", "primary": "SHAP", "tier": 4},
    "vi": {"name": "Literature RAG", "primary": "sentence-transformers + FAISS + LangGraph", "tier": 5},
}
