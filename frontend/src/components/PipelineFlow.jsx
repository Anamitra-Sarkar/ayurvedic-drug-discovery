/**
 * PipelineFlow.jsx — plain-language "How it works" diagram.
 * Layer ids i..vi and tier ids unchanged internally.
 */
import { FRIENDLY_STEPS, CONFIDENCE_LEVELS } from '../utils/friendly.js';

export default function PipelineFlow({ activeLayer = null, onSelectLayer }) {
  return (
    <div className="card overflow-hidden">
      <div className="px-5 py-4 border-b border-forest-900/10 bg-gradient-to-r from-cream-100 to-forest-50 flex items-center justify-between dark:from-white/5 dark:to-transparent">
        <div>
          <div className="font-display font-bold text-[15px] text-forest-950 dark:text-cream-50">How it works — 6 gentle steps</div>
          <div className="text-[11px] text-forest-700/70 dark:text-cream-100/60 mt-0.5">From plant library to shortlist · every step keeps its own confidence level</div>
        </div>
        <div className="hidden md:flex items-center gap-2">
          <span className="text-[10px] px-2.5 py-1 rounded-full bg-gold-50 border border-gold-300/60 text-gold-700 dark:bg-gold-400/10 dark:text-gold-300">Research preview, not advice</span>
        </div>
      </div>

      <div className="px-5 py-4 bg-forest-50/60 border-b border-forest-900/10 dark:bg-white/5">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-2xl bg-forest-700 text-white flex items-center justify-center">🌿</div>
          <div className="flex-1">
            <div className="font-display font-semibold text-sm text-forest-950 dark:text-cream-50">Your guide through the steps</div>
            <div className="text-[11px] text-forest-700/70 dark:text-cream-100/60 mt-0.5">Library → chemical check → shape fit → strength guess → why it guessed → research check → shortlist</div>
          </div>
        </div>
      </div>

      <div className="p-5">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-3">
          {FRIENDLY_STEPS.map((step) => {
            const isActive = activeLayer === step.id;
            return (
              <button
                key={step.id}
                onClick={() => onSelectLayer?.(step.id)}
                className={`card-lift text-left rounded-3xl border-2 p-4 transition-all bg-white dark:bg-white/5 ${isActive ? 'ring-2 ring-forest-700 ring-offset-2 shadow-lift scale-[1.02] border-forest-700' : 'border-forest-900/10 hover:shadow-card-hover hover:scale-[1.01]'}`}
              >
                <div className="flex items-start justify-between">
                  <div className="w-9 h-9 rounded-2xl flex items-center justify-center text-lg bg-cream-100 border border-forest-900/10">{step.icon}</div>
                  <span className="text-[10px] px-1.5 py-0.5 rounded bg-cream-100 border border-forest-900/10 dark:bg-white/10">Step {step.id}</span>
                </div>
                <div className="mt-2.5 font-display font-semibold text-[13px] leading-tight text-forest-950 dark:text-cream-50">{step.name}</div>
                <div className="text-[11px] text-forest-700/75 dark:text-cream-100/65 mt-1 leading-snug">{step.text}</div>
              </button>
            );
          })}
        </div>

        <div className="mt-5 rounded-2xl bg-forest-900 text-cream-50 p-4 text-[11px] leading-relaxed dark:bg-white/5">
          <div className="font-semibold text-white tracking-wide mb-2">What happens, in order</div>
          <div className="grid md:grid-cols-2 gap-3 text-cream-100/85">
            <div className="space-y-1">
              <div><span className="text-gold-300">1.</span> We find your plant and compound in the library.</div>
              <div><span className="text-gold-300">2.</span> We measure basic chemical properties.</div>
              <div><span className="text-gold-300">3.</span> We test how snugly it fits the protein shape.</div>
            </div>
            <div className="space-y-1">
              <div><span className="text-gold-300">4.</span> The model predicts a strength score.</div>
              <div><span className="text-gold-300">5.</span> We show which patterns pushed the guess.</div>
              <div><span className="text-gold-300">6.</span> We compare with published papers, then shortlist.</div>
            </div>
          </div>
        </div>

        <div className="mt-4 flex flex-wrap gap-2">
          {Object.values(CONFIDENCE_LEVELS).map((t) => (
            <span key={t.id} className="chip text-[11px] bg-white border-forest-900/10 text-forest-800 dark:bg-white/5 dark:text-cream-100" style={{ borderColor: `${t.color}30` }}>
              <span>{t.icon}</span>{t.label}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}
