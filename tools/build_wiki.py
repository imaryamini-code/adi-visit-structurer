"""Build the Markdown wiki: python3 -m tools.build_wiki --layout concept --out wiki_out/concept"""
import argparse
import json
from pathlib import Path

from src.wiki import LAYOUTS, build_wiki, check_provenance, load_records


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--layout", choices=LAYOUTS, required=True)
    ap.add_argument("--pred-dir", default="data/synthetic/pred")
    ap.add_argument("--raw-dir", default="data/synthetic/raw")
    ap.add_argument("--gold-dir", default="data/synthetic/gold", help="only used to map record -> patient_id")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    recs = load_records(Path(a.pred_dir), Path(a.raw_dir))
    patients = {}
    for rec, _ in recs:
        rid = rec["meta"]["record_id"]
        g = Path(a.gold_dir) / f"{rid}.json"
        if g.exists():
            patients[rid] = json.loads(g.read_text(encoding="utf-8")).get("patient", {}).get("patient_id", rid)
    files = build_wiki(recs, a.layout, Path(a.out), patients)
    rep = check_provenance(Path(a.out), [r["meta"]["record_id"] for r, _ in recs])
    print(f"{a.layout}: {len(files)} files -> {a.out} | provenance check: {rep}")


if __name__ == "__main__":
    main()
