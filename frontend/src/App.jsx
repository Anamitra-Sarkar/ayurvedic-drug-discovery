/**
 * App.jsx — routing, persistent header/footer. Plain-language consumer UI.
 * Routes: / (landing) · /compounds · /compounds/:id · /targets · /pipeline
 *         /results/:id · /ranking · /network · /about + /docs
 * Legacy /compound/:id and /dashboard redirect to their new homes.
 */
import { useEffect, useState } from 'react';
import { BrowserRouter, Routes, Route, NavLink, Link, Navigate, useLocation } from 'react-router-dom';
import Landing from './pages/Landing.jsx';
import Compounds from './pages/Compounds.jsx';
import CompoundDetail from './pages/CompoundDetail.jsx';
import Targets from './pages/Targets.jsx';
import PipelineRun from './pages/PipelineRun.jsx';
import Results from './pages/Results.jsx';
import Ranking from './pages/Ranking.jsx';
import Network from './pages/Network.jsx';
import Documentation from './pages/Documentation.jsx';

const NAV = [
  { to: '/compounds', label: 'Compounds' },
  { to: '/targets', label: 'Protein shapes' },
  { to: '/pipeline', label: 'Run Analysis' },
  { to: '/ranking', label: 'Shortlist' },
  { to: '/network', label: 'Plant map' },
  { to: '/about', label: 'About' },
];

function ScrollToTop() {
  const { pathname } = useLocation();
  useEffect(() => { window.scrollTo({ top: 0, behavior: 'instant' }); }, [pathname]);
  return null;
}

function useDarkMode() {
  const [dark, setDark] = useState(() => {
    try { return localStorage.getItem('ayur-theme') === 'dark'; } catch { return false; }
  });
  useEffect(() => {
    document.documentElement.classList.toggle('dark', dark);
    try { localStorage.setItem('ayur-theme', dark ? 'dark' : 'light'); } catch { /* ignore */ }
  }, [dark]);
  return [dark, setDark];
}

function Layout({ children }) {
  const [dark, setDark] = useDarkMode();
  const [menuOpen, setMenuOpen] = useState(false);
  const location = useLocation();

  useEffect(() => { setMenuOpen(false); }, [location.pathname]);

  return (
    <div className="min-h-screen bg-cream-50 text-forest-950 dark:bg-forest-950 dark:text-cream-50 transition-colors duration-300">
      {/* Gentle research notice */}
      <div className="bg-gradient-to-r from-gold-100 via-cream-100 to-gold-100 dark:from-forest-900 dark:via-forest-800 dark:to-forest-900 border-b border-gold-300/50 dark:border-white/10">
        <p className="mx-auto max-w-[1400px] px-4 md:px-6 py-2 text-center text-[11px] md:text-xs text-forest-800 dark:text-cream-100/75">
          🌼 <strong>Research previews only:</strong> computer guesses for study — not health or medical advice.
        </p>
      </div>

      <header className="sticky top-0 z-40 border-b border-forest-900/10 bg-cream-50/90 backdrop-blur dark:bg-forest-950/90 dark:border-white/10">
        <div className="mx-auto max-w-[1400px] px-4 md:px-6 h-[68px] flex items-center justify-between gap-3">
          <Link to="/" className="flex items-center gap-3 group">
            <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-forest-700 text-xl text-white shadow-card transition group-hover:scale-105 group-active:scale-95">🌿</div>
            <div>
              <div className="font-display font-bold text-[17px] leading-none">AyurDiscovery</div>
              <div className="text-[10px] tracking-[0.18em] uppercase text-forest-700/60 dark:text-cream-100/50 mt-1">Nature · Science · Clarity</div>
            </div>
          </Link>

          <nav className="hidden lg:flex items-center gap-1" aria-label="Main">
            {NAV.map((link) => (
              <NavLink
                key={link.to}
                to={link.to}
                className={({ isActive }) => `rounded-full px-4 py-2 text-sm font-medium transition active:scale-[0.97] ${isActive ? 'bg-forest-700 text-white shadow-card' : 'text-forest-800 hover:bg-forest-700/10 dark:text-cream-100 dark:hover:bg-white/10'}`}
              >
                {link.label}
              </NavLink>
            ))}
          </nav>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setDark(!dark)}
              className="rounded-full border border-forest-900/10 bg-white px-3 py-2 text-sm transition hover:shadow-card active:scale-95 dark:bg-white/10 dark:border-white/10"
              aria-label={dark ? 'Switch to light mode' : 'Switch to dark mode'}
              title={dark ? 'Light mode' : 'Dark mode'}
            >
              {dark ? '☀️' : '🌙'}
            </button>
            <Link to="/compounds" className="btn-primary !px-5 !py-2.5 hidden sm:inline-flex">Get Started</Link>
            <button
              className="lg:hidden rounded-full border border-forest-900/10 bg-white px-3.5 py-2 text-sm dark:bg-white/10 dark:border-white/10"
              onClick={() => setMenuOpen(!menuOpen)}
              aria-expanded={menuOpen}
              aria-label="Open menu"
            >
              {menuOpen ? '✕' : '☰'}
            </button>
          </div>
        </div>

        {menuOpen && (
          <nav className="modal-panel lg:hidden border-t border-forest-900/10 bg-cream-50 px-4 py-3 dark:bg-forest-950 dark:border-white/10" aria-label="Mobile">
            <div className="grid gap-1">
              {[{ to: '/', label: 'Home' }, ...NAV].map((link) => (
                <NavLink
                  key={link.to}
                  to={link.to}
                  className={({ isActive }) => `rounded-2xl px-4 py-3 text-sm font-medium transition ${isActive ? 'bg-forest-700 text-white' : 'hover:bg-forest-700/10 dark:hover:bg-white/10'}`}
                >
                  {link.label}
                </NavLink>
              ))}
            </div>
          </nav>
        )}
      </header>

      <main className="mx-auto max-w-[1400px] px-4 md:px-6 py-6 md:py-8">
        {children}
      </main>

      <footer className="border-t border-forest-900/10 bg-white/70 mt-12 dark:bg-white/5 dark:border-white/10">
        <div className="mx-auto max-w-[1400px] px-4 md:px-6 py-8 grid gap-6 md:grid-cols-3">
          <div>
            <div className="flex items-center gap-2">
              <span className="flex h-8 w-8 items-center justify-center rounded-xl bg-forest-700 text-white">🌿</span>
              <span className="font-display font-bold">AyurDiscovery</span>
            </div>
            <p className="mt-2 text-xs leading-relaxed text-forest-800/70 dark:text-cream-100/60">
              Helping curious minds explore Ayurvedic plants with honest, plain-word computer previews.
            </p>
          </div>
          <nav className="flex flex-wrap gap-x-5 gap-y-2 text-sm" aria-label="Footer">
            {NAV.map((l) => (
              <Link key={l.to} to={l.to} className="text-forest-800 hover:text-forest-950 dark:text-cream-100/70 dark:hover:text-cream-50 transition">{l.label}</Link>
            ))}
          </nav>
          <div className="rounded-2xl border border-gold-300/60 bg-gold-50 p-4 dark:bg-gold-400/10 dark:border-gold-400/30">
            <div className="text-[10px] font-bold uppercase tracking-widest text-gold-700 dark:text-gold-300">Please remember 🌼</div>
            <p className="mt-1 text-xs leading-relaxed text-forest-900/85 dark:text-cream-100/80">
              Results are computer predictions for research purposes only, not medical advice.
              Nothing here is proven to work or to be safe — please talk to a qualified professional about health decisions.
            </p>
          </div>
        </div>
        <div className="border-t border-forest-900/10 dark:border-white/10">
          <p className="mx-auto max-w-[1400px] px-4 md:px-6 py-4 text-[11px] text-forest-700/60 dark:text-cream-100/50">
            © AyurDiscovery — early research previews · built with care from plant libraries, 3D shape checks and published papers.
          </p>
        </div>
      </footer>
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <ScrollToTop />
      <Layout>
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/compounds" element={<Compounds />} />
          <Route path="/compounds/:id" element={<CompoundDetail />} />
          <Route path="/targets" element={<Targets />} />
          <Route path="/pipeline" element={<PipelineRun />} />
          <Route path="/results/:id" element={<Results />} />
          <Route path="/ranking" element={<Ranking />} />
          <Route path="/network" element={<Network />} />
          <Route path="/about" element={<Documentation />} />
          <Route path="/docs" element={<Documentation />} />
          {/* legacy redirects */}
          <Route path="/compound/:id" element={<LegacyCompound />} />
          <Route path="/dashboard" element={<Navigate to="/compounds" replace />} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
}

function LegacyCompound() {
  const { pathname } = useLocation();
  return <Navigate to={pathname.replace('/compound/', '/compounds/')} replace />;
}

function NotFound() {
  return (
    <div className="card p-10 text-center page-wrap">
      <div className="text-4xl">🧭</div>
      <h1 className="font-display text-2xl font-semibold mt-3">Hmm, this path wandered off</h1>
      <p className="text-sm text-forest-700/70 dark:text-cream-100/60 mt-2">The page you’re looking for isn’t here — but the plant library is wide open.</p>
      <div className="mt-5 flex justify-center gap-2">
        <Link to="/" className="btn-primary">Back home</Link>
        <Link to="/compounds" className="btn-secondary">Explore compounds</Link>
      </div>
    </div>
  );
}
