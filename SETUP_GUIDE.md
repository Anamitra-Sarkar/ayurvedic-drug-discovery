# Setup Guide - Ayurvedic Drug Discovery Pipeline

## Prerequisites

- Python 3.9+
- Node.js 18+
- (Optional) AutoDock Vina binary for real docking, else mock physics-inspired scoring used
- (Optional) RDKit for cheminformatics, else hash fallback
- Git

## Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Requirements include:
# fastapi, uvicorn, pydantic, pydantic-settings, python-multipart
# rdkit-pypi (optional, fallback exists)
# scikit-learn, xgboost (optional, fallback HistGradientBoosting), shap (optional), lime (optional)
# numpy, pandas, scipy
# sentence-transformers (optional, fallback TF-IDF), faiss-cpu (optional)
# langgraph, langchain (optional, custom StateGraph implemented)
# biopython (optional for PDB parsing)
# 3dmol via frontend, plotly

# If Vina not installed, system uses mock scoring (physics-inspired, -4 to -12 kcal/mol realistic)
# To install Vina:
# conda install -c conda-forge autodock-vina
# or download from https://vina.scripps.edu/

# Run backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
# Docs at http://localhost:8000/docs
# Root info at http://localhost:8000/
# Pipeline info at http://localhost:8000/api/pipeline/info
```

### Backend Data:

- `app/data/imppat_sample.json` - 100 phytochemicals covering Triphala, AYUSH-64, 63 anti-epileptic herbs - realistic ADMET
- `app/data/proteins/targets.json` - 10 targets: mGluR2 7E9G, mGluR3 5CNK, TLR4 3FXI, Factor Xa 2BOH, BACE1 2WJO, SARS-CoV-2 Mpro 6LU7 AYUSH-64 [3], GABRA1, SCN1A, GRIN2B etc
- `app/data/literature_corpus/references.json` - 40 refs covering 7 areas A-G
- `app/data/literature_corpus/papers/` - 5 sample papers
- `app/data/ml/training_data.csv` - 500 synthetic PDBBind-like
- `app/models/ml_rescorer.pkl` - DockingApp RF style rescorer

### Frontend Setup

```bash
cd frontend
npm install
# Dependencies: react, react-dom, vite, axios, 3dmol, plotly.js-dist, tailwind, react-router-dom

npm run dev
# -> http://localhost:5173
# Vite proxy /api -> http://localhost:8000

# Build for production
npm run build
# dist/ -> serve via nginx or static files
```

### Full Pipeline Example

```bash
cd backend
python -m app.agents.orchestrator --plant "Withania somnifera" --target 7E9G --top_n 10

# Or via API
curl -X POST http://localhost:8000/api/pipeline/run \
  -H "Content-Type: application/json" \
  -d '{
    "plant_names": ["Withania somnifera", "Bacopa monnieri"],
    "protein_target": "7E9G",
    "top_n": 10,
    "include_xai": true,
    "include_literature": true
  }'

# Or use example script
python examples/sample_run.py --plant "Withania somnifera" --target 7E9G --top_n 10
# Outputs examples/sample_output.json with all 5 tiers labeled
```

### Docker Setup

```bash
# Backend Dockerfile provided
cd backend
docker build -t ayurvedic-backend .
docker run -p 8000:8000 ayurvedic-backend

# Frontend
cd frontend
docker build -t ayurvedic-frontend .
docker run -p 5173:5173 ayurvedic-frontend

# Or docker-compose (create if needed)
docker-compose up --build
```

### Testing

```bash
cd backend
pytest tests/ -v
# test_evidence.py checks 5-tier enforcement, no clinical overclaim
# test_pipeline.py runs mock pipeline
```

### Environment Variables (Optional)

Create `.env` in backend/:

```
DEBUG=False
HOST=0.0.0.0
PORT=8000
OPENAI_API_KEY=  # optional, else mock LLM
HUGGINGFACE_TOKEN=  # optional for sentence-transformers
VINA_BINARY_PATH=/usr/local/bin/vina
```

No API keys required for mock mode - all agents have fallback.

### Troubleshooting

- **RDKit missing:** CheminformaticsAgent uses hash fallback, still returns descriptors, logs warning
- **Vina missing:** DockingAgent uses physics-inspired mock scoring -4 to -12 kcal/mol, logs mock_used True, still returns tier DOCKING_RESULT with disclaimer moderate correlation [14]
- **sentence-transformers missing:** LiteratureAgent uses TF-IDF fallback, still returns citation-grounded but faithfulness lower, logs fallback
- **FAISS missing:** Falls back to numpy brute-force
- **SHAP missing:** XAIAgent uses feature importance fallback

All fallbacks preserve evidence tier enforcement.

### Performance Notes

- Triphala network: 174 bioactives [4] - NetworkGraph component handles 100 nodes demo
- 63 herbs 349 phytochemicals 11 candidates [5] - batch docking 349 in ~2 min mock, ~30 min real Vina
- Vina 100x faster than AutoDock4 [12]
- RAG 0% hallucinated vs 40-60% non-RAG [27] - retriever top_k 5
- BACE1 fusion R2 0.78 [20] - feature engineering fuses docking + QSAR

