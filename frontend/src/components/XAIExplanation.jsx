
/**
 * XAIExplanation.jsx
 * SHAP waterfall plot using plotly, feature importance, tier XAI_INTERPRETATION
 */
import { useEffect, useRef, useState } from 'react';
import EvidenceTierBadge from './EvidenceTierBadge.jsx';

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
        const features = [...explanation.topFeatures].sort((a,b)=>Math.abs(b.shap)-Math.abs(a.shap)).slice(0,8);
        const y = features.map(f=> f.feature);
        const x = features.map(f=> f.shap);
        const colors = x.map(v=> v>=0 ? '#db2777' : '#0e7490');

        const data = [{
          type: 'bar',
          orientation: 'h',
          x,
          y,
          marker: { color: colors, line: { width: 1, color: '#ffffff' } },
          text: features.map(f=> `${f.value} → ${f.shap>0?'+':''}${f.shap.toFixed(2)}`),
          textposition: 'auto',
          hovertemplate: '%{y}<br>SHAP=%{x:.3f}<br>%{text}<extra></extra>',
        }];

        const layout = {
          title: { text: `SHAP Feature Importance — pKd ${explanation.baseValue} → ${explanation.prediction}`, font: { size: 12, family: 'Inter' } },
          margin: { l: 160, r: 20, t: 40, b: 30 },
          height: 320,
          xaxis: { title: 'SHAP value (impact on predicted pKd)', zeroline: true, gridcolor: '#f1f5f9' },
          yaxis: { automargin: true },
          plot_bgcolor: '#ffffff',
          paper_bgcolor: '#ffffff',
          font: { family: 'Inter, sans-serif', size: 11 },
        };

        const config = { responsive: true, displayModeBar: false };
        if (plotRef.current) {
          Plotly.newPlot(plotRef.current, data, layout, config);
          setPlotlyReady(true);
        }
      } catch(e) {
        console.error('Plotly SHAP failed', e);
      }
    })();
    return () => { mounted=false; };
  }, [explanation]);

  if (loading) return <div className="rounded-2xl border border-orange-100 bg-orange-50/50 p-6 animate-pulse h-[380px]" />;
  if (!explanation) return <div className="rounded-2xl border border-slate-200 bg-white p-6 text-center font-mono text-xs text-slate-500">No XAI explanation yet.</div>;

  return (
    <div className="rounded-2xl border border-orange-200 bg-white shadow-card overflow-hidden">
      <div className="px-4 py-3 border-b border-orange-100 bg-orange-50/70 flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-orange-600 text-white flex items-center justify-center">🔍</div>
          <div>
            <div className="font-display font-semibold text-sm">Explainable AI — SHAP Attributions</div>
            <div className="font-mono text-[11px] text-orange-700">Base {explanation.baseValue} → Pred {explanation.prediction} • {explanation.topFeatures?.length} features</div>
          </div>
        </div>
        <EvidenceTierBadge tier="XAI_INTERPRETATION" />
      </div>

      <div className="p-4">
        <div ref={plotRef} className="w-full rounded-xl border border-slate-100 bg-white" />
        {!plotlyReady && <div className="font-mono text-[11px] text-slate-500 mt-2">Loading SHAP waterfall (plotly.js)... fallback table below if plot fails.</div>}

        {/* Fallback table */}
        <div className="mt-4 rounded-xl border border-slate-200 overflow-hidden">
          <div className="grid grid-cols-12 bg-slate-50 font-mono text-[10px] tracking-widest text-slate-500 px-3 py-2 border-b">
            <span className="col-span-5">FEATURE</span><span className="col-span-2">VALUE</span><span className="col-span-2">SHAP</span><span className="col-span-3">INTERPRETATION</span>
          </div>
          {explanation.topFeatures?.map((f,i)=>(
            <div key={i} className="grid grid-cols-12 px-3 py-2 text-xs border-b last:border-0 border-slate-100 items-center">
              <span className="col-span-5 font-mono font-medium truncate" title={f.feature}>{f.feature}</span>
              <span className="col-span-2 font-mono text-slate-600">{typeof f.value==='number'? f.value.toFixed(2): String(f.value).slice(0,20)}</span>
              <span className={`col-span-2 font-mono font-semibold ${f.shap>=0?'text-pink-700':'text-cyan-700'}`}>{f.shap>0?'+':''}{f.shap.toFixed(3)}</span>
              <span className="col-span-3 text-[11px] text-slate-600 leading-tight">{f.description || '—'}</span>
            </div>
          ))}
        </div>

        <div className="mt-4 rounded-xl bg-slate-50 border border-slate-200 p-3">
          <div className="font-mono text-[10px] tracking-widest font-bold text-slate-700">XAI INTERPRETATION — WHY MODEL THINKS IT BINDS</div>
          <div className="text-[11px] text-slate-700 mt-1 leading-relaxed">
            {explanation.summary} SHAP values quantify each RDKit/ECFP4 feature's marginal contribution to predicted pKd via TreeSHAP. Positive SHAP pushes affinity higher. This explains <span className="font-semibold">model reasoning</span>, not biological mechanism. Like AYUSH-64, XAI helps triage chemotypes but does not constitute mechanism proof; requires pathway assays.
          </div>
        </div>

        <div className="mt-3 rounded-xl bg-amber-50 border border-amber-200 p-2.5">
          <div className="font-mono text-[10px] font-bold text-amber-900">TIER XAI_INTERPRETATION — MODEL TRANSPARENCY, NOT CAUSALITY</div>
        </div>
      </div>
    </div>
  );
}
