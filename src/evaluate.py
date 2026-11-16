"""Score saved predictions against synthetic gold: python3 -m src.evaluate --pred-dir PATH."""
from __future__ import annotations
import argparse
import json
import re
from pathlib import Path
from src.normalize import normalize_interventions, normalize_problems, normalize_reason

VITALS = ('blood_pressure_systolic', 'blood_pressure_diastolic', 'heart_rate', 'temperature', 'spo2')

def follow_up_key(value):
    if isinstance(value, dict):
        return (value.get('type'), value.get('timing_days'))
    if not isinstance(value, str) or not value.strip():
        return (None, None)
    s = value.lower()
    kind = ('controllo_ferita' if 'ferit' in s or 'lesion' in s else
            'ricontatto_telefonico' if 'telefon' in s or 'ricontatt' in s else
            'controllo' if 'controll' in s else 'other')
    match = re.search(r'\b(?:tra|fra|in|entro)\s+(\d+)\s+giorn', s)
    days = int(match.group(1)) if match else (7 if 'prossima settimana' in s else None)
    return (kind, days)

def label_counts(gold_sets, predicted_sets):
    tp = sum(len(g & p) for g, p in zip(gold_sets, predicted_sets))
    fp = sum(len(p - g) for g, p in zip(gold_sets, predicted_sets))
    fn = sum(len(g - p) for g, p in zip(gold_sets, predicted_sets))
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    return {'micro_precision': precision, 'micro_recall': recall,
            'micro_f1': 2 * precision * recall / (precision + recall) if precision + recall else 0.0,
            'tp': tp, 'fp': fp, 'fn': fn}

def evaluate(gold_dir: Path, pred_dir: Path):
    gold = {p.stem: json.loads(p.read_text(encoding='utf-8')) for p in gold_dir.glob('ADI-*.json')}
    pred = {p.stem: json.loads(p.read_text(encoding='utf-8')) for p in pred_dir.glob('ADI-*.json')}
    if not gold or set(gold) != set(pred):
        raise ValueError(f'Paired dataset required: gold={len(gold)}, predictions={len(pred)}, '
                         f'missing={sorted(set(gold)-set(pred))[:5]}, extra={sorted(set(pred)-set(gold))[:5]}')
    ids = sorted(gold)
    reasons = followups = vital_all = 0
    vital_correct = {k: 0 for k in VITALS}
    interventions_g, interventions_p, problems_g, problems_p = [], [], [], []
    errors = []
    for rid in ids:
        g, p = gold[rid], pred[rid]
        gc, pc = g['clinical'], p['clinical']
        gr, pr = normalize_reason(gc.get('reason_for_visit')), normalize_reason(pc.get('reason_for_visit'))
        reasons += gr == pr
        followups += follow_up_key(gc.get('follow_up')) == follow_up_key(pc.get('follow_up'))
        gv, pv = gc.get('vitals') or {}, pc.get('vitals') or {}
        matches = {k: gv.get(k) == pv.get(k) for k in VITALS}
        vital_all += all(matches.values())
        for k in VITALS:
            vital_correct[k] += matches[k]
        interventions_g.append(set(normalize_interventions(gc.get('interventions'))))
        interventions_p.append(set(normalize_interventions(pc.get('interventions'))))
        problems_g.append(set(normalize_problems(g.get('coding', {}).get('problems_normalized', []))))
        problems_p.append(set(normalize_problems(p.get('coding', {}).get('problems_normalized', []))))
        if not (gr == pr and all(matches.values())):
            errors.append({'record_id': rid, 'reason_gold': gr, 'reason_pred': pr,
                           'vital_mismatches': [k for k in VITALS if not matches[k]]})
    n = len(ids)
    return {'records': n, 'reason_accuracy': reasons / n,
            'follow_up_type_timing_accuracy': followups / n,
            'vitals_exact_record_accuracy': vital_all / n,
            'vitals_field_accuracy': {k: vital_correct[k] / n for k in VITALS},
            'interventions': label_counts(interventions_g, interventions_p),
            'problems': label_counts(problems_g, problems_p),
            'error_examples': errors[:20],
            'method': 'Missing-vs-missing counts correct for exact-match fields; multi-label F1 is micro-averaged; follow-up compares type and timing.'}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--gold-dir', type=Path, default=Path('data/synthetic/gold'))
    parser.add_argument('--pred-dir', type=Path, default=Path('data/synthetic/pred'))
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    rendered = json.dumps(evaluate(args.gold_dir, args.pred_dir), indent=2, ensure_ascii=False)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + '\n', encoding='utf-8')
    print(rendered)

if __name__ == '__main__':
    main()
