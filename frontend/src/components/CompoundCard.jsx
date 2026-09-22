/**
 * CompoundCard.jsx — plain-language plant compound card.
 * Data/API shapes unchanged; only visible copy is consumer-friendly.
 */
import { Link } from 'react-router-dom';
import { ConfidenceBadge, HowCalculated } from './ui.jsx';
import { shortChemicalId } from '../utils/friendly.js';

export default function CompoundCard({ compound, compact = false, onSelect }) {
  if (!compound) return null;
  const dl = compound.drugLikeness || {};
  const admet = compound.admet || {};

  const balance = dl.qed ?? null;
  const balanceStyle =
    balance > 0.7
      ? 'text-forest-700 bg-forest-50 border-forest-200'
      : balance > 0.5
        ? 'text-gold-700 bg-gold-50 border-gold-200'
        : 'text-forest-900/60 bg-cream-100 border-forest-900/10';

  return (
    <div
      className={`card card-lift overflow-hidden ${compact ? 'p-3' : 'p-0'} ${onSelect ? 'cursor-pointer' : ''}`}
      onClick={() => onSelect?.(compound)}
    >
      <div className={compact ? '' : 'p-5'}>
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2 flex-wrap">
              <h3 className="font-display font-semibold text-[17px] text-forest-950 dark:text-cream-50 truncate">{compound.name}</h3>
              <span className="text-[10px] px-1.5 py-0.5 rounded bg-cream-100 border border-forest-900/10 text-forest-700 dark:bg-white/10 dark:text-cream-100/70">
                {compound.id}
              </span>
            </div>
            <div className="mt-1 flex items-center gap-2 flex-wrap">
              <span className="text-[12px] text-forest-700/80 dark:text-cream-100/70 truncate">{compound.plant}</span>
              {compound.ayurvedicName && (
                <span className="text-[11px] px-2 py-0.5 rounded-full bg-gold-50 border border-gold-300/60 text-gold-700 dark:bg-gold-400/10 dark:text-gold-300">
                  {compound.ayurvedicName}
                </span>
              )}
            </div>
          </div>
          <ConfidenceBadge tier={compound.evidenceTier || 'DATABASE_DERIVED'} size="sm" />
        </div>

        {!compact && (
          <div className="mt-4 rounded-2xl bg-cream-50 border border-forest-900/10 h-[96px] flex items-center justify-center relative overflow-hidden dark:bg-white/5">
            <div className="text-[12px] text-forest-700/70 dark:text-cream-100/60 text-center px-3">
              <div className="text-xl">🌿</div>
              <div className="mt-1 font-medium text-forest-900 dark:text-cream-50">{compound.formula || 'Formula not listed'} · {compound.mw ? `${compound.mw} weight` : 'Weight unknown'}</div>
              <div className="text-[11px] mt-0.5">Chemical ID: {shortChemicalId(compound.smiles)}</div>
            </div>
            <div className="absolute top-2 right-2 text-[10px] px-2 py-0.5 rounded-full bg-white border border-forest-900/10 text-forest-700 dark:bg-white/10 dark:text-cream-100/70">
              From our plant library
            </div>
          </div>
        )}

        <div className="mt-4 grid grid-cols-4 gap-2">
          <div className="rounded-xl bg-cream-50 border border-forest-900/10 p-2 dark:bg-white/5">
            <div className="text-[9px] tracking-widest text-forest-700/60 dark:text-cream-100/50 uppercase">
              Oil–water mix
              <HowCalculated title="oil–water mix">A number describing whether the compound prefers oily or watery surroundings. It helps us guess how it might move around. It says nothing about health effects.</HowCalculated>
            </div>
            <div className="text-xs font-semibold text-forest-950 dark:text-cream-50 mt-0.5">{compound.logP ?? '—'}</div>
          </div>
          <div className="rounded-xl bg-cream-50 border border-forest-900/10 p-2 dark:bg-white/5">
            <div className="text-[9px] tracking-widest text-forest-700/60 dark:text-cream-100/50 uppercase">Exposed surface</div>
            <div className="text-xs font-semibold text-forest-950 dark:text-cream-50 mt-0.5">{compound.tpsa ?? '—'}</div>
          </div>
          <div className="rounded-xl bg-cream-50 border border-forest-900/10 p-2 dark:bg-white/5">
            <div className="text-[9px] tracking-widest text-forest-700/60 dark:text-cream-100/50 uppercase">Bonding spots</div>
            <div className="text-xs font-semibold text-forest-950 dark:text-cream-50 mt-0.5">{compound.hbd ?? '-'} / {compound.hba ?? '-'}</div>
          </div>
          <div className={`rounded-xl border p-2 ${balanceStyle} dark:bg-white/5`}>
            <div className="text-[9px] tracking-widest uppercase opacity-80">
              Balance score
              <HowCalculated title="balance score">One summary number (0–1) for how “well-rounded” the compound looks as a starting point for research. Higher is tidier — but it is not a health rating.</HowCalculated>
            </div>
            <div className="text-xs font-semibold mt-0.5">{balance ? balance.toFixed(2) : '—'}</div>
          </div>
        </div>

        {!compact && (
          <>
            <div className="mt-3 flex flex-wrap gap-1.5">
              {compound.traditionalUse && (
                <span className="inline-flex px-2.5 py-1 rounded-full bg-forest-50 border border-forest-600/15 text-[11px] text-forest-800 dark:bg-white/5 dark:text-cream-100/80">
                  Traditional use: {compound.traditionalUse}
                </span>
              )}
              {admet.giAbsorption && (
                <span className="inline-flex px-2.5 py-1 rounded-full bg-white border border-forest-900/10 text-[11px] text-forest-700 dark:bg-white/5 dark:text-cream-100/70">
                  Uptake: {admet.giAbsorption}
                </span>
              )}
              {dl.ruleOfFivePass !== undefined && (
                <span className={`inline-flex px-2.5 py-1 rounded-full text-[11px] border ${dl.ruleOfFivePass ? 'bg-forest-50 border-forest-200 text-forest-700' : 'bg-clay-100 border-clay-500/30 text-clay-700'}`}>
                  Passes {dl.lipinski ?? ''}/4 basic checks
                </span>
              )}
            </div>

            <div className="mt-4 flex items-center justify-between">
              <span className="text-[11px] text-forest-700/60 dark:text-cream-100/50">From the plant library · first step</span>
              <Link to={`/compounds/${compound.id}`} className="btn-secondary !px-4 !py-1.5 !text-xs">
                See details →
              </Link>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
