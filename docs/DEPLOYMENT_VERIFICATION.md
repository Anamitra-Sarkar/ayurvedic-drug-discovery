# Deployment Verification

**Initial deploy**: 2026-09-22. **Last re-verified live**: 2026-09-25.

## Live URLs

- **Frontend**: https://ayurvedic-drug-discovery.vercel.app (Vercel, production)
- **Backend API**: https://bhumika-tewari-282006-ayurvedic-drug-discovery-backend.hf.space
  (Hugging Face Space, Docker SDK, bhumika's account, public)
- **API docs**: https://bhumika-tewari-282006-ayurvedic-drug-discovery-backend.hf.space/docs
- **Trained model**: `bhumika-tewari-282006/ayurvedic-drug-discovery-affinity-model` on
  Hugging Face (public)
- **Training dataset**: `bhumika-tewari-282006/ayurvedic-affinity-training-data` on
  Hugging Face (public)
- **Source code**: GitHub, Anamitra's account (public)

## Verification performed (cumulative, across multiple live-testing sessions)

- `GET /api/pipeline/targets` returns real target data (10 real protein targets,
  real PDB IDs, binding sites, disease associations) — confirmed via direct `curl`.
- Frontend (`/`) and backend `/docs` both return HTTP 200; `VITE_API_BASE` points at
  the real backend, not a mock/relative path.
- **A real end-to-end pipeline run** (`POST /api/pipeline/run`) was exercised through
  the live deployed frontend in an actual browser, not just curled — timed at ~70
  seconds real wall-clock for the full database → cheminformatics → docking →
  interaction → ML → XAI → literature → validation → report chain, and confirmed
  reaching a real "Done" state with real results.
- **3D structure viewer**: confirmed rendering real RDKit-embedded ligand geometry and
  a real RCSB crystal structure (not a hardcoded placeholder molecule) for more than
  one compound/target pair, including all four display styles (sticks/balls/lines/
  ribbons) genuinely changing what's rendered.
- **ML prediction**: confirmed a real trained-model prediction round-trip (real
  `pKd`, real applicability-domain check, real SHAP-based feature attribution) through
  the deployed frontend for multiple compounds.
- **Literature/RAG**: confirmed real Groq-LLM-generated answers with real citation
  grounding (including a case where the model correctly refused to answer because its
  corpus had no information on the queried compound, rather than fabricating a
  response) — the answer's markdown (headings, bold/italic, tables, chemistry
  sup/sub notation) renders correctly in the UI, not as raw markdown syntax.
- **Shortlist/ranking view**: confirmed real, distinct per-candidate docking scores
  and real compound data; confirmed the view honestly labels ML/literature columns as
  "not computed for this shortlist" rather than showing a fabricated-looking zero,
  since that endpoint only runs the database+docking tiers for a bulk ranked list.
- **Mobile-width rendering**: a real narrow-viewport screenshot (browser DevTools
  docked, ~410px) surfaced a genuine CSS Grid intrinsic-sizing bug causing page
  content to be clipped off-screen; root-caused and fixed (`min-width: 0` on cards and
  their grid-item wrappers), and the fix's presence was confirmed in the live deployed
  CSS bundle.
- HF Space Docker build completes successfully on HF's own infrastructure (RDKit,
  scikit-learn, PLIP-adjacent tooling all installed) and reaches `RUNNING`.
- CI (`.github/workflows/ci.yml`) has stayed green across every commit in the most
  recent multi-session round of live-bug-fixing (one real build break — a stray
  block-comment-closing token in a JSDoc comment — was caught by CI/the Vercel build
  log and fixed the same session before it could stay broken).

## Known, honest constraints (not bugs)

- The HF Space is on the free CPU-only tier and can go to sleep after a period of
  inactivity; the first request after a sleep period takes noticeably longer while it
  restarts. Confirmed recovering to `RUNNING` within about a minute of a wake-up
  request.
- Real AutoDock Vina docking depends on the Vina binary being present at runtime on
  the Space; when it genuinely isn't, `DockingAgent` falls back to an honestly-labelled
  empirical scoring heuristic (`execution.mock_used: true` in the API response) rather
  than fabricating a real-Vina-looking result. This is a documented, transparent
  fallback, not a hidden mock.
- A full pipeline run takes ~60-90s on this hosting tier; the frontend's request
  timeout for that specific call was raised to accommodate it (see git history on
  `frontend/src/services/api.js`).

## Follow-ups not yet done

- A live mobile-viewport re-check on a real device (this session's browser-automation
  environment could not actually narrow its own rendered viewport, so the CSS fix
  above was verified by direct cause analysis and by inspecting the deployed CSS
  bundle, not by a literal narrow-screen screenshot).
- `/candidates/rank`'s bulk ranking endpoint intentionally does not run ML/XAI/
  literature per candidate (too slow for a list of up to 11); if a fuller shortlist
  view is wanted later, that is a deliberate scope decision to revisit, not an
  oversight.
