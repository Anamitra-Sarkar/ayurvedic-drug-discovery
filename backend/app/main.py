
"""
FastAPI Main Application
AI-Driven Computational Pipeline for Ayurvedic Drug Discovery
Bhumika Tewari - RCCIIT Winter Project 2026
Six functional layers + Agentic orchestration + 5-tier evidence enforcement
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Ayurvedic Drug Discovery Pipeline",
    description="""
    ## AI-Driven Computational Pipeline for Ayurvedic Drug Discovery
    
    ### Six Functional Layers:
    1. **Phytochemical Databases** (IMPPAT primary, 1,742 plants, 9,596 compounds)
    2. **Cheminformatics** (RDKit descriptors, drug-likeness)
    3. **Molecular Docking** (AutoDock Vina + PLIP interaction analysis)
    4. **ML Binding Affinity** (RF, ExtraTrees, XGB, NuSVR ensemble - BACE1 fusion style)
    5. **Explainable AI** (SHAP + multi-explainer triangulation)
    6. **Literature RAG** (Sentence-BERT + FAISS, 0% hallucinated citations)
    
    ### Orchestrated by:
    - **LangGraph-style multi-agent system** with Validation Agent (error-propagation prevention)
    - **Report Agent** with safety guardrail pattern (Tippy)
    
    ### Hard Constraint - Five Evidentiary Tiers:
    Every output MUST be traceable to one of:
    - `DATABASE_DERIVED` - IMPPAT, PubChem curated data
    - `DOCKING_RESULT` - Vina empirical scoring
    - `ML_PREDICTION` - Supervised affinity prediction
    - `XAI_INTERPRETATION` - SHAP explanations
    - `LITERATURE_DERIVED` - RAG citation-grounded synthesis
    
    **MUST NOT present computational prediction as clinical proof** - AYUSH-64 case study justification [3]
    Computational hypothesis -> RCT as separate subsequent step, not collapsed claim.
    """,
    version="1.0.0",
    contact={
        "name": "Bhumika Tewari - RCCIIT",
        "url": "https://github.com/ayurvedic-drug-discovery",
    },
    license_info={"name": "MIT"},
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers from all API modules
try:
    from app.api.main import router as health_router
    app.include_router(health_router, prefix="/api", tags=["Health"])
    logger.info("Health router included")
except Exception as e:
    logger.warning(f"Health router not included: {e}")

try:
    from app.api.pipeline import router as pipeline_router
    app.include_router(pipeline_router, prefix="/api", tags=["Pipeline"])
    logger.info("Pipeline router included")
except Exception as e:
    logger.warning(f"Pipeline router not included: {e}")

try:
    from app.api.database import router as database_router
    app.include_router(database_router, prefix="/api", tags=["Database"])
    logger.info("Database router included")
except Exception as e:
    logger.warning(f"Database router not included: {e}")

try:
    from app.api.docking import router as docking_router
    app.include_router(docking_router, prefix="/api", tags=["Docking"])
    logger.info("Docking router included")
except Exception as e:
    logger.warning(f"Docking router not included: {e}")

try:
    from app.api.ml import router as ml_router
    app.include_router(ml_router, prefix="/api", tags=["ML & XAI"])
    logger.info("ML router included")
except Exception as e:
    logger.warning(f"ML router not included: {e}")

try:
    from app.api.literature import router as literature_router
    app.include_router(literature_router, prefix="/api", tags=["Literature RAG"])
    logger.info("Literature router included")
except Exception as e:
    logger.warning(f"Literature router not included: {e}")

# Try to initialize agents globally
try:
    from app.agents.database_agent import DatabaseAgent
    from app.agents.cheminformatics_agent import CheminformaticsAgent
    from app.agents.docking_agent import DockingAgent
    from app.agents.ml_agent import MLAgent
    from app.agents.xai_agent import XAIAgent
    from app.agents.literature_agent import LiteratureAgent
    from app.agents.orchestrator import AyurvedicOrchestrator
    
    db_agent = DatabaseAgent()
    chem_agent = CheminformaticsAgent()
    docking_agent = DockingAgent()
    ml_agent = MLAgent()
    xai_agent = XAIAgent()
    lit_agent = LiteratureAgent()
    
    logger.info("All agents initialized successfully")
except Exception as e:
    logger.warning(f"Agent initialization warning (expected if dependencies missing): {e}")
    db_agent = None

@app.get("/")
async def root():
    return {
        "message": "Ayurvedic Drug Discovery Pipeline - Computational Prioritization Only",
        "version": "1.0.0",
        "project": "AI-Driven Computational Pipeline for Ayurvedic Drug Discovery",
        "author": "Bhumika Tewari - RCCIIT MAKAUT Winter 2026",
        "six_layers": [
            "1. Phytochemical & Traditional-Medicine Databases (IMPPAT)",
            "2. Cheminformatic Molecular-Structure Processing (RDKit)",
            "3. Structure-Based Protein-Ligand Docking (Vina + PLIP)",
            "4. Supervised ML for Binding-Affinity Prediction (Ensemble)",
            "5. Explainable AI (SHAP + triangulation)",
            "6. Literature Mining via RAG + Agentic Orchestration"
        ],
        "five_evidentiary_tiers": [
            "DATABASE_DERIVED",
            "DOCKING_RESULT", 
            "ML_PREDICTION",
            "XAI_INTERPRETATION",
            "LITERATURE_DERIVED"
        ],
        "hard_constraint": "MUST NOT present computational prediction as clinical proof - AYUSH-64 [3] shows computational -> RCT as separate step",
        "endpoints": {
            "health": "/api/health",
            "pipeline": "/api/pipeline/run",
            "database_search": "/api/database/search",
            "docking": "/api/docking/run",
            "ml_predict": "/api/ml/predict",
            "literature": "/api/literature/query",
            "docs": "/docs",
            "frontend": "http://localhost:5173"
        },
        "warning": "⚠️ COMPUTATIONAL ONLY - No clinical efficacy claim - All outputs labeled by evidentiary tier",
        "ayush64_note": "AYUSH-64 repurposed via NP+docking, then evaluated in open-label RCT as adjunct to standard care - rare documented example of computational hypothesis carried to clinical tier as separate subsequent step"
    }

@app.get("/api/pipeline/info")
async def pipeline_info():
    return {
        "flow_diagram": "DatabaseAgent -> CheminformaticsAgent -> DockingAgent -> InteractionAnalysisAgent -> MLAgent -> XAIAgent -> LiteratureAgent -> ValidationAgent -> ReportAgent",
        "orchestration": "LangGraph StateGraph with checkpointing, parallel execution, error-propagation prevention via separate ValidationAgent (Ref [32])",
        "evidence_enforcement": "Central EvidenceValidator checks every output has tier, blocks clinical overclaim patterns",
        "literature_grounding": {
            "triphala": "174 bioactives, 44 targets, 78 diseases - denser combined than single herb [4]",
            "epilepsy_herbs": "63 herbs, 349 phytochemicals, 11 novel neuromodulators [5]",
            "imppat": "1,742 plants, 9,596 phytochemicals, 27,074 associations [7]",
            "tcm_comparison": "7,288 publications 2007-2025 showing shift to NP-AI-multi-omics [6]",
            "vina_speed": "Up to 100x faster than AutoDock4 [12]",
            "hybrid_scoring": "Significant improvement in pKi correlation [14]",
            "plip": "7-8 interaction types without manual prep [15]",
            "tlr4_ml": "Leakage-aware diversity-preserving split for n=49 [16]",
            "factor_xa": "42-algorithm benchmark, ExtraTrees R2=0.760, XGB ROC-AUC=0.962 [19]",
            "bace1_fusion": "R2 0.78 combined vs 0.65/0.64 alone [20]",
            "xai_survey": "Bias-aware splits, multi-explainer triangulation [24]",
            "rag_pharma": "RAG 0% hallucinated citations vs 40-60% non-RAG [27]",
            "rag_hallucination": "47.8%->12.3%, faithfulness 0.52->0.87, accuracy 0.54->0.89 [28]",
            "agentic_pharma": "MAS pattern, error-propagation risk flagged [32]",
            "agentd": "Modular LLM framework [35] closest analogue to LangGraph agent layer",
            "tippy": "First production-ready agentic DMTA, 5-agent + Safety Guardrail [36] template for Report Agent"
        }
    }

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Global exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": str(exc),
            "evidence_tier": "SYSTEM_ERROR",
            "disclaimer": "System error - not a scientific result",
            "must_not": "Do not interpret error as clinical or experimental evidence"
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
