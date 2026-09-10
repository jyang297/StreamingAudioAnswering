"""Frozen-input diagnostic: real local vectors versus exact and real DeepSeek LLM."""
import argparse
import asyncio
import json
from pathlib import Path
import time

from rag_poc.endpoints import JSONEndpoint, LLMChecker, ExactChecker
from rag_poc.models import Query
from rag_poc.semantic import LocalEmbeddings, SemanticChecker, MODEL, REPO, REVISION


def cases():
    # Query-level coverage under general catalog contents, not accidental current rows.
    specs = [
      ('identical', {'name':'Chai'}, {'name':'Chai'}, True),
      ('case_insensitive', {'name':'Chai'}, {'name':'chai'}, True),
      ('capitalized', {'name':'CHANG'}, {'name':'Chang'}, True),
      ('numeric_equivalent', {'min_price':10}, {'min_price':10.0}, True),
      ('entity', {'name':'Chai'}, {'name':'Chang'}, False),
      ('stock_polarity', {'in_stock':True}, {'in_stock':False}, False),
      ('discontinued_polarity', {'discontinued':True}, {'discontinued':False}, False),
      ('numeric_disjoint', {'max_price':10}, {'min_price':20}, False),
      ('narrow_candidate', {'min_price':20}, {'min_price':10}, False),
      ('category', {'category_id':1}, {'category_id':2}, False),
      ('sort', {'order':'price_asc','limit':5}, {'order':'price_desc','limit':5}, False),
      ('too_few', {'limit':5}, {'limit':10}, False),
    ]
    return [{'id':name, 'candidate':Query.parse(c).json(), 'final':Query.parse(f).json(),
             'expected_reuse':expected} for name,c,f,expected in specs]

async def main(args):
    endpoint=JSONEndpoint.from_env()
    embeddings=None
    output={'boundary':'Hand-labeled diagnostic, not a calibrated or held-out accuracy benchmark',
            'model':MODEL,'source':REPO,'revision':REVISION,'dimension':384,
            'similarity':'cosine of actual ONNX dense model outputs',
            'representation':'query_text; structured final/candidate only; no prefix',
            'vector_cache':'none; model load and warmup excluded from decision latency',
            'cases':[]}
    try:
        started=time.perf_counter()
        embeddings=LocalEmbeddings.load(args.embedding_cache)
        output['model_load_ms']=(time.perf_counter()-started)*1000
        started=time.perf_counter()
        await embeddings.encode(['Retrieve catalog products.'])
        output['warmup_ms']=(time.perf_counter()-started)*1000
        semantic=SemanticChecker(embeddings,threshold=.99) # diagnostic sweep, not deployment default
        checkers={'exact':ExactChecker(),'llm':LLMChecker(endpoint),'semantic':semantic}
        for case in cases():
            row={**case,'arms':{}}
            for name,checker in checkers.items():
                views=[{'id':1,'query':case['candidate'],'completed':True}]
                start=time.perf_counter()
                try:
                    # Final text generated deterministically from frozen query, same all arms.
                    selected=await checker.select('Retrieve catalog products using these final filters: '+json.dumps(case['final']),[],Query.parse(case['final']),views)
                    row['arms'][name]={'selected':selected,'elapsed_ms':(time.perf_counter()-start)*1000,
                                      'correct':(selected==1)==case['expected_reuse'],'status':'ok'}
                except Exception as exc:
                    row['arms'][name]={'status':'error','error_type':type(exc).__name__,'elapsed_ms':(time.perf_counter()-start)*1000}
            row['semantic_detail']=semantic.metrics[-1]
            output['cases'].append(row)
            print(json.dumps(row),flush=True)
        output['threshold_sweep']=[]
        for threshold in [.9,.95,.98,.99,.995,.999,.9999]:
            fp=fn=0
            for c in output['cases']:
                pred=c['semantic_detail']['scores'][0]['cosine']>=threshold
                fp+=int(pred and not c['expected_reuse'])
                fn+=int(not pred and c['expected_reuse'])
            output['threshold_sweep'].append({'threshold':threshold,'false_accept':fp,'false_reject':fn})
        output['llm_metrics']=endpoint.metrics
        Path(args.output).write_text(json.dumps(output,indent=2))
    finally:
        try:
            if embeddings: await embeddings.close()
        finally: await endpoint.close()

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--embedding-cache',default='/private/tmp/livekit-semantic-models')
    parser.add_argument('--output',required=True)
    asyncio.run(main(parser.parse_args()))
