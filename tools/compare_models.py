"""Run a frozen, paired ADI comparison. Requires local Ollama for model conditions."""
from __future__ import annotations
import argparse
import hashlib
import json
import subprocess
import shutil
from datetime import datetime, timezone
from pathlib import Path
from src.evaluate import evaluate
import src.run_pipeline as pipeline
from src.run_pipeline import process_note, PIPELINE_VERSION
from src.wiki import load_records
from src.wiki_context import KnowledgeLayer

try:
    from src.llm_extract import SYSTEM_PROMPT, DEFAULT_OLLAMA_URL
except ImportError:
    SYSTEM_PROMPT, DEFAULT_OLLAMA_URL = None, 'http://localhost:11434'

RAW = Path('data/synthetic/raw')
GOLD = Path('data/synthetic/gold')

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def fingerprint(paths):
    return sha(b''.join(p.name.encode() + b'\0' + bytes.fromhex(sha(p.read_bytes())) for p in paths))

def ollama_info(model):
    import requests
    version = requests.get(f'{DEFAULT_OLLAMA_URL}/api/version', timeout=5).json()
    tags = requests.get(f'{DEFAULT_OLLAMA_URL}/api/tags', timeout=5).json()
    show = requests.post(f'{DEFAULT_OLLAMA_URL}/api/show', json={'model': model}, timeout=15).json()
    canonical = model if ':' in model else model + ':latest'
    matched = next((m for m in tags.get('models', []) if m.get('name') == canonical or m.get('model') == canonical), {})
    return {'server_version': version, 'model_digest': matched.get('digest'),
            'model_details': show.get('details'),
            'modelfile_sha256': sha(show.get('modelfile', '').encode()),
            'parameters': show.get('parameters'), 'template_sha256': sha(show.get('template', '').encode())}

def cname(mode, model, knowledge='none'):
    return f'{mode}{"" if knowledge == "none" else "+" + knowledge}_{model.replace(":", "_").replace("/", "_")}'

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--run-id', required=True, help='New directory name within experiments/')
    ap.add_argument('--models', nargs='+', default=['mistral', 'llama3.1:8b'])
    ap.add_argument('--gold-dir', type=Path, default=GOLD,
                    help='Versioned reference directory; default is the original synthetic gold')
    ap.add_argument('--modes', nargs='+', choices=['llm', 'hybrid', 'adaptive'], default=['llm', 'hybrid'])
    ap.add_argument('--knowledge', nargs='+', choices=['none', 'wiki', 'raw'], default=['none'],
                    help="Knowledge layer for LLM conditions: none (default), wiki (structured Markdown lines), "
                         "raw (conventional retrieval of sentences). Leave-one-out from --gold-dir.")
    ap.add_argument('--reuse-cache', type=Path,
                    help='Copy LLM answers from an earlier run (same prompt) so no-knowledge conditions are not recomputed')
    ap.add_argument('--raw-dir', type=Path, default=RAW,
                    help='Directory with the notes to process; default is the original synthetic notes. '
                         'Use data/synthetic/raw_messy for the untidy-writing stress test (same gold).')
    ap.add_argument('--extractors', choices=['v1', 'v2'], default='v1',
                    help='Rule extractors: v1 = original (default), v2 = improved reason/follow-up/problems rules')
    ap.add_argument('--rules-only', action='store_true', help='Reproduce the rules baseline without Ollama')
    ap.add_argument('--limit', type=int, help='Use the first N paired records for a small pilot')
    ap.add_argument('--resume', action='store_true', help='Continue an interrupted run without replacing predictions')
    ap.add_argument('--max-new', type=int, help='Stop after N new predictions per condition; resume later')
    args = ap.parse_args()
    if args.limit is not None and args.limit < 1 or args.max_new is not None and args.max_new < 1:
        ap.error('--limit and --max-new must be positive')
    if not args.run_id.replace('-', '').replace('_', '').isalnum():
        ap.error('run-id may contain letters, digits, - and _ only')
    raw = sorted(args.raw_dir.glob('ADI-*.txt'))
    gold = sorted(args.gold_dir.glob('ADI-*.json'))
    if not raw or [p.stem for p in raw] != [p.stem for p in gold]:
        ap.error('Raw and gold files must be paired and nonempty')
    if args.limit:
        raw, gold = raw[:args.limit], gold[:args.limit]
    root = Path('experiments') / args.run_id
    # One LLM answer per (prompt, model, note), shared by llm / hybrid / adaptive in this run.
    pipeline.LLM_CACHE_DIR = root / 'llm_cache'
    if args.reuse_cache and not args.reuse_cache.is_dir():
        ap.error(f'--reuse-cache not found: {args.reuse_cache}')
    layers = {}
    if set(args.knowledge) - {'none'}:
        reference = load_records(args.gold_dir, RAW)  # reviewed reference + its raw notes
        layers = {kn: KnowledgeLayer(reference, kn) for kn in args.knowledge if kn != 'none'}
    if args.resume:
        if not (root / 'manifest.json').exists():
            ap.error('Cannot resume: run manifest not found')
        manifest = json.loads((root / 'manifest.json').read_text())
        if (manifest['raw_fingerprint_sha256'] != fingerprint(raw) or
                manifest['gold_fingerprint_sha256'] != fingerprint(gold) or
                manifest.get('prompt_sha256') != (sha(SYSTEM_PROMPT.encode()) if SYSTEM_PROMPT else None)):
            ap.error('Cannot resume: dataset or prompt changed')
        if manifest.get('extractors', 'v1') != args.extractors:
            ap.error('Cannot resume with a different --extractors version')
        if set(manifest['conditions']) - {'rules'} - {
            cname(mode, model, kn)
            for model in args.models for mode in args.modes for kn in args.knowledge
        }:
            ap.error('Cannot resume with a different model list')
    else:
        root.mkdir(parents=True, exist_ok=False)
    if args.reuse_cache and not (root / 'llm_cache').exists():  # after the run dir exists
        shutil.copytree(args.reuse_cache, root / 'llm_cache')
    if not args.rules_only and SYSTEM_PROMPT is None:
        ap.error('Install requirements.txt before model comparisons')
    if SYSTEM_PROMPT is not None and not args.resume:
        (root / 'prompt.txt').write_text(SYSTEM_PROMPT + '\n', encoding='utf-8')
    if not args.resume:
        manifest = {'created_utc': datetime.now(timezone.utc).isoformat(),
                'commit': subprocess.run(['git', 'rev-parse', 'HEAD'], capture_output=True, text=True).stdout.strip(),
                'working_tree_changes': subprocess.run(['git', 'status', '--short'], capture_output=True, text=True).stdout.strip(),
                'source_sha256': {str(p): sha(p.read_bytes()) for p in
                                  [Path('src/run_pipeline.py'), Path('src/extract_rules.py'),
                                   Path('src/llm_extract.py'), Path('src/normalize.py'),
                                   Path('src/evaluate.py'), Path('src/schema.py'),
                                   Path('src/routing.py'), Path('src/wiki.py'), Path('src/wiki_context.py'),
                                   Path('src/extractors_v2.py'),
                                   Path('tools/compare_models.py')]},
                'extractors': args.extractors,
                'pipeline_version': PIPELINE_VERSION, 'dataset': 'synthetic, gold-first; see docs/DATASET.md',
                'gold_dir': str(args.gold_dir),
                'raw_count': len(raw), 'raw_fingerprint_sha256': fingerprint(raw),
                'gold_fingerprint_sha256': fingerprint(gold),
                'prompt_sha256': sha(SYSTEM_PROMPT.encode()) if SYSTEM_PROMPT else None,
                'ollama_url': DEFAULT_OLLAMA_URL,
                'llm_options': {'temperature': 0.0, 'stream': False, 'max_retries': 1},
                'llm_cache': 'llm_cache/<model>/<sha256(prompt+model+note)>.json; modes share one answer per note',
                'conditions': {}}
        (root / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    selected_gold = root / 'selected_gold'
    selected_gold.mkdir(exist_ok=True)
    for p in gold:
        target = selected_gold / p.name
        if not target.exists():
            shutil.copyfile(p, target)
    conditions = [('rules', None, 'none')] if args.rules_only else [('rules', None, 'none')] + [
        (mode, model, kn) for model in args.models for mode in args.modes for kn in args.knowledge]
    for mode, model, kn in conditions:
        name = 'rules' if model is None else cname(mode, model, kn)
        info = manifest['conditions'].get(name, {'mode': mode, 'model': model})
        if kn != 'none':
            info['knowledge'] = {'kind': kn, 'source': str(args.gold_dir), 'leave_one_out': True,
                                 'entries': len(layers[kn].entries), 'fingerprint_sha256': layers[kn].fingerprint(),
                                 'k': layers[kn].k, 'per_concept': layers[kn].per_concept, 'max_chars': layers[kn].max_chars}
        manifest['conditions'][name] = info
        (root / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
        if model and 'ollama' not in info:
            info['ollama'] = ollama_info(model)  # Fail loudly if model or service unavailable.
        pred_dir = root / name / 'predictions'
        pred_dir.mkdir(parents=True, exist_ok=True)
        new_count = 0
        for p in raw:
            target = pred_dir / f'{p.stem}.json'
            if target.exists():
                continue
            if args.max_new is not None and new_count >= args.max_new:
                break
            note = p.read_text(encoding='utf-8')
            ctx = layers[kn].context(pipeline.PREPROCESS(note), p.stem) if kn != 'none' else ''
            record = process_note(note, p.stem, mode, model or 'mistral', require_llm=True, context=ctx,
                                  extractors=args.extractors)
            target.write_text(json.dumps(record, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
            new_count += 1
        completed = len(list(pred_dir.glob('ADI-*.json')))
        if completed != len(raw):
            print(f'{name}: {completed}/{len(raw)} saved; use --resume to continue', flush=True)
            continue
        metrics = evaluate(selected_gold, pred_dir)
        (root / name / 'metrics.json').write_text(json.dumps(metrics, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
        info['metrics'] = metrics
        (root / 'manifest.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
        print(f'{name}: reason={metrics["reason_accuracy"]:.3f}, vitals={metrics["vitals_exact_record_accuracy"]:.3f}', flush=True)
    print(f'Progress saved to {root}')

if __name__ == '__main__':
    main()
