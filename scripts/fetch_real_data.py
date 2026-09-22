"""Fetch REAL data from public no-auth APIs for the Ayurvedic drug discovery repo.

Meant to run inside GitHub Actions (or any environment with internet access)
as ``python3 scripts/fetch_real_data.py`` from the repo root with no arguments.

Sources:
  1. PubChem PUG-REST -- compound enrichment for every distinct
     ``phytochemical_name`` in ``backend/app/data/imppat_sample.json``.
  2. RCSB PDB -- real structure files + metadata for every ``pdb_id`` in
     ``backend/app/data/proteins/targets.json``.
  3. Europe PMC -- literature verification for reference titles parsed out of
     ``docs/REFERENCES.md``.

NEVER invents data: if a request fails, the failure is logged (logging module)
and recorded in the output files (``unresolved`` / ``status: failed`` /
``match_plausible: false`` + note). No placeholder / fabricated values are
substituted. Each individual network call is wrapped in try/except so one
failure never crashes the whole run.

Outputs (created under ``data/raw/`` relative to the repo root):
  - ``data/raw/pubchem/pubchem_enrichment.json``
  - ``data/raw/pdb/{PDB_ID}.pdb`` + ``data/raw/pdb/PROVENANCE.json``
  - ``data/raw/literature/europepmc_verification.json``

Only the Python standard library is used (urllib, json, time, re, pathlib,
datetime, logging).
"""

from __future__ import annotations

import datetime
import json
import logging
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
log = logging.getLogger("fetch_real_data")

ROOT = Path(__file__).resolve().parent.parent  # repo root (scripts/ -> root)

IMPPAT_PATH = ROOT / "backend" / "app" / "data" / "imppat_sample.json"
TARGETS_PATH = ROOT / "backend" / "app" / "data" / "proteins" / "targets.json"
REFERENCES_PATH = ROOT / "docs" / "REFERENCES.md"

PUBCHEM_DIR = ROOT / "data" / "raw" / "pubchem"
PDB_DIR = ROOT / "data" / "raw" / "pdb"
LIT_DIR = ROOT / "data" / "raw" / "literature"

PUBCHEM_OUT = PUBCHEM_DIR / "pubchem_enrichment.json"
PDB_PROVENANCE_OUT = PDB_DIR / "PROVENANCE.json"
LIT_OUT = LIT_DIR / "europepmc_verification.json"

REQUEST_TIMEOUT = 30
POLITENESS_DELAY = 1.0
MAX_RETRIES_ON_BUSY = 4
USER_AGENT = "ayurvedic-drug-discovery-fetch/1.0 (github-actions; contact: repo-maintainer)"

STOPWORDS = {
    "the", "and", "for", "with", "from", "into", "onto", "using", "based",
    "study", "review", "database", "drug", "drugs", "discovery", "novel",
    "human", "crystal", "structure", "complex", "bound", "protein", "receptor",
}


def utc_now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def _http_get_once(url: str, timeout: int) -> tuple[int | None, bytes | None, str | None]:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "*/*"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read(), None
    except urllib.error.HTTPError as exc:
        try:
            body = exc.read()
        except Exception:  # noqa: BLE001
            body = None
        return exc.code, body, f"HTTPError {exc.code}: {exc.reason}"
    except urllib.error.URLError as exc:
        return None, None, f"URLError: {exc.reason}"
    except Exception as exc:  # noqa: BLE001 - never let one call crash the run
        return None, None, f"{type(exc).__name__}: {exc}"


def http_get(url: str, timeout: int = REQUEST_TIMEOUT) -> tuple[int | None, bytes | None, str | None]:
    """GET a URL with stdlib urllib. Returns (status, body, error).

    Retries with exponential backoff on HTTP 503 (server busy) - a retry is
    honest (same real endpoint, deferred), unlike substituting fabricated data.
    """
    attempt = 0
    while True:
        status, body, err = _http_get_once(url, timeout)
        if status == 503 and attempt < MAX_RETRIES_ON_BUSY:
            wait = 2 ** attempt * 2
            log.info("HTTP 503 (server busy), retrying in %ds (attempt %d/%d): %s", wait, attempt + 1, MAX_RETRIES_ON_BUSY, url)
            time.sleep(wait)
            attempt += 1
            continue
        return status, body, err


def http_get_json(url: str, timeout: int = REQUEST_TIMEOUT):
    """GET a URL and parse the body as JSON. Returns (data, error).

    503 retry-with-backoff is handled inside http_get() itself.
    """
    status, body, err = http_get(url, timeout=timeout)
    if err is not None and body is None:
        return None, err
    if status is not None and status >= 400:
        detail = ""
        if body:
            try:
                detail = " " + body[:200].decode("utf-8", errors="replace")
            except Exception:  # noqa: BLE001
                detail = ""
        return None, f"{err or ('HTTP ' + str(status))}{detail}"
    try:
        return json.loads((body or b"").decode("utf-8", errors="replace")), None
    except Exception as exc:  # noqa: BLE001
        return None, f"JSON decode error: {exc}"


def significant_words(text: str) -> list[str]:
    words = re.findall(r"[a-z0-9]+", text.lower())
    return [w for w in words if len(w) >= 4 and w not in STOPWORDS]


def titles_plausibly_match(expected: str, actual: str) -> bool:
    """Lenient sanity check: share at least 2 significant words, or 1 long one."""
    exp_words = significant_words(expected or "")
    if not exp_words:
        return False
    actual_lower = (actual or "").lower()
    hits = [w for w in exp_words if w in actual_lower]
    if len(hits) >= 2:
        return True
    if any(len(w) >= 8 for w in hits):
        return True
    # Short titles (e.g. "RDKit cheminformatics"): a single solid word hit is enough.
    if len(exp_words) <= 2 and len(hits) >= 1:
        return True
    return False


# ---------------------------------------------------------------------------
# Source 1: PubChem
# ---------------------------------------------------------------------------

def load_compound_names() -> list[str]:
    with open(IMPPAT_PATH, "r", encoding="utf-8") as fh:
        records = json.load(fh)
    names: list[str] = []
    seen: set[str] = set()
    for rec in records:
        if not isinstance(rec, dict):
            continue
        name = rec.get("phytochemical_name")
        if not name or not str(name).strip():
            continue
        name = str(name).strip()
        if name not in seen:
            seen.add(name)
            names.append(name)
    return names


def fetch_pubchem_for_name(name: str):
    encoded = urllib.parse.quote(name, safe="")
    url = (
        "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/"
        f"{encoded}/property/CanonicalSMILES,MolecularFormula,MolecularWeight,IUPACName/JSON"
    )
    data, err = http_get_json(url)
    if err is not None:
        return None, err
    try:
        props = data["PropertyTable"]["Properties"][0]
    except (KeyError, IndexError, TypeError) as exc:
        return None, f"No properties in PubChem response: {exc}"
    smiles = props.get("CanonicalSMILES") or props.get("ConnectivitySMILES")
    if props.get("CID") is None or not smiles:
        return None, "PubChem response missing CID or SMILES"
    return {
        "query_name": name,
        "pubchem_cid": props.get("CID"),
        "canonical_smiles": smiles,
        "molecular_formula": props.get("MolecularFormula"),
        "molecular_weight": props.get("MolecularWeight"),
        "iupac_name": props.get("IUPACName"),
    }, None


def run_pubchem() -> tuple[int, int]:
    PUBCHEM_DIR.mkdir(parents=True, exist_ok=True)
    names = load_compound_names()
    log.info("PubChem: %d distinct compound names to enrich", len(names))
    resolved: list[dict] = []
    unresolved: list[dict] = []
    for i, name in enumerate(names):
        try:
            entry, err = fetch_pubchem_for_name(name)
        except Exception as exc:  # noqa: BLE001 - keep going no matter what
            entry, err = None, f"{type(exc).__name__}: {exc}"
        if entry is not None:
            resolved.append(entry)
            log.info("PubChem OK (%d/%d): %s -> CID %s", i + 1, len(names), name, entry["pubchem_cid"])
        else:
            unresolved.append({"query_name": name, "error": err})
            log.warning("PubChem FAILED (%d/%d): %s: %s", i + 1, len(names), name, err)
        time.sleep(POLITENESS_DELAY)
    # NOTE: the task asks for "a JSON list" of resolved entries *plus* a
    # top-level "unresolved" key. A bare JSON list cannot carry a key, so the
    # file is a JSON object whose "results" key holds exactly that list.
    payload = {
        "results": resolved,
        "unresolved": unresolved,
        "retrieved_at": utc_now_iso(),
        "source": "PubChem PUG-REST",
    }
    with open(PUBCHEM_OUT, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)
    log.info("PubChem: wrote %d resolved + %d unresolved to %s", len(resolved), len(unresolved), PUBCHEM_OUT)
    return len(resolved), len(unresolved)


# ---------------------------------------------------------------------------
# Source 2: RCSB PDB
# ---------------------------------------------------------------------------

def run_pdb() -> tuple[int, int]:
    PDB_DIR.mkdir(parents=True, exist_ok=True)
    with open(TARGETS_PATH, "r", encoding="utf-8") as fh:
        targets = json.load(fh)
    log.info("PDB: %d targets to fetch", len(targets))
    provenance: list[dict] = []
    ok = 0
    failed = 0
    for entry in targets:
        pdb_id = str(entry.get("pdb_id", "")).strip()
        protein_name = str(entry.get("protein_name", "")).strip()
        if not pdb_id:
            log.warning("PDB: skipping entry with missing pdb_id: %r", entry)
            provenance.append({
                "pdb_id": pdb_id,
                "protein_name_expected": protein_name,
                "title_from_rcsb": None,
                "release_date": None,
                "file_size_bytes": None,
                "retrieved_at": utc_now_iso(),
                "title_match_ok": False,
                "status": "failed",
                "error": "missing pdb_id in targets.json entry",
            })
            failed += 1
            continue
        pdb_id_upper = pdb_id.upper()
        pdb_url = f"https://files.rcsb.org/download/{pdb_id_upper}.pdb"
        meta_url = f"https://data.rcsb.org/rest/v1/core/entry/{pdb_id_upper}"
        title: str | None = None
        release_date = None
        file_size = None
        error: str | None = None
        try:
            status, body, err = http_get(pdb_url)
            if err is not None or body is None:
                raise RuntimeError(f"structure download failed: {err or 'empty body'}")
            out_path = PDB_DIR / f"{pdb_id_upper}.pdb"
            with open(out_path, "wb") as fh:
                fh.write(body)
            file_size = len(body)
            log.info("PDB OK: %s (%d bytes)", pdb_id_upper, file_size)
        except Exception as exc:  # noqa: BLE001
            error = f"{type(exc).__name__}: {exc}"
            log.warning("PDB structure FAILED for %s: %s", pdb_id_upper, error)
        try:
            meta, meta_err = http_get_json(meta_url)
            if meta_err is not None:
                raise RuntimeError(f"metadata fetch failed: {meta_err}")
            struct = (meta or {}).get("struct", {}) if isinstance(meta, dict) else {}
            title = struct.get("title") if isinstance(struct, dict) else None
            acc = (meta or {}).get("rcsb_accession_info", {}) if isinstance(meta, dict) else {}
            release_date = acc.get("initial_release_date") if isinstance(acc, dict) else None
            log.info("PDB metadata OK: %s title=%r", pdb_id_upper, title)
        except Exception as exc:  # noqa: BLE001
            meta_error = f"{type(exc).__name__}: {exc}"
            error = f"{error}; {meta_error}" if error else meta_error
            log.warning("PDB metadata FAILED for %s: %s", pdb_id_upper, meta_error)
        if error is not None:
            provenance.append({
                "pdb_id": pdb_id_upper,
                "protein_name_expected": protein_name,
                "title_from_rcsb": title,
                "release_date": release_date,
                "file_size_bytes": file_size,
                "retrieved_at": utc_now_iso(),
                "title_match_ok": False,
                "status": "failed",
                "error": error,
            })
            failed += 1
            continue
        match_ok = titles_plausibly_match(protein_name, title or "")
        if not match_ok:
            log.warning(
                "PDB title mismatch? pdb_id=%s expected=%r rcsb_title=%r",
                pdb_id_upper, protein_name, title,
            )
        provenance.append({
            "pdb_id": pdb_id_upper,
            "protein_name_expected": protein_name,
            "title_from_rcsb": title,
            "release_date": release_date,
            "file_size_bytes": file_size,
            "retrieved_at": utc_now_iso(),
            "title_match_ok": match_ok,
            "status": "ok",
        })
        ok += 1
    with open(PDB_PROVENANCE_OUT, "w", encoding="utf-8") as fh:
        json.dump(provenance, fh, indent=2)
    log.info("PDB: wrote provenance for %d ok + %d failed to %s", ok, failed, PDB_PROVENANCE_OUT)
    return ok, failed


# ---------------------------------------------------------------------------
# Source 3: Europe PMC
# ---------------------------------------------------------------------------

def extract_reference_titles() -> list[tuple[int, str | None, str]]:
    """Parse numbered entries out of REFERENCES.md.

    Returns [(ref_number, title_or_None, raw_entry_text)]. Entries without a
    clearly extractable title get None and are recorded downstream with a note.
    """
    text = REFERENCES_PATH.read_text(encoding="utf-8")
    # Entries look like "[N] ...text...". Split on lines starting with [N].
    parts = re.split(r"(?m)^\[(\d+)\]\s*", text)
    # parts = [preamble, num1, body1, num2, body2, ...]
    results: list[tuple[int, str | None, str]] = []
    for idx in range(1, len(parts) - 1, 2):
        try:
            num = int(parts[idx])
        except ValueError:
            continue
        body = parts[idx + 1].strip()
        raw = body
        # Collapse newlines, strip markdown emphasis.
        flat = re.sub(r"\s+", " ", body).replace("*", "").strip()
        if not flat:
            results.append((num, None, raw))
            continue
        # Title heuristic: first sentence-like chunk before ". <Year or Capital>".
        # Take text up to the first period followed by space; require it to look
        # like a real title (>= 4 words, has letters).
        title: str | None = None
        chunks = re.split(r"\.\s+", flat)
        for chunk in chunks:
            chunk = chunk.strip().rstrip(".")
            if len(chunk.split()) >= 4 and re.search(r"[A-Za-z]", chunk):
                # Skip chunks that are just years or journal boilerplate.
                if re.fullmatch(r"[\d,\-\s]+", chunk):
                    continue
                title = chunk
                break
        if title is None:
            log.warning("REFERENCES: no extractable title for [%d]; skipping query", num)
        results.append((num, title, raw))
    results.sort(key=lambda t: t[0])
    return results


def fetch_europepmc_for_title(title: str):
    encoded = urllib.parse.quote(title, safe="")
    url = (
        "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
        f"?query={encoded}&format=json&pageSize=1"
    )
    data, err = http_get_json(url)
    if err is not None:
        return None, err
    try:
        results = data["resultList"]["result"]
        if not results:
            return None, "no results returned by Europe PMC"
        return results[0], None
    except (KeyError, IndexError, TypeError) as exc:
        return None, f"unexpected Europe PMC response shape: {exc}"


def run_literature() -> tuple[int, int]:
    LIT_DIR.mkdir(parents=True, exist_ok=True)
    refs = extract_reference_titles()
    log.info("Europe PMC: %d references parsed from REFERENCES.md", len(refs))
    out: list[dict] = []
    ok = 0
    failed = 0
    for num, title, _raw in refs:
        if not title:
            out.append({
                "ref_number": num,
                "original_ref_title": None,
                "matched_title": None,
                "doi": None,
                "pmid": None,
                "pub_year": None,
                "match_plausible": False,
                "note": f"no clearly extractable title for reference [{num}]; skipped query, not guessed",
            })
            failed += 1
            continue
        try:
            top, err = fetch_europepmc_for_title(title)
        except Exception as exc:  # noqa: BLE001
            top, err = None, f"{type(exc).__name__}: {exc}"
        if top is None or not isinstance(top, dict):
            out.append({
                "ref_number": num,
                "original_ref_title": title,
                "matched_title": None,
                "doi": None,
                "pmid": None,
                "pub_year": None,
                "match_plausible": False,
                "note": f"Europe PMC query failed or returned nothing: {err}",
            })
            log.warning("Europe PMC FAILED [%d] %r: %s", num, title, err)
            failed += 1
        else:
            matched = top.get("title")
            plausible = titles_plausibly_match(title, str(matched or ""))
            out.append({
                "ref_number": num,
                "original_ref_title": title,
                "matched_title": matched,
                "doi": top.get("doi"),
                "pmid": top.get("pmid"),
                "pub_year": top.get("pubYear"),
                "match_plausible": plausible,
            })
            log.info("Europe PMC (%s) [%d] %r -> %r", "match" if plausible else "weak", num, title, matched)
            if plausible:
                ok += 1
            else:
                failed += 1
        time.sleep(POLITENESS_DELAY)
    with open(LIT_OUT, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2)
    log.info("Europe PMC: wrote %d plausible + %d failed/unclear to %s", ok, failed, LIT_OUT)
    return ok, failed


# ---------------------------------------------------------------------------

def main() -> None:
    pub_ok, pub_fail = run_pubchem()
    pdb_ok, pdb_fail = run_pdb()
    lit_ok, lit_fail = run_literature()
    summary = (
        "\n===== fetch_real_data summary =====\n"
        f"PubChem (compounds):      {pub_ok} resolved, {pub_fail} unresolved\n"
        f"RCSB PDB (targets):       {pdb_ok} downloaded, {pdb_fail} failed\n"
        f"Europe PMC (references):  {lit_ok} plausibly matched, {lit_fail} failed/unclear\n"
        "==================================="
    )
    print(summary)


if __name__ == "__main__":
    main()
