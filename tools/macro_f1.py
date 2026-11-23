"""Macro-F1 (over the labels of the gold) and micro-F1 for interventions and problems, from saved predictions (no model calls).

Run from the repository root:  python3 -m tools.macro_f1
"""
import json,sys,collections
from pathlib import Path
sys.path.insert(0,'.')
from src.normalize import normalize_interventions, normalize_problems
G=Path('data/synthetic/gold'); ids=sorted(p.stem for p in G.glob('ADI-*.json'))
gold={i:json.loads((G/f'{i}.json').read_text()) for i in ids}
def sets(d,kind):
    out={}
    for i in ids:
        if kind=='int': out[i]=set(normalize_interventions(d[i]['clinical'].get('interventions')))
        else: out[i]=set(normalize_problems(d[i].get('coding',{}).get('problems_normalized',[])))
    return out
def prf(tp,fp,fn):
    p=tp/(tp+fp) if tp+fp else 0; r=tp/(tp+fn) if tp+fn else 0
    return 2*p*r/(p+r) if p+r else 0
runs=[('Rules','experiments/full_01/rules'),('LLM only, Mistral','experiments/full_01/llm_mistral'),('LLM only, Llama','experiments/full_01/llm_llama3.1_8b'),('Adaptive, Mistral','experiments/full_01/adaptive_mistral'),('Adaptive, Llama','experiments/full_01/adaptive_llama3.1_8b')]
for kind,name in (('int','Interventions'),('prob','Problems')):
    g=sets(gold,kind); support=collections.Counter(l for s in g.values() for l in s)
    print(f'\n{name}: {len(support)} labels in gold; support: {dict(support.most_common())}')
    for label,path in runs:
        pred={i:json.loads((Path(path)/'predictions'/f'{i}.json').read_text()) for i in ids}
        p=sets(pred,kind)
        labels=sorted(set(support)|{l for s in p.values() for l in s})
        per={}
        for l in labels:
            tp=sum(l in g[i] and l in p[i] for i in ids); fp=sum(l not in g[i] and l in p[i] for i in ids); fn=sum(l in g[i] and l not in p[i] for i in ids)
            per[l]=(tp,fp,fn,prf(tp,fp,fn))
        gl=[l for l in labels if support[l]>0]
        macro_gold=sum(per[l][3] for l in gl)/len(gl)
        TP=sum(v[0] for v in per.values());FP=sum(v[1] for v in per.values());FN=sum(v[2] for v in per.values())
        spurious=[l for l in labels if support[l]==0]
        print(f'  {label:20s} micro {prf(TP,FP,FN):.3f}  macro (gold labels, {len(gl)}) {macro_gold:.3f}  labels never found: {[l for l in gl if per[l][0]==0]}  predicted but not in gold: {spurious}')
