/**
 * Documentation.jsx — "/docs" and "/about": plain-language guide.
 * "How should I read results?" — honest, jargon-free.
 */
import { Link } from 'react-router-dom';
import PipelineFlow from '../components/PipelineFlow.jsx';
import { Page, ResearchNote } from '../components/ui.jsx';
import { CONFIDENCE_LEVELS } from '../utils/friendly.js';

export default function Documentation() {
  return (
    <Page className="space-y-6 max-w-[1100px]">
      <div className="card p-6 md:p-8">
        <span className="inline-flex items-center gap-2 rounded-full bg-forest-50 border border-forest-200 px-3 py-1 text-[11px] font-medium text-forest-700">📖 A friendly guide</span>
        <h1 className="font-display font-semibold text-3xl mt-3 text-forest-950 dark:text-cream-50">How should I read these results?</h1>
        <p className="text-[15px] text-forest-900/80 dark:text-cream-100/75 mt-3 leading-relaxed max-w-3xl">
          Everything on this site is an <strong>early computer guess for research</strong>. Think of it like a
          weather forecast for molecules: useful for deciding what to study next, never a promise about real life.
          Every result carries a <strong>confidence level</strong> telling you what kind of clue it is — and every page
          reminds you that lab testing is still needed.
        </p>
      </div>

      <div>
        <h2 className="font-display text-xl font-semibold text-forest-950 dark:text-cream-50">The five confidence levels</h2>
        <p className="text-sm text-forest-800/75 dark:text-cream-100/65 mt-1">Each result is judged on its own — we never blend them into one “health score”.</p>
        <div className="grid md:grid-cols-2 gap-4 mt-4">
          {Object.values(CONFIDENCE_LEVELS).map((t) => (
            <div key={t.id} className="card p-5">
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-2xl text-lg" style={{ background: `${t.color}15` }}>{t.icon}</div>
                <h3 className="font-display font-semibold text-[15px] text-forest-950 dark:text-cream-50">{t.label}</h3>
              </div>
              <p className="mt-3 text-sm leading-relaxed text-forest-900/80 dark:text-cream-100/75">{t.blurb}</p>
              <div className="mt-3 rounded-2xl bg-cream-50 border border-forest-900/10 p-3 dark:bg-white/5">
                <div className="text-[10px] tracking-widest uppercase font-bold text-forest-700 dark:text-cream-100/70">How it’s worked out</div>
                <div className="text-[12px] text-forest-900/80 dark:text-cream-100/75 mt-1 leading-relaxed">{t.howCalculated}</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      <PipelineFlow />

      <div className="card p-6">
        <h2 className="font-display text-xl font-semibold text-forest-950 dark:text-cream-50">🌿 A note on Triphala</h2>
        <p className="mt-2 text-sm leading-relaxed text-forest-900/80 dark:text-cream-100/75">
          Triphala blends three fruits — Amla, Bibhitaki and Haritaki — with about 174 natural compounds between them
          in our library. Our map shows how those compounds spread across the plants and which protein shapes they were
          compared with. A rich, busy map is interesting — it is still only a starting point for researchers.
        </p>
      </div>

      <ResearchNote text="Results are computer predictions for research purposes only — not health or medical advice. Nothing here is proven to work or to be safe. Please speak to a qualified professional about any health decision." />

      <div className="flex flex-wrap gap-2">
        <Link to="/compounds" className="btn-primary !text-sm">Explore compounds →</Link>
        <Link to="/pipeline" className="btn-secondary !text-sm">Run an analysis</Link>
      </div>
    </Page>
  );
}
