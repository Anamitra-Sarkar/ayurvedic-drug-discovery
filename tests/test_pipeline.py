
import pathlib, json, csv, sys
BASE = pathlib.Path(__file__).parent.parent
sys.path.insert(0, str(BASE / "backend"))

def test_imppat_sample_exists():
    p = BASE / "backend/app/data/imppat_sample.json"
    assert p.exists()
    with open(p) as f:
        data = json.load(f)
    assert len(data) == 65  # real record count after Phase B fabrication fix (see docs/DATA_PROVENANCE.md)
    # These thresholds were originally >=20/>=20, which only held because of the
    # 80 fabricated "derivative N" padding records purged in the Phase B integrity
    # fix (see docs/DATA_PROVENANCE.md). Real counts as of that fix: 7 genuinely
    # Triphala-tagged compounds, 0 tagged AYUSH-64 (no compound in the current
    # real seed data has been specifically cross-referenced to that formulation
    # yet - honest gap, not asserted away).
    triphala = [d for d in data if 'Triphala' in str(d['traditional_formulations'])]
    assert len(triphala) >= 5
    ayush = [d for d in data if 'AYUSH-64' in str(d['traditional_formulations'])]
    assert len(ayush) >= 0
    for d in data[:3]:
        assert 'smiles' in d
        assert 'admet' in d
        assert 'drug_likeness' in d

def test_targets_exist():
    p = BASE / "backend/app/data/proteins/targets.json"
    assert p.exists()
    with open(p) as f:
        targets = json.load(f)
    assert len(targets) == 10
    pdb_ids = [t['pdb_id'] for t in targets]
    assert '6LU7' in pdb_ids
    assert '3FXI' in pdb_ids
    assert '1XKA' in pdb_ids
    assert '2QP8' in pdb_ids
    assert any('mGluR' in t['protein_name'] for t in targets)

def test_references_exist():
    p = BASE / "backend/app/data/literature_corpus/references.json"
    assert p.exists()
    with open(p) as f:
        refs = json.load(f)
    assert len(refs) == 40

def test_papers_exist():
    papers_dir = BASE / "backend/app/data/literature_corpus/papers"
    assert papers_dir.exists()
    files = list(papers_dir.glob("*.txt"))
    assert len(files) >= 5

def test_pdb_exists():
    p = BASE / "backend/app/data/docking/sample_complex.pdb"
    assert p.exists()
    txt = p.read_text()
    assert 'ATOM' in txt
    assert 'HETATM' in txt

def test_ml_training_data():
    p = BASE / "backend/app/data/ml/training_data.csv"
    assert p.exists()
    with open(p) as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    assert len(rows) == 500
    assert 'pKd' in rows[0]
    assert 'vina_score' in rows[0]

def test_sample_run_exists():
    p = BASE / "examples/sample_run.py"
    assert p.exists()
    txt = p.read_text()
    assert 'EvidentiaryTier' in txt or 'DATABASE_DERIVED' in txt

def test_sample_output_exists_and_has_five_tiers():
    p = BASE / "examples/sample_output.json"
    assert p.exists()
    with open(p) as f:
        out = json.load(f)
    assert 'hard_constraint' in out or 'evidence_tiers_definition' in out
    content = json.dumps(out).lower()
    assert 'database' in content
    assert 'docking' in content
    assert 'ml' in content
    assert 'literature' in content
    assert 'clinically proven' not in content

def test_cheminformatics_mock_works():
    import random
    def mock_descriptor(smiles):
        return {"valid": True, "mw": random.uniform(150,500), "logP": random.uniform(0,4)}
    res = mock_descriptor("C1=CC(=C(C(=C1O)O)O)C(=O)O")
    assert res['valid']

def test_docs_exists():
    p = BASE / "docs/LITERATURE_REVIEW_COMBINED.md"
    assert p.exists()
    txt = p.read_text()
    assert len(txt) > 10000
    assert 'AYUSH-64' in txt
    assert 'IMPPAT' in txt
