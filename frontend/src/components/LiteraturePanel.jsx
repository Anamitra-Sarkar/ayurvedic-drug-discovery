/**
 * LiteraturePanel.jsx — plain-language "What does published research say?"
 * Citation popup uses the smooth Modal.
 */
import { useState } from 'react';
import { ConfidenceBadge, HowCalculated, Modal, ResearchNote } from './ui.jsx';
import MarkdownLite from '../utils/markdownLite.jsx';

export default function LiteraturePanel({ literature, loading, query }) {
  const [activePaper, setActivePaper] = useState(null);

  if (loading) {
    return <div className="rounded-3xl border border-forest-900/10 bg-white p-6 animate-pulse h-[320px] dark:bg-forest-900" />;
  }
  if (!literature) {
    return (
      <div className="card p-8 text-center">
        <div className="text-3xl">📖</div>
        <div className="text-sm font-medium text-forest-800 dark:text-cream-100 mt-2">No research roundup yet</div>
        <div className="text-xs text-forest-700/70 dark:text-cream-100/60 mt-1">Try a search like “Ashwagandha active compound”.</div>
      </div>
    );
  }

  const citations = literature.citations || [];
  const faith = literature.faithfulness || 0;
  const faithColor = faith > 0.8 ? 'bg-forest-600' : faith > 0.6 ? 'bg-gold-500' : 'bg-clay-500';

  return (
    <div className="card overflow-hidden">
      <div className="px-4 py-3 sm:px-5 sm:py-4 border-b border-forest-900/10 bg-forest-50/70 flex flex-wrap items-center justify-between gap-2 dark:bg-white/5">
        <div className="flex min-w-0 flex-1 items-center gap-2.5">
          <div className="w-9 h-9 shrink-0 rounded-2xl bg-forest-700 text-white flex items-center justify-center">📖</div>
          <div className="min-w-0">
            <div className="font-display font-semibold text-[15px] text-forest-950 dark:text-cream-50">
              What does published research say?
              <HowCalculated title="research roundup">
                We search a small shelf of published papers for related work and write a short summary. Every claim should trace back to a listed paper — the “grounding” bar shows how closely the summary sticks to its sources.
              </HowCalculated>
            </div>
            <div className="text-[11px] text-forest-700/75 dark:text-cream-100/60">
              About “{literature.query || query}” · {literature.retrievedDocs} papers checked · sticks to sources {Math.round(faith * 100)}%
            </div>
          </div>
        </div>
        <div className="shrink-0"><ConfidenceBadge tier="LITERATURE_DERIVED" size="sm" align="right" /></div>
      </div>

      <div className="p-5">
        <div className="flex items-center gap-3 rounded-2xl bg-cream-50 border border-forest-900/10 p-3 dark:bg-white/5">
          <span className="text-[10px] tracking-widest uppercase text-forest-700/70 dark:text-cream-100/60">Sticks to sources</span>
          <div className="flex-1 h-2 bg-cream-200 rounded-full overflow-hidden dark:bg-white/10">
            <div className={`h-full ${faithColor} transition-all duration-500`} style={{ width: `${faith * 100}%` }} />
          </div>
          <span className="text-xs font-semibold">{faith.toFixed(2)}</span>
        </div>

        <div className="mt-4 rounded-2xl bg-white border border-forest-900/10 p-4 dark:bg-transparent">
          <div className="text-[10px] tracking-widest uppercase font-bold text-forest-800 dark:text-cream-100">What the papers say (their words)</div>
          <MarkdownLite text={literature.synthesis} className="mt-2 text-forest-950/90 dark:text-cream-50/90" />
        </div>

        <div className="mt-4">
          <div className="text-[11px] tracking-wide font-semibold uppercase text-forest-800 dark:text-cream-100 mb-2">Source papers ({citations.length})</div>
          <div className="space-y-2.5">
            {citations.map((c, i) => (
              <button
                key={i}
                onClick={() => setActivePaper(c)}
                className="card-lift w-full text-left rounded-2xl border border-forest-900/10 bg-cream-50/70 p-3 hover:bg-white dark:bg-white/5 dark:hover:bg-white/10 transition"
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0 flex-1">
                    <div className="font-display font-medium text-sm text-forest-950 dark:text-cream-50 leading-tight">{c.title}</div>
                    <div className="text-[11px] text-forest-700/75 dark:text-cream-100/60 mt-1">{c.authors}</div>
                  </div>
                  <span className="text-[10px] px-2 py-0.5 rounded-full bg-forest-50 border border-forest-200 text-forest-700 shrink-0">
                    {Math.round(c.relevance * 100)}% match
                  </span>
                </div>
                <div className="mt-1 text-[11px] text-forest-700 underline decoration-gold-400 decoration-2 underline-offset-2">Tap for details →</div>
              </button>
            ))}
          </div>
        </div>

        <div className="mt-4">
          <ResearchNote text="This roundup repeats what others published — it is background reading, not a new finding and not health advice. Always check the original papers." />
        </div>
      </div>

      {activePaper && (
        <Modal onClose={() => setActivePaper(null)} title="Paper details" wide>
          <div className="font-display font-semibold text-forest-950 dark:text-cream-50">{activePaper.title}</div>
          <div className="text-xs text-forest-700/75 dark:text-cream-100/60 mt-1">{activePaper.authors}</div>
          {activePaper.doi && <div className="text-[11px] text-forest-700/60 dark:text-cream-100/50 mt-1">Reference: {activePaper.doi}</div>}
          {activePaper.excerpt && (
            <blockquote className="mt-3 rounded-2xl border border-forest-900/10 bg-cream-50 p-3 text-sm italic leading-relaxed dark:bg-white/5">
              “{activePaper.excerpt}”
            </blockquote>
          )}
          <p className="mt-3 text-xs text-forest-700/70 dark:text-cream-100/60">
            This is a short quoted passage for context. Please read the full paper before drawing any conclusions.
          </p>
        </Modal>
      )}
    </div>
  );
}
