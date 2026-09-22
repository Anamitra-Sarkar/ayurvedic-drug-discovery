/**
 * XAIExplanation.jsx — plain-language "Why this result?".
 * Plotly chart kept; labels translated to plain words.
 */
import { useEffect, useRef, useState } from 'react';
import { ConfidenceBadge, HowCalculated, ResearchNote } from './ui.jsx';
import { friendlyFeatureName } from './MLPredictionCard.jsx';

export default function XAIExplanation({ explanation, loading }) {
  const plotRef = useRef(null);
  const [plotlyReady, setPlotlyReady] = useState(false);

  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        if (!explanation?.topFeatures) return;
        const Plotly = await import('plotly.js-dist');
        if (!mounted) return;
        const features = [...explanation.topFeatures].sort((a, b) => Math.abs(b.shap) - Math.abs(a.shap)).slice(0, 8);
        const y = features.map((f) => friendlyFeatureName(f.feature));
        const x = features.map((f) => f.shap);
        const colors = x.map((v) => (v >= 0 ? '#0F5C4D' : '#D9962B'));

        const data = [{
          type: 'bar',
          orientation: 'h',
          x,
          y,
          marker: { color: colors, line: { width: 1, color: '#ffffff' } },
          text: features.map((f) => `${f.shap > 0 ? '+' : ''}${f.shap.toFixed(2)}`),
          textposition: 'auto',
          hovertemplate: '%{y}<br>Push=%{x:.3f}<extra></extra>',
        }];

        const isNarrow = typeof window !== 'undefined' && window.innerWidth < 640;
        const layout = {
          title: { text: `What pushed the prediction up or down`, font: { size: isNarrow ? 11 : 12, family: 'Inter' } },
          margin: { l: isNarrow ? 108 : 150, r: 12, t: 40, b: 30 },
          height: isNarrow ? 340 : 300,
          autosize: true,
          xaxis: { title: 'Push on the strength score →', zeroline: true, gridcolor: '#eee9d6', tickfont: { size: isNarrow ? 9 : 11 } },
          yaxis: { automargin: true, tickfont: { size: isNarrow ? 9 : 11 } },
          plot_bgcolor: 'rgba(0,0,0,0)',
          paper_bgcolor: 'rgba(0,0,0,0)',
          font: { family: 'Inter, sans-serif', size: 11 },
        };

        const config = { responsive: true, displayModeBar: false, useResizeHandler: true };
        if (plotRef.current) {
          Plotly.newPlot(plotRef.current, data, layout, config);
          setPlotlyReady(true);
        }
      } catch (e) {
        console.error('Chart failed', e);
      }
    })();
    return () => { mounted = false; };
  }, [explanation]);

  if (loading) return <div className="rounded-3xl border border-forest-900/10 bg-white p-6 animate-pulse h-[380px] dark:bg-forest-900" />;
  if (!explanation) {
    return (
      <div className="card p-8 text-center">
        <div className="text-3xl">💡</div>
        <div className="text-sm font-medium text-forest-800 dark:text-cream-100 mt-2">No “why” breakdown yet</div>
        <div className="text-xs text-forest-700/70 dark:text-cream-100/60 mt-1">Once there is a prediction, we will show what pushed it up or down.</div>
      </div>
    );
  }

  return (
    <div className="card overflow-hidden">
      <div className="px-4 py-3 sm:px-5 sm:py-4 border-b border-forest-900/10 bg-cream-50/70 flex flex-wrap items-center justify-between gap-2 dark:bg-white/5">
        <div className="flex min-w-0 flex-1 items-center gap-2.5">
          <div className="w-9 h-9 shrink-0 rounded-2xl bg-clay-500 text-white flex items-center justify-center">💡</div>
          <div className="min-w-0">
            <div className="font-display font-semibold text-[15px] text-forest-950 dark:text-cream-50">
              Why this result?
              <HowCalculated title="why this result">
                We ask the model to show its working. Each bar is a chemical feature: bars to the right pushed the strength score up, bars to the left pulled it down. This explains the model’s thinking — not how nature really works.
              </HowCalculated>
            </div>
            <div className="text-[11px] text-forest-700/75 dark:text-cream-100/60">Which chemical patterns mattered most · {explanation.topFeatures?.length} patterns</div>
          </div>
        </div>
        <div className="shrink-0"><ConfidenceBadge tier="XAI_INTERPRETATION" size="sm" align="right" /></div>
      </div>

      <div className="p-4 sm:p-5">
        <div ref={plotRef} className="w-full min-h-[280px] overflow-hidden rounded-2xl border border-forest-900/10 bg-white dark:bg-white/5" />
        {!plotlyReady && <div className="text-[11px] text-forest-700/60 dark:text-cream-100/50 mt-2">Drawing the chart… the table below always works.</div>}

        <div className="mt-4 overflow-x-auto rounded-2xl border border-forest-900/10">
          <div className="min-w-[560px]">
          <div className="grid grid-cols-12 bg-cream-50 text-[10px] tracking-widest uppercase text-forest-700/60 px-3 py-2 border-b border-forest-900/10 dark:bg-white/5">
            <span className="col-span-5">Pattern</span><span className="col-span-2">Value</span><span className="col-span-2">Push</span><span className="col-span-3">What it means</span>
          </div>
          {explanation.topFeatures?.map((f, i) => (
            <div key={i} className="grid grid-cols-12 px-3 py-2 text-xs border-b last:border-0 border-forest-900/5 items-center">
              <span className="col-span-5 font-medium truncate" title={f.feature}>{friendlyFeatureName(f.feature)}</span>
              <span className="col-span-2 text-forest-700/70 dark:text-cream-100/60">{typeof f.value === 'number' ? f.value.toFixed(2) : (f.value == null ? '—' : String(f.value).slice(0, 20))}</span>
              <span className={`col-span-2 font-semibold ${f.shap >= 0 ? 'text-forest-700' : 'text-gold-600'}`}>{f.shap > 0 ? '+' : ''}{f.shap.toFixed(3)}</span>
              <span className="col-span-3 text-[11px] text-forest-800/75 dark:text-cream-100/70 leading-tight">{plainDescription(f.description)}</span>
            </div>
          ))}
          </div>
        </div>

        <div className="mt-4 rounded-2xl bg-cream-50 border border-forest-900/10 p-3 dark:bg-white/5">
          <div className="text-[10px] tracking-widest uppercase font-bold text-forest-800 dark:text-cream-100">In plain words</div>
          <div className="text-[12px] text-forest-900/85 dark:text-cream-100/80 mt-1 leading-relaxed">
            {plainDescription(explanation.summary)} Right-pointing bars pushed the score up; left-pointing bars pulled it down. This shows the model’s reasoning, not a proven real-world cause.
          </div>
        </div>

        <div className="mt-3">
          <ResearchNote text="This breakdown explains the computer model — like seeing a student’s rough work. It does not prove how anything works in real life." />
        </div>
      </div>
    </div>
  );
}

function plainDescription(text) {
  if (!text) return '—';
  return text
    .replace(/SHAP/gi, 'push score')
    .replace(/pKd/gi, 'strength score')
    .replace(/affinity/gi, 'holding strength')
    .replace(/MolLogP/gi, 'oil–water mix')
    .replace(/TPSA/gi, 'exposed surface')
    .replace(/ECFP4[^,]*/gi, 'fragment pattern')
    .replace(/TreeSHAP/gi, 'step-by-step check');
}
