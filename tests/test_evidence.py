
import sys, pathlib
BASE = pathlib.Path(__file__).parent.parent
sys.path.insert(0, str(BASE / "backend"))

def test_tier_enum_exists():
    try:
        from app.core.evidence.tiers import EvidentiaryTier
    except ImportError:
        from app.core.evidence import EvidenceTier as EvidentiaryTier
    assert len(list(EvidentiaryTier)) == 5
    names = [e.value for e in EvidentiaryTier]
    assert "DATABASE_DERIVED" in names
    assert "DOCKING_RESULT" in names
    assert "ML_PREDICTION" in names
    assert "XAI_INTERPRETATION" in names
    assert "LITERATURE_EVIDENCE" in names

def test_tiered_evidence_wrapper():
    try:
        from app.core.evidence.tiers import EvidentiaryTier, TieredEvidence
        ev = TieredEvidence(tier=EvidentiaryTier.DOCKING_RESULT, data={"score": -7.5}, source="test")
        assert ev.tier == EvidentiaryTier.DOCKING_RESULT
        assert ev.clinical_proof is False
        d = ev.to_dict()
        assert "evidentiary_tier" in d
    except ImportError:
        from app.core.evidence import EvidenceTier, EvidenceTaggedOutput
        ev = EvidenceTaggedOutput(tier=EvidenceTier.DOCKING_RESULT, data={"score": -7.5})
        assert ev.tier == EvidenceTier.DOCKING_RESULT

def test_clinical_claim_blocked():
    try:
        from app.core.evidence.tiers import EvidentiaryTier, validate_no_clinical_claim
        validate_no_clinical_claim({"data": {"score": -7.5}})
        try:
            validate_no_clinical_claim({"data": "clinically proven effective against COVID-19"})
            assert False
        except ValueError as e:
            assert "FORBIDDEN CLAIM" in str(e) or "clinical proof" in str(e).lower()
    except ImportError:
        from app.core.evidence import EvidenceTaggedOutput, EvidenceTier
        ev = EvidenceTaggedOutput(tier=EvidenceTier.DOCKING_RESULT, data={"claim": "clinically proven"})
        try:
            ev.assert_not_clinical()
            assert False
        except ValueError:
            pass

def test_imppat_sample_tier_label():
    import json
    imppat_path = BASE / "backend/app/data/imppat_sample.json"
    with open(imppat_path) as f:
        data = json.load(f)
    assert len(data) == 100
    for entry in data[:5]:
        assert entry['evidence_tier'] == 1
        assert entry['evidence_tier_label'] == "database-derived information"

def test_all_five_tiers_in_sample_output():
    import json
    out_path = BASE / "examples/sample_output.json"
    with open(out_path) as f:
        out = json.load(f)
    assert "tier_1_database_derived" in out
    assert "tier_2_docking_result" in out
    assert "tier_3_ml_prediction" in out
    assert "tier_4_xai_interpretation" in out
    assert "tier_5_literature_derived" in out
    for key in ["tier_1_database_derived","tier_2_docking_result","tier_3_ml_prediction","tier_4_xai_interpretation","tier_5_literature_derived"]:
        assert "evidentiary_tier" in out[key]
        assert "disclaimer" in out[key]
        assert "clinically proven" not in json.dumps(out[key]).lower()
