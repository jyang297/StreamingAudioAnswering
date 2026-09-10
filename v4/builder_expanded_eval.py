"""Real-API expanded diagnostic with bounded concurrency and per-case evidence."""
import argparse,asyncio,json,random,time
from pathlib import Path
from collections import Counter,defaultdict
from statistics import median
from rag_poc.endpoints import JSONEndpoint,Builder
from rag_poc.builder_prompts import PROMPTS
from rag_poc.models import CATALOG_SCHEMA

def judge(plan,expected):
    if expected['action']=='wait':
        return 'appropriate_wait' if plan.action=='wait' else 'unjustified_retrieve'
    if plan.action=='wait':return 'missed_retrieve'
    for k,v in expected.get('query_fields',{}).items():
        actual=plan.query.json().get(k)
        if k=='name' and isinstance(actual,str) and isinstance(v,str):
            if actual.casefold()==v.casefold():continue
        if actual!=v:return 'wrong_query'
    # Unrequested order/limit differences can be harmless or alter coverage;
    # do not silently count them as proven-correct or as unsafe entity errors.
    fields=expected.get('query_fields',{})
    if any(k not in fields and plan.query.json()[k] != default for k,default in [('order','product_id'),('limit',10)]):
        return 'query_variant_review'
    return 'correct_retrieve' 

async def main(args):
    versions=getattr(args, 'versions', ['v1','v2'])
    if not versions or len(set(versions)) != len(versions) or any(v not in PROMPTS for v in versions):
        raise ValueError('Choose distinct known prompt versions')
    cases=json.loads(Path(args.cases).read_text())
    out=Path(args.output_dir);out.mkdir(parents=True,exist_ok=False)
    (out/'cases.json').write_text(json.dumps(cases,ensure_ascii=False,indent=2))
    (out/'prompts.json').write_text(json.dumps({k:CATALOG_SCHEMA+v+'\nReturn only a valid JSON object.' for k,v in PROMPTS.items() if k in versions},ensure_ascii=False,indent=2))
    # One sentinel per group has two extra repeats. Counts kept separate from 100 unique cases.
    sentinels={}
    for c in cases:sentinels.setdefault(c['group'],c['id'])
    jobs=[(c,v,repeat) for c in cases for repeat in range(3 if c['id'] in sentinels.values() else 1) for v in versions]
    random.Random(20260910).shuffle(jobs)
    semaphore=asyncio.Semaphore(2)
    results=[]
    async def work(case,version,repeat):
        async with semaphore:
            # Independent metric collection per request; no shared-last-entry race.
            ep=JSONEndpoint.from_env();raw=None
            class Capture:
                async def call(self,*a):
                    nonlocal raw
                    raw=await ep.call(*a);return raw
            start=time.perf_counter()
            row={'id':case['id'],'group':case['group'],'version':version,'repeat':repeat,'model':ep.model,'thinking':ep.thinking}
            try:
                x=case['input']
                plan=await Builder(Capture(),prompt_version=version).build(x['text'],x['confirmed_context'],x['previous_queries'],final=x['final'])
                row.update(outcome=judge(plan,case['expected']),plan={'action':plan.action,'query':plan.query.json() if plan.query else None})
            except Exception as e:row.update(outcome='api_or_contract_error',error_type=type(e).__name__)
            finally:
                row.update(raw_response=raw,elapsed_ms=(time.perf_counter()-start)*1000,api_metrics=ep.metrics)
                await ep.close()
            results.append(row)
            with (out/'results.jsonl').open('a') as f:f.write(json.dumps(row,ensure_ascii=False)+'\n')
            if len(results)%20==0:print(f'{len(results)}/{len(jobs)} completed',flush=True)
    await asyncio.gather(*(work(*job) for job in jobs))
    primary=[r for r in results if r['repeat']==0]
    summary={'unique_cases':len(cases),'requests':len(jobs),'selected_versions':versions,'concurrency':2,'shuffle_seed':20260910,
             'repeats_per_sentinel':3,'boundary':'AI-authored development cases in one schema; not held-out production accuracy', 'versions':{},'groups':{},'sentinel_outcome_changes':[]}
    for v in versions:
        rows=[r for r in primary if r['version']==v]
        summary['versions'][v]={'outcomes':dict(Counter(r['outcome'] for r in rows)),'median_ms':median(r['elapsed_ms'] for r in rows)}
        summary['groups'][v]={g:dict(Counter(r['outcome'] for r in rows if r['group']==g)) for g in sentinels}
        for caseid in sentinels.values():
            rr=sorted([r for r in results if r['version']==v and r['id']==caseid],key=lambda r:r['repeat'])
            if len({r['outcome'] for r in rr})>1:summary['sentinel_outcome_changes'].append({'id':caseid,'version':v,'outcomes':[r['outcome'] for r in rr]})
    (out/'summary.json').write_text(json.dumps(summary,indent=2))
    print(json.dumps(summary['versions']),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--cases',required=True);p.add_argument('--output-dir',required=True)
    p.add_argument('--versions',nargs='+',choices=sorted(PROMPTS),default=['v1','v2'])
    asyncio.run(main(p.parse_args()))
