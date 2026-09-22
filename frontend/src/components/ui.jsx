/**
 * ui.jsx — shared polished primitives: cards, spinner, skeleton,
 * modal popup (scale+fade), and "How is this calculated?" info popup.
 * All copy here is plain-language, consumer-friendly.
 */
import { useEffect, useState } from 'react';
import { CONFIDENCE_LEVELS, confidenceLevel } from '../utils/friendly.js';

export function LoadingSpinner({ label = 'Loading…', dark = false }) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 py-10" role="status" aria-live="polite">
      <span className={`spinner ${dark ? '' : 'spinner-dark'}`} style={{ width: 28, height: 28 }} />
      <span className="text-sm text-forest-700 dark:text-cream-100">{label}</span>
    </div>
  );
}

export function Skeleton({ className = '' }) {
  return <div className={`skeleton ${className}`} aria-hidden="true" />;
}

export function SkeletonCard() {
  return (
    <div className="card p-5 space-y-3" aria-hidden="true">
      <Skeleton className="h-5 w-2/3" />
      <Skeleton className="h-24 w-full" />
      <div className="grid grid-cols-4 gap-2">
        <Skeleton className="h-12" /><Skeleton className="h-12" /><Skeleton className="h-12" /><Skeleton className="h-12" />
      </div>
    </div>
  );
}

export function EmptyState({ icon = '🌱', title = 'Nothing here yet', hint = 'Try a different search, or come back later.', action = null }) {
  return (
    <div className="card p-10 text-center page-wrap">
      <div className="text-4xl">{icon}</div>
      <h3 className="font-display text-xl font-semibold text-forest-900 dark:text-cream-50 mt-3">{title}</h3>
      <p className="text-sm text-forest-700/80 dark:text-cream-100/70 mt-2 max-w-md mx-auto leading-relaxed">{hint}</p>
      {action && <div className="mt-5">{action}</div>}
    </div>
  );
}

/** Confidence badge — plain-language face over the internal tier id (prop API unchanged). */
export function ConfidenceBadge({ tier, size = 'md', showTooltip = true, showLabel = true, className = '' }) {
  const [hover, setHover] = useState(false);
  const meta = confidenceLevel(tier);
  if (!meta) {
    return <span className={`chip bg-slate-100 text-slate-600 ${className}`}>Not rated yet</span>;
  }
  const sizes = {
    sm: 'px-2 py-0.5 text-[11px]',
    md: 'px-2.5 py-1 text-xs',
    lg: 'px-3 py-1.5 text-sm',
  };
  return (
    <div className="relative inline-block" onMouseEnter={() => setHover(true)} onMouseLeave={() => setHover(false)}>
      <span
        className={`chip font-medium ${sizes[size]} ${className} bg-white dark:bg-white/5 border-forest-600/15 text-forest-800 dark:text-cream-50 transition-all cursor-help hover:shadow-card-hover`}
        style={{ borderColor: `${meta.color}33` }}
      >
        <span className="leading-none">{meta.icon}</span>
        {showLabel && <span>{size === 'sm' ? meta.short : meta.label}</span>}
        <span className="h-1.5 w-1.5 rounded-full" style={{ background: meta.color }} />
      </span>
      {showTooltip && hover && (
        <div className="modal-panel absolute left-0 top-full z-50 mt-2 w-[min(320px,calc(100vw-3rem))] max-w-[calc(100vw-3rem)] rounded-2xl border border-forest-900/10 bg-white p-4 text-left shadow-lift dark:bg-forest-900 dark:border-white/10">
          <div className="flex items-center gap-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl text-lg" style={{ background: `${meta.color}15` }}>{meta.icon}</div>
            <div>
              <div className="font-display text-sm font-semibold text-forest-950 dark:text-cream-50">{meta.label}</div>
              <div className="text-[11px] text-forest-700/70 dark:text-cream-100/60">Confidence level · computer prediction</div>
            </div>
          </div>
          <p className="mt-2 text-xs leading-relaxed text-forest-900/80 dark:text-cream-100/80">{meta.blurb}</p>
          <div className="mt-2 rounded-xl bg-cream-100 p-2.5 text-[11px] leading-relaxed text-forest-800 dark:bg-white/5 dark:text-cream-100/80">
            {meta.howCalculated}
          </div>
          <div className="mt-2 border-t border-forest-900/10 pt-2 text-[10px] font-semibold tracking-wide text-clay-700 dark:border-white/10">
            Research-stage guess — not health advice.
          </div>
        </div>
      )}
    </div>
  );
}

export function ConfidenceLegend({ className = '' }) {
  return (
    <div className={'flex flex-wrap gap-2 ' + className}>
      {Object.values(CONFIDENCE_LEVELS).map((t) => (
        <ConfidenceBadge key={t.id} tier={t.id} size='sm' />
      ))}
    </div>
  );
}

/** Small "?" button that opens a friendly "How is this calculated?" popup. */
export function HowCalculated({ title, children }) {
  const [open, setOpen] = useState(false);
  return (
    <>
      <button
        onClick={() => setOpen(true)}
        className="ml-2 inline-flex h-5 w-5 items-center justify-center rounded-full border border-forest-600/25 bg-white text-[11px] font-bold text-forest-700 transition hover:shadow-card hover:scale-105 active:scale-95 dark:bg-white/10 dark:text-cream-100"
        aria-label={`How is ${title} calculated?`}
        title="How is this calculated?"
      >
        ?
      </button>
      {open && (
        <Modal onClose={() => setOpen(false)} title={`How is “${title}” worked out?`}>
          <div className="text-sm leading-relaxed text-forest-900/85 dark:text-cream-100/85">{children}</div>
        </Modal>
      )}
    </>
  );
}

/** Smooth modal popup (scale + fade). */
export function Modal({ onClose, title, children, wide = false }) {
  useEffect(() => {
    const onKey = (e) => { if (e.key === 'Escape') onClose?.(); };
    document.addEventListener('keydown', onKey);
    document.body.style.overflow = 'hidden';
    return () => {
      document.removeEventListener('keydown', onKey);
      document.body.style.overflow = '';
    };
  }, [onClose]);

  return (
    <div
      className="modal-backdrop fixed inset-0 z-[80] flex items-end justify-center bg-forest-950/50 p-3 backdrop-blur-sm sm:items-center sm:p-4"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-label={title}
    >
      <div
        className={`modal-panel w-full ${wide ? 'max-w-2xl' : 'max-w-md'} max-h-[90vh] overflow-y-auto rounded-3xl border border-forest-900/10 bg-white p-5 shadow-lift sm:p-6 dark:bg-forest-900 dark:border-white/10`}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-start justify-between gap-3">
          <h3 className="font-display text-lg font-semibold text-forest-950 dark:text-cream-50">{title}</h3>
          <button
            onClick={onClose}
            className="rounded-full border border-forest-900/10 px-2.5 py-1 text-xs text-forest-700 transition hover:bg-cream-100 active:scale-95 dark:text-cream-100 dark:hover:bg-white/10"
            aria-label="Close"
          >
            ✕
          </button>
        </div>
        <div className="mt-3">{children}</div>
      </div>
    </div>
  );
}

/** Page fade wrapper */
export function Page({ children, className = '' }) {
  return <div className={`page-wrap ${className}`}>{children}</div>;
}

/** Friendly research-only notice used inside cards (replaces jargon disclaimers). */
export function ResearchNote({ text = 'These are early computer guesses for research — not health advice. Lab testing is still needed.' }) {
  return (
    <div className="rounded-2xl border border-gold-300/60 bg-gold-50 p-3 dark:bg-gold-400/10 dark:border-gold-400/30">
      <div className="text-[10px] font-bold uppercase tracking-widest text-gold-700 dark:text-gold-300">🌼 Just so you know</div>
      <p className="mt-1 text-[12px] leading-relaxed text-forest-900/85 dark:text-cream-100/85">{text}</p>
    </div>
  );
}
