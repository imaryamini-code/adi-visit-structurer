import json
from pathlib import Path

from src.normalize import normalize_interventions, normalize_reason
from src.schema import coerce_llm_output


def test_reviewed_reference_preserves_original_and_corrects_unsupported_labels():
    original = Path('data/synthetic/gold')
    reviewed = Path('data/synthetic/gold_reviewed_v1')
    assert len(list(reviewed.glob('ADI-*.json'))) == 100
    for rid in ('ADI-0002', 'ADI-0003', 'ADI-0004', 'ADI-0006'):
        before = json.loads((original / f'{rid}.json').read_text())
        after = json.loads((reviewed / f'{rid}.json').read_text())
        assert after != before
    assert json.loads((reviewed / 'ADI-0003.json').read_text())['coding']['problems_normalized'] == []
    for rid, removed in {
        'ADI-0018': 'febbre', 'ADI-0024': 'insonnia',
        'ADI-0050': 'dispnea', 'ADI-0097': 'insonnia',
    }.items():
        before = json.loads((original / f'{rid}.json').read_text())
        after = json.loads((reviewed / f'{rid}.json').read_text())
        assert removed in before['coding']['problems_normalized']
        assert removed not in after['coding']['problems_normalized']
    for number in range(9, 14):
        item = json.loads((reviewed / f'ADI-{number:04d}.json').read_text())
        assert item['meta']['visit_datetime'] == '2026-02-10T08:00:00'


def test_reason_equivalence_is_limited_to_same_clinical_intent():
    assert normalize_reason('valutazione delle condizioni generali') == normalize_reason('controllo generale')
    assert normalize_reason('valutazione sintomatologia generale') == normalize_reason('riferiti sintomi generali')
    assert normalize_reason('rivalutazione dolore') != normalize_reason('controllo parametri')


def test_italian_decimal_temperature_from_model_json():
    out = coerce_llm_output({'clinical': {'vitals': {'temperature': '37,1'}}})
    assert out['clinical']['vitals']['temperature'] == 37.1
    assert coerce_llm_output({'clinical': {'vitals': {'temperature': True}}})['clinical']['vitals']['temperature'] is None


def test_therapy_review_is_not_counted_as_drug_administration():
    assert 'somministrazione_farmaco' not in normalize_interventions(['controllo terapia'])
