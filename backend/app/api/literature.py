
from fastapi import APIRouter, Query
from typing import Optional

router = APIRouter()

@router.get("/literature/query")
async def query_literature(q: str = Query(..., description="Scientific question"), top_k: int = 5):
    """RAG literature mining - 0% hallucinated citations vs 40-60% non-RAG [27]"""
    try:
        from app.agents.literature_agent import LiteratureAgent
        agent = LiteratureAgent()
        # NOTE: this previously called agent.query(...), a method that does not
        # exist on LiteratureAgent - every call silently raised AttributeError
        # and fell into the except block below, which returned a HARDCODED
        # fake answer + fake citation IDs (REF_004/007/012) regardless of the
        # actual question asked. Found via live production testing (identical
        # byte-for-byte response to unrelated queries). Fixed to call the real,
        # working method used elsewhere in this codebase (orchestrator.py),
        # which does real retrieval + real citation-grounded generation
        # (real LLM via Groq if GROQ_API_KEY is set, honest mock otherwise).
        tiered = agent.answer_question(q, top_k=top_k)
        result = tiered.to_dict() if hasattr(tiered, "to_dict") else tiered
        return result
    except Exception as e:
        # Honest failure - never fabricate citations or an answer.
        return {
            "query": q,
            "error": str(e),
            "answer": None,
            "citations": [],
            "evidence_tier": "LITERATURE_DERIVED",
            "disclaimer": "Real literature retrieval failed for this query - no answer generated. This is not a fabricated result.",
        }

@router.get("/literature/rag-info")
async def rag_info():
    return {
        "retriever": "Sentence-BERT + FAISS + reranking, TF-IDF fallback",
        "generator": "Citation-grounded synthesis, 0% hallucinated citations [27]",
        "performance_target": "Hallucination 47.8%->12.3%, faithfulness 0.52->0.87, accuracy 0.54->0.89 [28]",
        "applicability": "Both molecule-generation and literature sides - RetMol, PromptDiff, BIOREADER precedent [30]",
        "corpus": "40 references covering 7 literature areas A-G",
        "evidence_tier": "LITERATURE_DERIVED"
    }

@router.get("/literature/references")
async def list_references():
    from pathlib import Path
    import json
    ref_path = Path(__file__).parent.parent / "data" / "literature_corpus" / "references.json"
    if ref_path.exists():
        return json.loads(ref_path.read_text())
    return {"count": 40, "note": "Full list in docs/REFERENCES.md", "evidence_tier": "LITERATURE_DERIVED"}
