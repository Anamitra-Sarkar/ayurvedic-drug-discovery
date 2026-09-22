
/**
 * LiteraturePanel.jsx
 * RAG results with citations, faithfulness score, tier LITERATURE_DERIVED
 */
import EvidenceTierBadge from './EvidenceTierBadge.jsx';

export default function LiteraturePanel({ literature, loading, query }) {
  if (loading) {
    return <div className="rounded-2xl border border-green-100 bg-green-50/50 p-6 animate-pulse h-[320px]" />;
  }
  if (!literature) {
    return <div className="rounded-2xl border border-slate-200 bg-white p-6 text-center font-mono text-xs text-slate-500">No literature retrieved — try a query (e.g., Withaferin A Mpro).</div>;
  }

  const citations = literature.citations || [];
  const faith = literature.faithfulness || 0;

  const faithColor = faith > 0.8 ? 'bg-green-600' : faith > 0.6 ? 'bg-amber-500' : 'bg-red-500';

  return (
    <div className="rounded-2xl border border-green-200 bg-white shadow-card overflow-hidden">
      <div className="px-4 py-3 border-b border-green-100 bg-green-50/70 flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-green-700 text-white flex items-center justify-center">📚</div>
          <div>
            <div className="font-display font-semibold text-sm">Literature Mining — RAG + Synthesis</div>
            <div className="font-mono text-[11px] text-green-800">Query: "{literature.query || query}" • {literature.retrievedDocs} docs • faithfulness {(faith*100).toFixed(0)}%</div>
          </div>
        </div>
        <EvidenceTierBadge tier="LITERATURE_DERIVED" />
      </div>

      <div className="p-4">
        {/* Faithfulness bar */}
        <div className="flex items-center gap-3 rounded-xl bg-slate-50 border border-slate-200 p-3">
          <span className="font-mono text-[10px] tracking-widest text-slate-600">FAITHFULNESS</span>
          <div className="flex-1 h-2 bg-slate-200 rounded-full overflow-hidden">
            <div className={`h-full ${faithColor} transition-all`} style={{width: `${faith*100}%`}} />
          </div>
          <span className="font-mono text-xs font-semibold">{faith.toFixed(2)}</span>
          <span className="font-mono text-[10px] text-slate-500">RAG retrieval grounding</span>
        </div>

        {/* Synthesis */}
        <div className="mt-4 rounded-xl bg-white border border-slate-200 p-4">
          <div className="font-mono text-[10px] tracking-widest font-bold text-slate-700">LLM SYNTHESIS — LITERATURE_DERIVED TIER</div>
          <p className="mt-2 text-sm text-slate-800 leading-relaxed">{literature.synthesis}</p>
          <div className="mt-2 font-mono text-[10px] text-slate-500">LLM synthesised from retrieved chunks via sentence-transformers + FAISS (or TF-IDF fallback). Includes AYUSH-64 reference for justification pattern.</div>
        </div>

        {/* Citations */}
        <div className="mt-4">
          <div className="font-mono text-[11px] tracking-widest font-semibold text-slate-700 mb-2">CITATIONS ({citations.length}) — VERIFIED</div>
          <div className="space-y-2.5">
            {citations.map((c,i)=>(
              <div key={i} className="rounded-xl border border-slate-200 bg-slate-50/70 p-3 hover:bg-white transition">
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0 flex-1">
                    <div className="font-display font-medium text-sm text-slate-900 leading-tight">{c.title}</div>
                    <div className="font-mono text-[11px] text-slate-600 mt-1">{c.authors} • DOI: {c.doi}</div>
                    <div className="mt-2 text-xs text-slate-700 bg-white border border-slate-100 rounded-lg p-2 italic">"{c.excerpt}"</div>
                  </div>
                  <div className="flex flex-col items-end gap-1">
                    <span className="font-mono text-[10px] px-2 py-0.5 rounded-full bg-green-50 border border-green-200 text-green-700">{Math.round(c.relevance*100)}% rel</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="mt-4 rounded-xl bg-amber-50 border border-amber-200 p-3">
          <div className="font-mono text-[10px] tracking-widest font-bold text-amber-900">TIER LITERATURE_DERIVED — SUPPORTIVE, NOT CONCLUSIVE</div>
          <div className="text-[11px] text-amber-800 mt-1 leading-relaxed">
            RAG retrieves prior art; synthesis may contain LLM inference but is anchored to retrieved documents with faithfulness scoring. Like AYUSH-64 literature justification, it provides context for repurposing hypothesis, <span className="font-semibold">not new clinical evidence</span>. All claims require citation verification.
          </div>
        </div>
      </div>
    </div>
  );
}
