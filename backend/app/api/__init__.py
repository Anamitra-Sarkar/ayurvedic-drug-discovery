
from fastapi import APIRouter

# Import all routers
from .main import router as health_router

try:
    from .pipeline import router as pipeline_router
except ImportError:
    pipeline_router = None

try:
    from .database import router as database_router
except ImportError:
    database_router = None

try:
    from .docking import router as docking_router
except ImportError:
    docking_router = None

try:
    from .ml import router as ml_router
except ImportError:
    ml_router = None

try:
    from .literature import router as literature_router
except ImportError:
    literature_router = None

def include_all_routers(app):
    app.include_router(health_router, prefix="/api", tags=["Health"])
    if pipeline_router:
        app.include_router(pipeline_router, prefix="/api", tags=["Pipeline"])
    if database_router:
        app.include_router(database_router, prefix="/api", tags=["Database"])
    if docking_router:
        app.include_router(docking_router, prefix="/api", tags=["Docking"])
    if ml_router:
        app.include_router(ml_router, prefix="/api", tags=["ML & XAI"])
    if literature_router:
        app.include_router(literature_router, prefix="/api", tags=["Literature RAG"])
