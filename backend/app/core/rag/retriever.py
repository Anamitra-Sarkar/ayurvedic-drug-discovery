"""
Retriever Logic for Ayurvedic RAG
=================================
Implements dense retrieval with sentence-transformers (all-MiniLM-L6-v2) + FAISS,
with TF-IDF fallback for environments without those libs.

Includes reranking step via cross-encoder or heuristic scoring.

Evidence tier: LITERATURE_DERIVED
Must achieve 0% hallucination by grounding in corpus IDs.
"""

from typing import List, Dict, Any, Optional, Tuple
import logging
import os
import pickle
import re
from dataclasses import dataclass

import numpy as np

# Lazy imports - allow fallback if libs missing
try:
    from sentence_transformers import SentenceTransformer  # type: ignore
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

try:
    import faiss  # type: ignore
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False

try:
    from sklearn.feature_extraction.text import TfidfVectorizer  # type: ignore
    from sklearn.metrics.pairwise import cosine_similarity  # type: ignore
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

from .corpus import Document, AyurvedicCorpusLoader

logger = logging.getLogger(__name__)


@dataclass
class RetrievalResult:
    doc: Document
    score: float
    rank: int
    embedding_score: float
    rerank_score: float
    highlights: List[str]  # grounded snippets


class AyurvedicRetriever:
    """
    Hybrid retriever:
    - Primary: sentence-transformers + FAISS (all-MiniLM-L6-v2)
    - Fallback: TF-IDF + cosine similarity
    - Reranking: cross-encoder heuristic (keyword overlap + citation recency + category boost)
    """

    def __init__(
        self,
        corpus_loader: AyurvedicCorpusLoader,
        embedding_model_name: str = "all-MiniLM-L6-v2",
        faiss_index_dir: Optional[str] = None,
        use_faiss: bool = True
    ):
        self.corpus_loader = corpus_loader
        self.documents: List[Document] = []
        self.embedding_model_name = embedding_model_name
        self.faiss_index_dir = faiss_index_dir or os.path.join(os.path.dirname(__file__), "faiss_index")
        os.makedirs(self.faiss_index_dir, exist_ok=True)

        self.embedding_model = None
        self.faiss_index = None
        self.tfidf_vectorizer = None
        self.tfidf_matrix = None
        self.doc_embeddings: Optional[np.ndarray] = None

        self.use_dense = SENTENCE_TRANSFORMERS_AVAILABLE and use_faiss and FAISS_AVAILABLE
        logger.info(f"Dense retrieval available: {self.use_dense} (ST={SENTENCE_TRANSFORMERS_AVAILABLE}, FAISS={FAISS_AVAILABLE})")

    def _load_embedding_model(self):
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            logger.warning("sentence-transformers not available, cannot load embedding model")
            return None
        try:
            model = SentenceTransformer(self.embedding_model_name)
            logger.info(f"Loaded embedding model {self.embedding_model_name}")
            return model
        except Exception as e:
            logger.warning(f"Failed to load SentenceTransformer {self.embedding_model_name}: {e}, fallback to TF-IDF")
            self.use_dense = False
            return None

    def ingest_corpus(self, documents: Optional[List[Document]] = None, rebuild: bool = False):
        """
        Ingest corpus and build indices.
        Public API required by LiteratureAgent.
        """
        if documents is not None:
            self.documents = documents
        else:
            self.documents = self.corpus_loader.load_corpus()

        logger.info(f"Ingesting {len(self.documents)} documents")

        # Try to load existing FAISS index if not rebuild
        index_path = os.path.join(self.faiss_index_dir, "faiss.index")
        meta_path = os.path.join(self.faiss_index_dir, "metadata.pkl")

        if not rebuild and os.path.exists(index_path) and os.path.exists(meta_path) and self.use_dense:
            try:
                self.faiss_index = faiss.read_index(index_path)
                with open(meta_path, 'rb') as f:
                    meta = pickle.load(f)
                    self.documents = meta['documents']
                    self.doc_embeddings = meta.get('embeddings')
                logger.info(f"Loaded existing FAISS index from {index_path}")
                if self.embedding_model is None:
                    self.embedding_model = self._load_embedding_model()
                return
            except Exception as e:
                logger.warning(f"Failed to load existing FAISS index: {e}, rebuilding")

        # Build new embeddings
        texts = [d.to_text_for_embedding() for d in self.documents]

        if self.use_dense:
            if self.embedding_model is None:
                self.embedding_model = self._load_embedding_model()

            if self.embedding_model is not None:
                try:
                    logger.info("Generating dense embeddings...")
                    embeddings = self.embedding_model.encode(
                        texts,
                        show_progress_bar=True,
                        convert_to_numpy=True,
                        normalize_embeddings=True
                    )
                    self.doc_embeddings = embeddings.astype(np.float32)

                    # Build FAISS index (Inner Product for normalized vectors = cosine similarity)
                    dim = self.doc_embeddings.shape[1]
                    self.faiss_index = faiss.IndexFlatIP(dim)
                    self.faiss_index.add(self.doc_embeddings)
                    logger.info(f"Built FAISS index: dim={dim}, n={self.faiss_index.ntotal}")

                    # Save
                    faiss.write_index(self.faiss_index, index_path)
                    with open(meta_path, 'wb') as f:
                        pickle.dump({'documents': self.documents, 'embeddings': self.doc_embeddings}, f)
                    logger.info(f"Saved FAISS index to {index_path}")

                except Exception as e:
                    logger.error(f"Dense embedding failed: {e}, falling back to TF-IDF")
                    self.use_dense = False

        # Always build TF-IDF as fallback (and for hybrid scoring)
        if SKLEARN_AVAILABLE:
            try:
                logger.info("Building TF-IDF index as fallback/hybrid...")
                self.tfidf_vectorizer = TfidfVectorizer(
                    max_features=10000,
                    stop_words='english',
                    ngram_range=(1, 2),
                    min_df=1,
                    max_df=0.9
                )
                self.tfidf_matrix = self.tfidf_vectorizer.fit_transform(texts)
                logger.info(f"Built TF-IDF matrix shape {self.tfidf_matrix.shape}")
            except Exception as e:
                logger.error(f"TF-IDF build failed: {e}")
                self.tfidf_vectorizer = None
        else:
            logger.warning("sklearn not available, no TF-IDF fallback")

    def _dense_retrieve(self, query: str, top_k: int = 20) -> List[Tuple[int, float]]:
        """Retrieve via FAISS."""
        if self.faiss_index is None or self.embedding_model is None or self.doc_embeddings is None:
            return []

        try:
            q_emb = self.embedding_model.encode([query], convert_to_numpy=True, normalize_embeddings=True).astype(np.float32)
            scores, indices = self.faiss_index.search(q_emb, top_k)
            results = [(int(idx), float(score)) for idx, score in zip(indices[0], scores[0]) if idx != -1]
            return results
        except Exception as e:
            logger.error(f"Dense retrieve failed: {e}")
            return []

    def _tfidf_retrieve(self, query: str, top_k: int = 20) -> List[Tuple[int, float]]:
        """Retrieve via TF-IDF."""
        if self.tfidf_vectorizer is None or self.tfidf_matrix is None:
            return []
        try:
            q_vec = self.tfidf_vectorizer.transform([query])
            sims = cosine_similarity(q_vec, self.tfidf_matrix).flatten()
            top_indices = np.argsort(sims)[::-1][:top_k]
            return [(int(i), float(sims[i])) for i in top_indices if sims[i] > 0]
        except Exception as e:
            logger.error(f"TF-IDF retrieve failed: {e}")
            return []

    def _extract_highlights(self, doc: Document, query: str, max_snippets: int = 2) -> List[str]:
        """Extract grounded snippets containing query keywords."""
        keywords = re.findall(r'\w+', query.lower())
        keywords = [k for k in keywords if len(k) > 3]

        text = doc.full_text + " " + doc.abstract
        sentences = re.split(r'(?<=[.!?])\s+', text)

        scored_sentences = []
        for sent in sentences:
            sent_lower = sent.lower()
            overlap = sum(1 for kw in keywords if kw in sent_lower)
            if overlap > 0:
                scored_sentences.append((overlap, sent.strip()))

        scored_sentences.sort(key=lambda x: x[0], reverse=True)
        highlights = [s for _, s in scored_sentences[:max_snippets]]
        if not highlights and doc.abstract:
            highlights = [doc.abstract[:300]]
        return highlights

    def _rerank(
        self,
        query: str,
        candidates: List[Tuple[int, float]],
        method: str = "heuristic"
    ) -> List[RetrievalResult]:
        """
        Reranking step - crucial for relevance.
        Heuristic cross-encoder style reranking:
        - embedding score * 0.6
        - keyword overlap * 0.2
        - recency boost * 0.1
        - category relevance boost * 0.1
        """
        query_lower = query.lower()
        query_keywords = set(re.findall(r'\w+', query_lower))
        query_keywords = {k for k in query_keywords if len(k) > 2}

        # Category boost based on query intent detection
        category_boost_map = {
            "ayush": ["ayush64", "ayurveda_pharmacology"],
            "withaferin": ["docking", "ayush64", "database"],
            "imppat": ["database"],
            "docking": ["docking"],
            "binding affinity": ["ml", "docking"],
            "shap": ["xai"],
            "explainable": ["xai"],
            "rdkit": ["cheminformatics"],
            "covid": ["ayush64", "docking"],
            "mpro": ["docking", "ml"],
            "toxicity": ["ayurveda_pharmacology"],
            "rag": ["rag_methods", "agentic_ai"],
            "hallucination": ["rag_methods"],
            "agentic": ["agentic_ai", "rag_methods"]
        }

        boosted_categories = set()
        for key, cats in category_boost_map.items():
            if key in query_lower:
                boosted_categories.update(cats)
        # default: if no match, slight boost to ayurveda_pharmacology + database
        if not boosted_categories:
            boosted_categories.update(["database", "ayurveda_pharmacology"])

        reranked: List[RetrievalResult] = []

        for rank_idx, (doc_idx, emb_score) in enumerate(candidates):
            doc = self.documents[doc_idx]

            # Keyword overlap score
            doc_text = (doc.title + " " + doc.abstract + " " + " ".join(doc.keywords)).lower()
            doc_keywords = set(re.findall(r'\w+', doc_text))
            overlap = len(query_keywords & doc_keywords) / max(len(query_keywords), 1)
            keyword_score = overlap  # 0-1

            # Recency boost: recent papers (2020+ ) slight boost for COVID/ML
            recency_score = 0.0
            if doc.year >= 2020:
                recency_score = min(0.2, (doc.year - 2019) * 0.05)  # 0.05 per year after 2019, cap 0.2

            # Category boost
            category_score = 0.15 if doc.category in boosted_categories else 0.0

            # Combined rerank score
            # embedding already normalized approx 0-1, TF-IDF 0-1
            rerank_score = (emb_score * 0.6) + (keyword_score * 0.2) + (recency_score) + (category_score)

            highlights = self._extract_highlights(doc, query)

            rr = RetrievalResult(
                doc=doc,
                score=rerank_score,
                rank=0,  # set after sorting
                embedding_score=emb_score,
                rerank_score=rerank_score,
                highlights=highlights
            )
            reranked.append(rr)

        # Sort by rerank_score descending
        reranked.sort(key=lambda x: x.rerank_score, reverse=True)
        for i, r in enumerate(reranked):
            r.rank = i + 1

        return reranked

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        rerank_top_k: int = 20
    ) -> List[RetrievalResult]:
        """
        Main retrieval API: dense or TF-IDF -> rerank -> top_k
        Returns grounded RetrievalResults with doc_id mapping to prevent hallucination.
        """
        if not self.documents:
            logger.warning("No documents ingested, loading corpus now")
            self.ingest_corpus()

        logger.info(f"Retrieving for query: '{query}' top_k={top_k} rerank_top_k={rerank_top_k}")

        # Step 1: Candidate retrieval (more candidates for reranking)
        if self.use_dense and self.faiss_index is not None:
            candidates = self._dense_retrieve(query, top_k=rerank_top_k)
            if len(candidates) < rerank_top_k // 2:
                # Hybrid fallback: add TF-IDF candidates
                tfidf_cands = self._tfidf_retrieve(query, top_k=rerank_top_k)
                # Merge dedup
                seen = {idx for idx, _ in candidates}
                for idx, score in tfidf_cands:
                    if idx not in seen:
                        candidates.append((idx, score * 0.8))  # downweight TF-IDF slightly
                        seen.add(idx)
        else:
            candidates = self._tfidf_retrieve(query, top_k=rerank_top_k)
            if not candidates:
                # Emergency fallback: keyword match on abstract
                logger.warning("No candidates from TF-IDF, using keyword emergency fallback")
                query_lower = query.lower()
                scored = []
                for i, doc in enumerate(self.documents):
                    text = (doc.title + doc.abstract).lower()
                    score = sum(1 for kw in query_lower.split() if kw in text) / max(len(query_lower.split()), 1)
                    if score > 0:
                        scored.append((i, score))
                scored.sort(key=lambda x: x[1], reverse=True)
                candidates = scored[:rerank_top_k]

        if not candidates:
            logger.warning(f"No candidates retrieved for query: {query}")
            return []

        # Step 2: Reranking
        reranked = self._rerank(query, candidates)

        # Step 3: Return top_k
        final = reranked[:top_k]
        logger.info(f"Retrieved {len(final)} results after reranking (from {len(candidates)} candidates)")
        for r in final:
            logger.debug(f"  Rank {r.rank}: {r.doc.doc_id} score={r.score:.3f} title={r.doc.title[:60]}")
        return final

    def retrieve_batch(
        self,
        queries: List[str],
        top_k: int = 5
    ) -> Dict[str, List[RetrievalResult]]:
        """Batch retrieval for multiple queries."""
        results = {}
        for q in queries:
            results[q] = self.retrieve(q, top_k=top_k)
        return results
