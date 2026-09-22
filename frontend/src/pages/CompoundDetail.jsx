
/**
 * CompoundDetail.jsx
 * Full compound view with all 5 evidence tiers, 3Dmol viewer
 */
import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { apiClient } from '../services/api.js';
import CompoundCard from '../components/CompoundCard.jsx';
import MoleculeViewer from '../components/MoleculeViewer.jsx';
import DockingResults from '../components/DockingResults.jsx';
import MLPredictionCard from '../components/MLPredictionCard.jsx';
import XAIExplanation from '../components/XAIExplanation.jsx';
import LiteraturePanel from '../components/LiteraturePanel.jsx';
import { EvidenceTierLegend, TierSeparator } from '../components/EvidenceTierBadge.jsx';

export default function CompoundDetail() {
  const { id } = useParams();
  const [compound, setCompound] = useState(null);
  const [docking, setDocking] = useState(null);
  const [ml, setMl] = useState(null);
  const [xai, setXai] = useState(null);
  const [lit, setLit] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(()=> {
    (async ()=>{
      setLoading(true);
      const [c, d, m, x, l] = await Promise.all([
        apiClient.getCompound(id),
        apiClient.runDocking(id, '6LU7'),
        apiClient.predictAffinity(id, '6LU7'),
        apiClient.explainPrediction(id, '6LU7'),
        apiClient.queryLiterature(`${id} phytochemical binding target`),
      ]);
      setCompound(c);
      setDocking(d);
      setMl(m);
      setXai(x);
      setLit(l);
      setLoading(false);
    })();
  }, [id]);

  if (loading) {
    return <div className="space-y-4 animate-pulse"><div className="h-24 bg-white border border-slate-200 rounded-2xl" /><div className="h-[480px] bg-white border border-slate-200 rounded-2xl" /></div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2 font-mono text-[11px] text-slate-500">
        <Link to="/" className="hover:text-slate-800">Dashboard</Link><span>/</span><span>{id}</span><span>/</span><span className="text-slate-900 font-semibold">{compound?.name}</span>
      </div>

      <div className="grid lg:grid-cols-12 gap-6">
        <div className="lg:col-span-5 space-y-4">
          {compound && <CompoundCard compound={compound} />}
          <MoleculeViewer dockingResult={docking} height={420} />
          <div className="rounded-2xl border border-amber-200 bg-amber-50 p-3">
            <div className="font-mono text-[11px] font-bold tracking-widest text-amber-900">COMPOUND DETAIL — ALL TIERS SEPARATED</div>
            <div className="mt-1 text-[11px] text-amber-800 leading-relaxed">This view aggregates five evidence tiers for one phytochemical but keeps them visually and semantically separated per AYUSH-64 justification. No tier is presented as validating another; ML does not prove docking, literature does not prove efficacy.</div>
            <div className="mt-2"><EvidenceTierLegend /></div>
          </div>
        </div>

        <div className="lg:col-span-7 space-y-6">
          <DockingResults result={docking} />
          <MLPredictionCard prediction={ml} />
          <XAIExplanation explanation={xai} />
          <LiteraturePanel literature={lit} query={`${compound?.name} target`} />
          <TierSeparator tiersPresent={['DATABASE_DERIVED','DOCKING_RESULT','ML_PREDICTION','XAI_INTERPRETATION','LITERATURE_DERIVED']} />
        </div>
      </div>
    </div>
  );
}
