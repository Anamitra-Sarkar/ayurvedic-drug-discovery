/**
 * PipelineRun.jsx — "/pipeline" guided analysis flow, plain language.
 * Same staged mock progression + real apiClient.runPipeline call.
 */
import { useState } from 'react';
import { Link } from 'react-router-dom';
import PipelineFlow from '../components/PipelineFlow.jsx';
import { Page, ResearchNote } from '../components/ui.jsx';
import { ConfidenceBadge } from '../components/ui.jsx';
import { PROTEIN_SHAPES, FRIENDLY_STEPS } from '../utils/friendly.js';
import { apiClient } from '../services/api.js';

const STEP_TIER = { i: 'DATABASE_DERIVED', ii: 'DATABASE_DERIVED', iii: 'DOCKING_RESULT', iv: 'ML_PREDICTION', v: 'XAI_INTERPRETATION', vi: 'LITERATURE_DERIVED' };

export default function PipelineRun() {
  const [compoundId, setCompoundId] = useState('IMP000013');
  const [target, setTarget] = useState('6LU7');
  const [jobId, setJobId] = useState(null);
  const [status, setStatus] = useState(null);
  const [logs, setLogs] = useState([]);
  const [activeLayer, setActiveLayer] = useState('i');
  const [running, setRunning] = useState(false);

  const addLog = (stepId, message) => {
    setLogs((prev) => [...prev, { time: new Date().toLocaleTimeString(), stepId, message }]);
  };

  // The 6 "steps" below are a friendly narration of what the real backend
  // pipeline (database -> cheminformatics -> docking -> ML -> XAI ->
  // literature) is doing while we wait for it - they advance on a timer
  // because the orchestrator doesn't stream per-step progress, but they
  // NEVER claim completion on their own: progress caps at 92% until the
  // real apiClient.runPipeline() call actually resolves, and only a real
  // success reaches 100% / unlocks the results link. A real failure shows
  // an honest error instead of a fake "done" state.
  const NARRATION = [
    { id: 'i', cap: 15, msg: 'Found the plant, the compound and its traditional background.' },
    { id: 'ii', cap: 35, msg: 'Measuring basic chemical properties (size, balance, surface).' },
    { id: 'iii', cap: 55, msg: `Trying the compound inside the ${target} protein shape from many angles.` },
    { id: 'iv', cap: 75, msg: 'The model predicts a strength score and checks its trust level.' },
    { id: 'v', cap: 88, msg: 'Showing which chemical patterns pushed the guess up or down.' },
    { id: 'vi', cap: 92, msg: 'Comparing with published papers and gathering sources.' },
  ];

  const runPipeline = async () => {
    setRunning(true);
    setLogs([]);
    setStatus({ progress: 0, stage: 'Warming up…' });
    addLog('i', `Finding ${compoundId} in the plant library…`);

    let step = 0;
    const startedAt = Date.now();
    const timer = setInterval(() => {
      if (step < NARRATION.length) {
        const n = NARRATION[step];
        setActiveLayer(n.id);
        addLog(n.id, n.msg);
        setStatus({ progress: n.cap, stage: `Working — this can take a little while on real chemistry` });
        step += 1;
        return;
      }
      // Real docking + ML + XAI + a real literature LLM call genuinely
      // takes ~60-90s end to end (timed live at 70s) - once the 6 narration
      // steps run out, keep sending a real-elapsed-time heartbeat so the
      // page never looks frozen for the remaining wait.
      const elapsed = Math.round((Date.now() - startedAt) / 1000);
      addLog('vi', `Still working — real chemistry takes longer than a demo would (${elapsed}s so far)…`);
    }, 5000);

    try {
      const job = await apiClient.runPipeline({ compound_id: compoundId, target });
      clearInterval(timer);
      setActiveLayer('vi');
      setJobId(job.jobId || job.request_id || null);
      setStatus({ progress: 100, stage: 'Done — your results are ready 🎉' });
      addLog('vi', 'Full pipeline finished — real docking, prediction and literature results are ready.');
    } catch (e) {
      clearInterval(timer);
      setStatus({ progress: 0, stage: 'The analysis failed — no results were generated' });
      addLog('vi', `We hit a real error and stopped rather than show made-up results: ${e?.response?.data?.detail || e?.message || 'unknown error'}`);
    }
    setRunning(false);
  };

  const stepName = (id) => FRIENDLY_STEPS.find((s) => s.id === id)?.name || id;

  return (
    <Page className="space-y-6">
      <div>
        <h1 className="font-display text-3xl md:text-4xl font-semibold text-forest-950 dark:text-cream-50">Run a new analysis</h1>
        <p className="mt-2 max-w-2xl text-[15px] leading-relaxed text-forest-800/80 dark:text-cream-100/70">
          Pick a compound and a protein shape. We will walk through six gentle steps and explain each one —
          real computation, usually one to two minutes, with plain words throughout.
        </p>
      </div>

      <div className="card p-5 md:p-6">
        <div className="font-display font-bold text-lg text-forest-950 dark:text-cream-50">Start here</div>
        <p className="text-xs text-forest-700/70 dark:text-cream-100/60 mt-1">Tip: “IMP000013” is Withaferin A from Ashwagandha — a lovely first try.</p>

        <div className="mt-4 grid md:grid-cols-12 gap-3 items-end">
          <div className="md:col-span-4">
            <label htmlFor="compound-id" className="text-[11px] tracking-widest uppercase text-forest-700/70 dark:text-cream-100/60">Compound code</label>
            <input
              id="compound-id"
              value={compoundId}
              onChange={(e) => setCompoundId(e.target.value)}
              className="mt-1 w-full px-3 py-2.5 rounded-2xl border border-forest-900/10 bg-cream-50 text-sm dark:bg-white/5 dark:border-white/10 dark:text-cream-50"
              placeholder="IMP000013"
            />
          </div>
          <div className="md:col-span-3">
            <label htmlFor="shape-pick" className="text-[11px] tracking-widest uppercase text-forest-700/70 dark:text-cream-100/60">Protein shape</label>
            <div className="relative mt-1">
              <select
                id="shape-pick"
                value={target}
                onChange={(e) => setTarget(e.target.value)}
                className="w-full appearance-none px-3 py-2.5 pr-9 rounded-2xl border border-forest-900/10 bg-white text-sm text-forest-950 dark:bg-white/5 dark:border-white/10 dark:text-cream-50 focus:outline-none focus:ring-2 focus:ring-forest-500/40 transition-shadow"
              >
                {PROTEIN_SHAPES.map((p) => (
                  <option key={p.code} value={p.code}>{p.code} — {p.name}</option>
                ))}
              </select>
              <span className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-forest-700/50 dark:text-cream-100/50 text-xs">▾</span>
            </div>
          </div>
          <div className="md:col-span-5 flex flex-col sm:flex-row gap-2">
            <button onClick={runPipeline} disabled={running} className="btn-primary flex-1">
              {running ? <span className="spinner" /> : '▶'} {running ? 'Working…' : 'Start my analysis'}
            </button>
            <button onClick={() => { setLogs([]); setStatus(null); }} className="btn-secondary">Clear</button>
          </div>
        </div>

        {status && (
          <div className="mt-4">
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-[12px] font-medium text-forest-800 dark:text-cream-100">{status.stage}</span>
              <span className="text-[12px] text-forest-700/70 dark:text-cream-100/60">{status.progress}%</span>
            </div>
            <div className="w-full h-2.5 bg-cream-200 rounded-full overflow-hidden dark:bg-white/10">
              <div className="h-full rounded-full bg-gradient-to-r from-forest-600 to-gold-500 transition-all duration-500" style={{ width: `${status.progress}%` }} />
            </div>
          </div>
        )}

        {status?.progress === 100 && !running && (
          <div className="modal-panel mt-4 flex flex-wrap items-center gap-3 rounded-2xl bg-forest-50 border border-forest-200 p-4 dark:bg-white/5">
            <span className="text-xl">🎉</span>
            <p className="text-sm text-forest-900 dark:text-cream-50 flex-1 min-w-[200px]">Your results are ready — see them split into four friendly tabs.</p>
            <Link to={`/results/${compoundId}?shape=${target}`} className="btn-primary !py-2.5">See my results →</Link>
          </div>
        )}
      </div>

      <PipelineFlow activeLayer={activeLayer} onSelectLayer={setActiveLayer} />

      <div className="rounded-3xl border border-forest-900/10 bg-forest-950 text-cream-100 p-5 shadow-card font-mono text-[12px] leading-relaxed max-h-[360px] overflow-auto dark:bg-white/5">
        <div className="flex items-center justify-between mb-3">
          <span className="font-bold tracking-widest text-white font-sans text-sm">What’s happening — live notes</span>
          <span className="text-[10px] px-2.5 py-1 rounded-full bg-white/10">{logs.length} notes · {jobId || 'getting ready'}</span>
        </div>
        {logs.length === 0 ? (
          <div className="text-cream-100/50 font-sans text-sm">Nothing yet — press “Start my analysis” and follow along here. 🌱</div>
        ) : logs.map((l, i) => (
          <div key={i} className="py-2 border-b border-white/10 flex gap-3 items-start">
            <span className="text-cream-100/40 shrink-0">{l.time}</span>
            <ConfidenceBadge tier={STEP_TIER[l.stepId] || 'DATABASE_DERIVED'} size="sm" showLabel={false} />
            <span className="flex-1 font-sans text-[13px]"><strong>{stepName(l.stepId)}:</strong> {l.message}</span>
          </div>
        ))}
      </div>

      <ResearchNote />
    </Page>
  );
}
