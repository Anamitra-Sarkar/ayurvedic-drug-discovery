/**
 * Landing.jsx — "/" plain-language hero + feature highlights.
 * First thing anyone sees. No jargon.
 */
import { Link } from 'react-router-dom';
import { Page } from '../components/ui.jsx';

function HeroArt() {
  return (
    <div className="hero-pattern relative overflow-hidden rounded-[2rem] leaf-shape">
      <div className="absolute inset-0 flex items-center justify-end pr-10 opacity-90" aria-hidden="true">
        <div className="hidden md:block text-[120px] animate-float-slow select-none">🌿</div>
      </div>
      <div className="absolute inset-0 bg-gradient-to-r from-forest-950/60 via-forest-950/20 to-transparent" />
    </div>
  );
}

const FEATURES = [
  { icon: '🌿', title: 'Explore nature’s library', text: 'Browse beloved Ayurvedic plants — Ashwagandha, Turmeric, Amla — and meet the natural compounds inside them.' },
  { icon: '🧩', title: 'See how shapes fit', text: 'Watch a 3D preview of how a compound sits inside a protein shape, with a simple match-strength meter.' },
  { icon: '💡', title: 'Understand every guess', text: 'Each result shows its working, its confidence level, and the published papers behind it — in plain words.' },
  { icon: '🌼', title: 'Honest from the start', text: 'Everything here is an early computer guess for research. We say so clearly, on every page.' },
];

const STEPS = [
  { n: '1', title: 'Pick a plant or compound', text: 'Start with something familiar, like Turmeric.' },
  { n: '2', title: 'Run a guided check', text: 'We walk the compound through six gentle steps.' },
  { n: '3', title: 'Read a plain summary', text: 'See the shortlist, the “why”, and what to read next.' },
];

export default function Landing() {
  return (
    <Page>
      {/* Hero */}
      <section className="relative overflow-hidden rounded-[2rem] bg-forest-950 text-cream-50">
        <div className="hero-pattern absolute inset-0" aria-hidden="true" />
        <div className="relative grid gap-8 p-6 sm:p-8 md:grid-cols-2 md:p-14 items-center min-h-[480px]">
          <div className="min-w-0">
            <span className="inline-flex items-center gap-2 rounded-full border border-cream-50/25 bg-white/10 px-3.5 py-1.5 text-[11px] tracking-widest uppercase">
              🌱 Rooted in Ayurveda · guided by computers
            </span>
            <h1 className="font-display text-3xl sm:text-4xl md:text-[3.4rem] font-semibold leading-[1.05] mt-5 break-words">
              Discover promising natural compounds, <span className="text-gold-300">gently explained.</span>
            </h1>
            <p className="mt-5 max-w-lg text-[15px] leading-relaxed text-cream-100/85">
              Discover promising natural compounds from Ayurvedic medicine using computer simulations.
              Search familiar plants, preview 3D shape fits, and read honest, plain-word summaries of what the computer found.
            </p>
            <div className="mt-8 flex flex-col sm:flex-row sm:flex-wrap gap-3">
              <Link to="/compounds" className="inline-flex w-full sm:w-auto items-center justify-center gap-2 rounded-full bg-gold-400 px-7 py-3.5 text-sm font-bold text-forest-950 transition hover:bg-gold-300 hover:shadow-lift active:scale-[0.97]">
                Explore Compounds →
              </Link>
              <Link to="/pipeline" className="inline-flex w-full sm:w-auto items-center justify-center gap-2 rounded-full border border-cream-50/30 px-7 py-3.5 text-sm font-semibold text-cream-50 transition hover:bg-white/10 active:scale-[0.97]">
                Run an Analysis
              </Link>
            </div>
            <p className="mt-5 text-xs text-cream-100/60">Free to explore · no account needed · research previews only</p>
          </div>
          <HeroArt />
        </div>
      </section>

      {/* Features */}
      <section className="mt-10">
        <h2 className="font-display text-2xl md:text-3xl font-semibold text-forest-950 dark:text-cream-50 text-center">Made to feel simple, built to stay honest</h2>
        <p className="text-center text-sm text-forest-700/75 dark:text-cream-100/65 mt-2 max-w-xl mx-auto">Every screen translates the science into everyday words — while keeping the real numbers one tap away for the curious.</p>
        <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {FEATURES.map((f) => (
            <div key={f.title} className="card card-lift p-6">
              <div className="text-3xl">{f.icon}</div>
              <h3 className="font-display text-[17px] font-semibold text-forest-950 dark:text-cream-50 mt-3">{f.title}</h3>
              <p className="text-sm text-forest-800/80 dark:text-cream-100/70 mt-2 leading-relaxed">{f.text}</p>
            </div>
          ))}
        </div>
      </section>

      {/* How it works strip */}
      <section className="mt-10 card p-8 md:p-10">
        <h2 className="font-display text-2xl font-semibold text-forest-950 dark:text-cream-50">Three easy steps</h2>
        <div className="mt-5 grid gap-4 md:grid-cols-3">
          {STEPS.map((s) => (
            <div key={s.n} className="rounded-2xl bg-cream-50 border border-forest-900/10 p-5 dark:bg-white/5">
              <div className="flex h-9 w-9 items-center justify-center rounded-full bg-forest-700 font-display font-bold text-white">{s.n}</div>
              <h3 className="font-semibold text-forest-950 dark:text-cream-50 mt-3">{s.title}</h3>
              <p className="text-sm text-forest-800/75 dark:text-cream-100/65 mt-1">{s.text}</p>
            </div>
          ))}
        </div>
        <div className="mt-6 flex flex-wrap gap-3">
          <Link to="/compounds" className="btn-primary">Get Started — Explore Compounds</Link>
          <Link to="/about" className="btn-secondary">How should I read results?</Link>
        </div>
      </section>

      {/* Honesty strip */}
      <section className="mt-6 rounded-[2rem] border border-gold-300/60 bg-gold-50 p-6 md:p-8 text-center dark:bg-gold-400/10 dark:border-gold-400/30">
        <div className="text-2xl">🌼</div>
        <p className="mt-2 text-sm leading-relaxed text-forest-900/85 dark:text-cream-100/85 max-w-2xl mx-auto">
          Results are computer predictions for research purposes only — not health or medical advice.
          Promising on screen still means unproven in real life. Always talk to a qualified professional about health decisions.
        </p>
        <Link to="/ranking" className="link-underline mt-3 inline-block text-sm font-semibold text-forest-800 dark:text-gold-300">See this week’s shortlist →</Link>
      </section>
    </Page>
  );
}
