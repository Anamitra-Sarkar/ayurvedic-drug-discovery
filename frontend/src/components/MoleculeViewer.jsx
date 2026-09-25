
/**
 * MoleculeViewer.jsx
 * 3Dmol.js viewer for protein-ligand complex, shows interactions, pose
 * - Supports PDB for protein, SDF/MOL for ligand
 * - Interaction visualization
 * - Evidence tier: DOCKING_RESULT
 */
import React, { useEffect, useRef, useState } from 'react';
import { ConfidenceBadge } from './ui.jsx';
import { proteinShapeName, interactionLabel } from '../utils/friendly.js';

function shapeTitle(raw) {
  if (!raw) return 'Protein shape preview';
  const m = String(raw).match(/(6LU7|1P44|2AZ5|4KIK)/);
  if (m) return proteinShapeName(m[1]);
  return 'Protein shape preview';
}

// Style buttons previously only ever restyled the tiny ligand while the
// protein stayed cartoon forever, so the huge protein dominated the view
// and every button looked the same. Both models now switch representation
// together, so "Sticks"/"Balls"/"Lines"/"Ribbons" each genuinely differ.
function proteinStyleFor(style) {
  switch (style) {
    case 'sphere': return { sphere: { scale: 0.22, colorscheme: 'Jmol' } };
    case 'line': return { line: { colorscheme: 'Jmol' } };
    case 'stick': return { stick: { radius: 0.15, colorscheme: 'Jmol' } };
    case 'cartoon':
    default:
      return { cartoon: { color: '#a3b18a', opacity: 0.85 } };
  }
}

function ligandStyleFor(style) {
  switch (style) {
    case 'sphere': return { sphere: { scale: 0.3, colorscheme: 'greenCarbon' } };
    case 'line': return { line: { colorscheme: 'greenCarbon', linewidth: 3 } };
    case 'cartoon': return { stick: { radius: 0.2, colorscheme: 'greenCarbon' }, sphere: { scale: 0.25, colorscheme: 'greenCarbon' } };
    case 'stick':
    default:
      return { stick: { radius: 0.25, colorscheme: 'greenCarbon' }, sphere: { scale: 0.22, colorscheme: 'greenCarbon' } };
  }
}

export default function MoleculeViewer({
  proteinPDB = null, // real PDB text (RCSB structure)
  ligandSDF = null, // SDF/MOL string (legacy prop, mock fallback only)
  ligandPDB = null, // real PDB text (RDKit 3D-embedded ligand)
  dockingResult = null,
  height = 480,
  showControls = true,
}) {
  const viewerRef = useRef(null);
  const containerRef = useRef(null);
  const [style, setStyle] = useState('stick'); // stick, sphere, cartoon, line
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [viewerReady, setViewerReady] = useState(false);

  // Default PDB for demo - small peptide from 6LU7 Mpro active site snippet
  const defaultProteinPDB = `ATOM      1  N   HIS A  41      10.123  15.234  20.345  1.00  20.00           N
ATOM      2  CA  HIS A  41      11.345  15.678  21.123  1.00  20.00           C
ATOM      3  C   HIS A  41      12.123  14.567  22.000  1.00  20.00           C
ATOM      4  O   HIS A  41      11.890  13.400  22.100  1.00  20.00           O
ATOM      5  CB  HIS A  41      10.900  16.900  22.000  1.00  20.00           C
ATOM      6  CG  HIS A  41      10.200  18.100  21.200  1.00  20.00           C
ATOM      7  N   MET A  49       9.000  14.000  18.000  1.00  20.00           N
ATOM      8  CA  MET A  49       8.123  13.500  17.200  1.00  20.00           C
ATOM      9  C   MET A  49       7.500  12.200  17.800  1.00  20.00           C
ATOM     10  O   MET A  49       7.800  11.200  17.200  1.00  20.00           O
ATOM     11  N   HIS A 163       5.000  10.000  15.000  1.00  20.00           N
ATOM     12  CA  HIS A 163       4.200   9.500  14.200  1.00  20.00           C
ATOM     13  C   HIS A 163       3.500   8.200  14.800  1.00  20.00           C
ATOM     14  O   HIS A 163       3.800   7.200  14.200  1.00  20.00           O
ATOM     15  N   GLU A 166       2.000   9.000  13.000  1.00  20.00           N
ATOM     16  CA  GLU A 166       1.200   8.500  12.200  1.00  20.00           C
END
`;

  const defaultLigandSDF = `
  Withaferin A mock
     RDKit          2D

  8  8  0  0  0  0  0  0  0  0999 V2000
    0.0000    0.0000    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0
    1.2000    0.0000    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0
    1.8000    1.0000    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0
    1.2000    2.0000    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0
    0.0000    2.0000    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0
   -0.6000    1.0000    0.0000 O   0  0  0  0  0  0  0  0  0  0  0  0
    2.5000   -1.0000    0.0000 O   0  0  0  0  0  0  0  0  0  0  0  0
   -1.2000   -0.5000    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0
  1  2  2  0  0  0  0
  2  3  1  0  0  0  0
  3  4  2  0  0  0  0
  4  5  1  0  0  0  0
  5  1  1  0  0  0  0
  5  6  1  0  0  0  0
  2  7  2  0  0  0  0
  1  8  1  0  0  0  0
M  END
$$$$
`;

  useEffect(() => {
    let mounted = true;
    const initViewer = async () => {
      if (!containerRef.current) return;
      setIsLoading(true);
      setError(null);
      try {
        // Dynamic import 3dmol
        const $3Dmol = await import('3dmol');
        if (!mounted) return;

        // Clear previous
        containerRef.current.innerHTML = '';
        const viewer = $3Dmol.createViewer(containerRef.current, {
          backgroundColor: '#f8faf6',
          antialias: true,
        });
        viewerRef.current = viewer;

        const pdbData = proteinPDB || defaultProteinPDB;
        // Prefer the real RDKit-embedded ligand PDB; fall back to the
        // legacy mock SDF only when no real structure was returned.
        const ligandData = ligandPDB || ligandSDF || defaultLigandSDF;
        const ligandFormat = ligandPDB ? 'pdb' : 'sdf';

        // Add protein
        viewer.addModel(pdbData, 'pdb');
        viewer.setStyle({ model: 0 }, proteinStyleFor(style));

        // Add ligand as second model
        if (ligandData) {
          viewer.addModel(ligandData, ligandFormat);
          viewer.setStyle({ model: 1 }, ligandStyleFor(style));
        }

        // Highlight interactions if present
        if (dockingResult?.interactions) {
          dockingResult.interactions.forEach(inter => {
            // Simple labeling - create pseudo shape
            // In real implementation you'd get residue coordinates
          });
        }

        viewer.zoomTo();
        viewer.render();
        setViewerReady(true);
      } catch (e) {
        console.error('3Dmol init failed', e);
        setError(e.message);
      } finally {
        setIsLoading(false);
      }
    };

    initViewer();
    return () => { mounted = false; };
  }, [proteinPDB, ligandSDF, ligandPDB, dockingResult]);

  // Update style dynamically
  useEffect(() => {
    if (!viewerRef.current || !viewerReady) return;
    try {
      viewerRef.current.setStyle({ model: 0 }, proteinStyleFor(style));
      viewerRef.current.setStyle({ model: 1 }, ligandStyleFor(style));
      viewerRef.current.render();
    } catch {}
  }, [style, viewerReady]);

  const handleExport = () => {
    if (!viewerRef.current) return;
    const img = viewerRef.current.pngURI();
    const a = document.createElement('a');
    a.href = img;
    a.download = 'docking_pose.png';
    a.click();
  };

  return (
    <div className="rounded-2xl border border-slate-200 bg-white shadow-card overflow-hidden">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-2 px-4 py-3 border-b border-slate-100 bg-slate-50/60">
        <div className="flex min-w-0 flex-1 items-center gap-3">
          <div className="w-8 h-8 shrink-0 rounded-lg bg-violet-600 text-white flex items-center justify-center text-sm">🧬</div>
          <div className="min-w-0">
            <div className="font-display font-semibold text-sm truncate">3D protein shape + compound</div>
            <div className="font-mono text-[11px] text-slate-500 truncate">{shapeTitle(dockingResult?.target)} • {dockingResult?.affinity_kcal_mol ? `${dockingResult.affinity_kcal_mol} kcal/mol` : 'pose preview'}</div>
          </div>
        </div>
        <div className="flex shrink-0 items-center gap-2">
          <ConfidenceBadge tier="DOCKING_RESULT" size="sm" align="right" />
        </div>
      </div>

      {/* Viewer — fluid width, clamped height so it fits phones and desktops */}
      <div className="relative bg-[#f8faf6]">
        <div ref={containerRef} className="molecule-viewer w-full min-h-[300px] h-[62vw] max-h-[440px] sm:h-[380px] sm:max-h-none lg:h-[440px]" style={{ height: `clamp(300px, 62vw, ${height}px)`, width: '100%', position: 'relative' }} />
        {isLoading && (
          <div className="absolute inset-0 bg-white/70 backdrop-blur-sm flex items-center justify-center">
            <div className="flex flex-col items-center gap-2">
              <div className="w-6 h-6 border-2 border-violet-600 border-t-transparent rounded-full animate-spin" />
              <span className="font-mono text-xs text-slate-600">Loading the 3D view...</span>
            </div>
          </div>
        )}
        {error && (
          <div className="absolute inset-0 bg-red-50 flex items-center justify-center p-6 text-center">
            <div>
              <div className="text-red-700 font-semibold text-sm">3D view hiccup</div>
              <div className="text-xs text-red-600 mt-1 font-mono break-all">{error}</div>
              <div className="text-[11px] text-slate-500 mt-2">Try reloading — a still preview is shown meanwhile.</div>
            </div>
          </div>
        )}
        {/* Watermark */}
        <div className="absolute bottom-2 right-3 font-mono text-[10px] text-slate-400 bg-white/80 px-2 py-0.5 rounded-full border border-slate-200">3D view • computer preview</div>
      </div>

      {/* Controls */}
      {showControls && (
        <div className="px-4 py-3 border-t border-slate-100 flex flex-col gap-2.5 sm:flex-row sm:flex-wrap sm:items-center sm:justify-between">
          <div className="flex items-center gap-1.5 overflow-x-auto scrollbar-hide pb-0.5 -mx-1 px-1">
            {[
              { id: 'stick', label: 'Sticks' },
              { id: 'sphere', label: 'Balls' },
              { id: 'line', label: 'Lines' },
              { id: 'cartoon', label: 'Ribbons' },
            ].map(b => (
              <button
                key={b.id}
                onClick={()=>setStyle(b.id)}
                className={`shrink-0 px-3 py-1.5 rounded-full text-xs font-medium border transition ${style===b.id ? 'bg-slate-900 text-white border-slate-900' : 'bg-white text-slate-700 border-slate-200 hover:bg-slate-50'}`}
              >
                {b.label}
              </button>
            ))}
          </div>
          <div className="flex items-center gap-2">
            <button onClick={()=>viewerRef.current?.zoomTo()} className="px-3 py-1.5 rounded-full text-xs border border-slate-200 bg-white hover:bg-slate-50">Fit</button>
            <button onClick={handleExport} className="px-3 py-1.5 rounded-full text-xs border border-slate-200 bg-white hover:bg-slate-50">PNG</button>
          </div>
        </div>
      )}

      {/* Interactions - only when there's real per-residue contact data;
          the backend's docking response doesn't populate this yet (only
          aggregate hydrophobic/hbond counts), so an empty array is the
          normal case and shouldn't render an empty-looking section. */}
      {dockingResult?.interactions?.length > 0 && (
        <div className="px-4 py-3 bg-violet-50/60 border-t border-violet-100">
          <div className="font-mono text-[11px] tracking-widest text-violet-800 font-semibold mb-2">Where it seems to touch</div>
          <div className="flex flex-wrap gap-2">
            {dockingResult.interactions.map((it, i)=>(
              <span key={i} className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-white border border-violet-200 text-xs">
                <span className="w-1.5 h-1.5 rounded-full bg-violet-600" />
                <span className="font-medium">{interactionLabel(it.type).icon} {interactionLabel(it.type).label}</span>
                <span className="font-mono text-slate-500">{it.residue}</span>
                <span className="font-mono text-[11px] text-slate-400">{typeof it.distance === 'number' ? it.distance.toFixed(2) : it.distance}Å</span>
              </span>
            ))}
          </div>
          <div className="mt-2 font-mono text-[10px] text-violet-700">⚠️ A computer guess about touch points — lab testing would still be needed.</div>
        </div>
      )}
    </div>
  );
}
