"""Frozen-input, single-pass prompt diagnostic; real API, no database dependencies."""
import argparse
import asyncio
import json
from pathlib import Path
from statistics import median
import time
from rag_poc.endpoints import JSONEndpoint, Builder
from rag_poc.builder_prompts import PROMPTS
from rag_poc.models import CATALOG_SCHEMA

class RecordingEndpoint:
    def __init__(self, endpoint):
        self.endpoint=endpoint
        self.raw=None
    async def call(self,*args):
        self.raw=await self.endpoint.call(*args)
        return self.raw

async def run(args):
    fixtures=json.loads(Path(args.cases).read_text())
    endpoint=JSONEndpoint.from_env()
    output={'boundary':'Development diagnostic; same catalog schema, not domain-transfer validation; one call per case/version',
        'model':endpoint.model,'thinking':endpoint.thinking,
        'system_prompts':{k:CATALOG_SCHEMA+v+'\nReturn only a valid JSON object.' for k,v in PROMPTS.items()},
        'cases':[]}
    try:
        for i,case in enumerate(fixtures):
            row={'id':case['id'],'input':case['input'],'expected':case['expected'],'arms':{}}
            # Alternate order to reduce systematic warmup/order bias; not randomized statistics.
            for version in (['v1','v2'] if i%2==0 else ['v2','v1']):
                recorder=RecordingEndpoint(endpoint)
                started=time.perf_counter()
                try:
                    x=case['input']
                    plan=await Builder(recorder,prompt_version=version).build(x['text'],x['confirmed_context'],x['previous_queries'],final=x['final'])
                    exp=case['expected']
                    correct=plan.action==exp['action']
                    if plan.query:
                        correct=correct and all(plan.query.json().get(k)==v for k,v in exp.get('query_fields',{}).items())
                    row['arms'][version]={'status':'ok','correct':correct,'raw_response':recorder.raw,
                        'plan':{'action':plan.action,'query':plan.query.json() if plan.query else None}}
                except Exception as exc:
                    row['arms'][version]={'status':'error','correct':False,'error_type':type(exc).__name__,'raw_response':recorder.raw}
                row['arms'][version]['elapsed_ms']=(time.perf_counter()-started)*1000
                row['arms'][version]['api_metrics']=dict(endpoint.metrics[-1])
            output['cases'].append(row)
            print(case['id'],{v:r['correct'] for v,r in row['arms'].items()},flush=True)
            Path(args.output).write_text(json.dumps(output,ensure_ascii=False,indent=2))
        output['summary']={v:{'correct':sum(c['arms'][v]['correct'] for c in output['cases']),
            'total':len(output['cases']), 'median_ms':median(c['arms'][v]['elapsed_ms'] for c in output['cases'])} for v in ['v1','v2']}
        Path(args.output).write_text(json.dumps(output,ensure_ascii=False,indent=2))
    finally:await endpoint.close()

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--cases',required=True);p.add_argument('--output',required=True)
    asyncio.run(run(p.parse_args()))
