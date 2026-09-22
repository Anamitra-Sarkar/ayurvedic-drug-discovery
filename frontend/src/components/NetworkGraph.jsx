
/**
 * NetworkGraph.jsx
 * Network pharmacology graph for Triphala example (174 bioactives)
 * Canvas-based force layout + SVG fallback, tier DATABASE_DERIVED for structure, LITERATURE_DERIVED for edges
 */
import { useEffect, useRef, useState, useMemo } from 'react';
import { ConfidenceBadge } from './ui.jsx';
import { proteinShapeName } from '../utils/friendly.js';

const KNOWN_SHAPE_NAMES = { 'NF-kB': 'Cell-stress shape', 'TNF-alpha': 'Immune-signal shape', 'IL-6': 'Immune-signal shape', 'COX-2': 'Swelling-linked shape', 'Mpro': 'Virus defence shape', 'ACE2': 'Virus defence shape' };
function labelFor(n) {
  if (n.type === 'target') {
    if (KNOWN_SHAPE_NAMES[n.label]) return KNOWN_SHAPE_NAMES[n.label];
    if (KNOWN_SHAPE_NAMES[n.id]) return KNOWN_SHAPE_NAMES[n.id];
    const friendly = proteinShapeName(n.id);
    if (friendly !== ('Protein shape ' + n.id)) return friendly;
  }
  return n.label;
}

export default function NetworkGraph({ networkData, loading }) {
  const canvasRef = useRef(null);
  const [hoverNode, setHoverNode] = useState(null);
  const [filter, setFilter] = useState('all'); // all, plant, compound, target
  const [search, setSearch] = useState('');

  const stats = networkData?.stats;

  // Simplified force simulation parameters
  const filtered = useMemo(()=> {
    if (!networkData?.nodes) return { nodes: [], edges: [] };
    let nodes = networkData.nodes;
    let edges = networkData.edges;
    if (filter !== 'all') {
      nodes = nodes.filter(n=> n.type===filter || ['plant','target'].includes(n.type) && filter==='all' ? true : n.type===filter || n.type==='plant' || n.type==='target');
      // keep edges where both ends in filtered nodes
      const ids = new Set(nodes.map(n=>n.id));
      edges = edges.filter(e=> ids.has(e.source) && ids.has(e.target));
    }
    if (search) {
      const s = search.toLowerCase();
      nodes = nodes.filter(n=> n.label.toLowerCase().includes(s) || n.id.toLowerCase().includes(s));
      const ids = new Set(nodes.map(n=>n.id));
      edges = edges.filter(e=> ids.has(e.source) && ids.has(e.target));
    }
    return { nodes: nodes.slice(0, 220), edges };
  }, [networkData, filter, search]);

  useEffect(()=> {
    if (!canvasRef.current || !filtered.nodes.length) return;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    const w = canvas.width = canvas.clientWidth * 2;
    const h = canvas.height = 420 * 2;
    ctx.scale(2,2);
    const width = canvas.clientWidth;
    const height = 420;

    // Naive circular layout for plants, random for others, then a few force iterations
    const nodes = filtered.nodes.map((n,i)=>{
      if (n.type==='plant') {
        const angle = (i/3) * Math.PI *2;
        return { ...n, x: width/2 + Math.cos(angle)*120, y: height/2 + Math.sin(angle)*100, vx:0, vy:0 };
      } else if (n.type==='target') {
        return { ...n, x: 50 + (i%6)* (width/7), y: height-60, vx:0, vy:0 };
      } else {
        return { ...n, x: width/2 + (Math.random()-0.5)*260, y: height/2 + (Math.random()-0.5)*180, vx:0, vy:0 };
      }
    });

    // very simple force iteration
    for (let iter=0; iter<60; iter++) {
      // repulsion
      for (let i=0;i<nodes.length;i++) {
        for (let j=i+1;j<nodes.length;j++) {
          const dx = nodes[i].x-nodes[j].x;
          const dy = nodes[i].y-nodes[j].y;
          const dist = Math.sqrt(dx*dx+dy*dy) || 1;
          if (dist < 80) {
            const f = (80-dist)*0.02;
            const fx = dx/dist*f;
            const fy = dy/dist*f;
            nodes[i].vx+=fx; nodes[i].vy+=fy;
            nodes[j].vx-=fx; nodes[j].vy-=fy;
          }
        }
      }
      // attraction for edges
      filtered.edges.forEach(e=>{
        const s = nodes.find(n=>n.id===e.source);
        const t = nodes.find(n=>n.id===e.target);
        if (!s||!t) return;
        const dx = t.x - s.x;
        const dy = t.y - s.y;
        const dist = Math.sqrt(dx*dx+dy*dy) || 1;
        const f = dist*0.003 * e.weight;
        s.vx+=dx*f; s.vy+=dy*f;
        t.vx-=dx*f; t.vy-=dy*f;
      });
      // integrate + damping + bounds
      nodes.forEach(n=>{
        n.vx*=0.85; n.vy*=0.85;
        n.x+=n.vx; n.y+=n.vy;
        n.x=Math.max(20,Math.min(width-20,n.x));
        n.y=Math.max(20,Math.min(height-20,n.y));
      });
    }

    // draw
    ctx.clearRect(0,0,width,height);
    // edges
    ctx.lineWidth = 0.6;
    filtered.edges.forEach(e=>{
      const s = nodes.find(n=>n.id===e.source);
      const t = nodes.find(n=>n.id===e.target);
      if (!s||!t) return;
      ctx.beginPath();
      ctx.moveTo(s.x,s.y);
      ctx.lineTo(t.x,t.y);
      ctx.strokeStyle = e.type==='predicted' ? '#f9a8d4' : '#e5e7eb';
      ctx.globalAlpha = e.weight || 0.8;
      ctx.stroke();
    });
    ctx.globalAlpha = 1;

    // nodes
    nodes.forEach(n=>{
      ctx.beginPath();
      ctx.arc(n.x,n.y, n.size||4, 0, Math.PI*2);
      ctx.fillStyle = n.color || '#888';
      ctx.fill();
      ctx.strokeStyle = '#ffffff';
      ctx.lineWidth = 1;
      ctx.stroke();

      if (n.type==='plant' || n.type==='target') {
        ctx.fillStyle = '#0f172a';
        ctx.font = '11px Inter';
        ctx.fillText(labelFor(n), n.x+ (n.size||4)+4, n.y+3);
      }
    });

    // hover detection not fully implemented for brevity

  }, [filtered]);

  if (loading) return <div className="card h-[460px] animate-pulse p-6" />;

  return (
    <div className="rounded-2xl border border-slate-200 bg-white shadow-card overflow-hidden">
      <div className="px-4 py-3 border-b border-slate-100 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex min-w-0 items-center gap-2.5">
          <div className="w-8 h-8 shrink-0 rounded-lg bg-green-700 text-white flex items-center justify-center">🕸️</div>
          <div className="min-w-0">
            <div className="font-display font-semibold text-sm truncate">Triphala plant map</div>
            <div className="font-mono text-[10px] sm:text-[11px] text-slate-500 leading-snug">Plant connections — {stats?.plants ?? 3} plants • {stats?.bioactives ?? 174} bioactives • {stats?.targets ?? '—'} shared targets (literature) • {filtered.edges.length} edges shown</div>
          </div>
        </div>
        <div className="flex shrink-0 items-center gap-1.5 overflow-x-auto">
          <ConfidenceBadge tier="DATABASE_DERIVED" size="sm" />
          <ConfidenceBadge tier="LITERATURE_DERIVED" size="sm" />
        </div>
      </div>

      <div className="px-4 py-3 flex flex-wrap gap-2 items-center border-b border-slate-100 bg-slate-50/60">
        {[
          {id:'all', label:'All'},
          {id:'plant', label:'Plants'},
          {id:'compound', label:`Compounds (${stats?.bioactives ?? 174})`},
          {id:'target', label:'Targets'},
        ].map(b=>(
          <button key={b.id} onClick={()=>setFilter(b.id)} className={`px-3 py-1.5 rounded-full text-xs font-medium border ${filter===b.id ? 'bg-slate-900 text-white border-slate-900' : 'bg-white border-slate-200 text-slate-700 hover:bg-slate-50'}`}>{b.label}</button>
        ))}
        <div className="w-full sm:w-auto sm:ml-auto flex items-center gap-2">
          <input value={search} onChange={e=>setSearch(e.target.value)} placeholder="Filter nodes..." className="px-3 py-1.5 rounded-full border border-slate-200 bg-white font-mono text-xs w-full sm:w-[180px]" />
        </div>
      </div>

      <div className="relative bg-[#fcfcfa] border-b border-slate-100">
        <canvas ref={canvasRef} className="w-full min-h-[300px]" style={{height: 'clamp(300px, 70vw, 420px)', display:'block'}} />
        <div className="absolute top-3 left-3 max-w-[calc(100%-24px)] rounded-xl bg-white/95 border border-slate-200 shadow-sm p-2 sm:p-2.5 space-y-1 sm:space-y-1.5">
          <div className="font-mono text-[10px] tracking-widest text-slate-500">Map key</div>
          <div className="flex items-center gap-2 text-[11px] font-mono"><span className="w-2.5 h-2.5 rounded-full bg-[#16a34a]" /> Plant</div>
          <div className="flex items-center gap-2 text-[11px] font-mono"><span className="w-2 h-2 rounded-full bg-[#7c3aed]" /> Natural compound</div>
          <div className="flex items-center gap-2 text-[11px] font-mono"><span className="w-2.5 h-2.5 rounded-full bg-[#db2777]" /> Protein shape (compared)</div>
          <div className="flex items-center gap-2 text-[11px] font-mono"><span className="w-4 h-0.5 bg-slate-300" /> Comes from this plant</div>
          <div className="flex items-center gap-2 text-[11px] font-mono"><span className="w-4 h-0.5 bg-pink-300" /> Compared with this shape</div>
        </div>
        <div className="absolute bottom-3 right-3 rounded-full bg-white border border-slate-200 px-3 py-1 font-mono text-[10px] text-slate-500">Interactive map • research preview only</div>
      </div>

      <div className="p-3 sm:p-4 grid grid-cols-1 sm:grid-cols-3 gap-2 sm:gap-3">
        <div className="rounded-xl bg-slate-50 border border-slate-200 p-3 text-center">
          <div className="font-mono text-[10px] tracking-widest text-slate-500">Plants (Triphala)</div>
          <div className="font-mono text-lg font-bold mt-1">{stats?.plants || 3}</div>
          <div className="font-mono text-[11px] text-slate-600 mt-1">Amalaki, Bibhitaki, Haritaki</div>
        </div>
        <div className="rounded-xl bg-violet-50 border border-violet-100 p-3 text-center">
          <div className="font-mono text-[10px] tracking-widest text-violet-600">Natural compounds</div>
          <div className="font-mono text-lg font-bold mt-1 text-violet-800">{stats?.bioactives || 174}</div>
          <div className="font-mono text-[11px] text-violet-700 mt-1">From the plant library</div>
        </div>
        <div className="rounded-xl bg-green-50 border border-green-100 p-3 text-center">
          <div className="font-mono text-[10px] tracking-widest text-green-600">Comparisons</div>
          <div className="font-mono text-lg font-bold mt-1 text-green-800">{stats?.interactions || 200}+</div>
          <div className="font-mono text-[11px] text-green-700 mt-1">Library + computer checks</div>
        </div>
      </div>

      <div className="px-4 pb-4">
        <div className="rounded-xl bg-amber-50 border border-amber-200 p-3">
          <div className="font-mono text-[10px] font-bold tracking-widest text-amber-900">Triphala example — three plants, many compounds</div>
          <div className="text-[11px] text-amber-800 mt-1 leading-relaxed">Triphala blends three fruits — Amla, Bibhitaki and Haritaki. Dots are plants (green), natural compounds (purple) and protein shapes (pink). Lines show which compound comes from which plant, and which protein shapes they were compared with. A busy map hints at variety — not at health effects.</div>
        </div>
      </div>
    </div>
  );
}
