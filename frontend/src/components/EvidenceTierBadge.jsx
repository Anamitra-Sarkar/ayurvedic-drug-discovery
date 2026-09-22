/**
 * EvidenceTierBadge.jsx — kept for backwards compatibility.
 * Now renders plain-language "Confidence level" labels; internal tier ids unchanged.
 */
import { ConfidenceBadge, ConfidenceLegend } from './ui.jsx';

export default function EvidenceTierBadge(props) {
  return <ConfidenceBadge {...props} />;
}

export function EvidenceTierLegend({ className = '' }) {
  return <ConfidenceLegend className={className} />;
}

export function TierSeparator({ tiersPresent }) {
  return (
    <div className="flex items-center gap-2 py-2">
      <div className="h-px flex-1 bg-forest-900/10 dark:bg-white/10" />
      <span className="text-[10px] tracking-widest text-forest-700/60 dark:text-cream-100/50">
        EACH RESULT IS JUDGED SEPARATELY
      </span>
      <div className="h-px flex-1 bg-forest-900/10 dark:bg-white/10" />
    </div>
  );
}
