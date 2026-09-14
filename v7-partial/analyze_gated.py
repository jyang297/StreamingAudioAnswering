"""Describe retrieval diagnostics without treating candidate agreement as accuracy."""
import json
from pathlib import Path
import statistics
import sys


def analyze(root):
    rows = [json.loads(x) for x in (root/'results.jsonl').read_text().splitlines()]
    timings = [json.loads(x) for x in (root/'timing.jsonl').read_text().splitlines()]
    out = {'timings': {}, 'by_snapshot': {}, 'exact_cache_replay': {}}
    for stage in ('model_load', 'index_embedding', 'query_embedding', 'cosine_search', 'builder_llm', 'snapshot_total', 'length_gate'):
        values = sorted(r['elapsed_ms'] for r in timings if r['step'] == stage)
        if values:
            out['timings'][stage] = {'n': len(values), 'median_ms': statistics.median(values),
                 'p95_nearest_rank_ms': values[max(0, __import__('math').ceil(len(values)*.95)-1)]}
    for step in range(4):
        selected = [r for r in rows if r['snapshot'] == step]
        out['by_snapshot'][step] = {'n': len(selected),
             'gated': sum(r['status'] == 'gated' for r in selected),
             'wait': sum(r.get('builder', {}).get('action') == 'wait' for r in selected),
             'search': sum(r.get('builder', {}).get('action') == 'search' for r in selected),
             'error': sum(r['status'] == 'error' for r in selected)}
        exact = [r for r in selected if r['kind'] == 'exact-cache-replay']
        out['exact_cache_replay'][step] = {'n': len(exact), **{arm: {
              'searched': sum(bool(r.get(arm)) for r in exact),
              'target_top1': sum(bool(r.get(arm)) and r[arm][0]['id'] == r['target_id'] for r in exact),
              'target_top3': sum(any(c['id'] == r['target_id'] for c in r.get(arm, [])) for r in exact)
              } for arm in ('raw', 'normalized')}}
    out.pop('exact_cache_replay', None)
    out['boundary'] = 'Long/compound text diagnostics; no semantic hit labels or measured voice latency savings.'
    (root/'analysis.json').write_text(json.dumps(out, indent=2)+'\n')
    lines = ['# Builder output review', '', 'AI-authored diagnostic export; semantic judgments require reading each row.', '']
    for r in rows:
        lines.extend([f"## {r['case']} / snapshot {r['snapshot']}",
                      f"Input: {r['payload']['text']}",
                      'Context: '+json.dumps(r['payload']['confirmed_context'], ensure_ascii=False),
                      'Builder: '+json.dumps(r.get('builder', {'gate': r.get('gate'), 'status': r['status']}), ensure_ascii=False),
                      'Raw top candidate: '+json.dumps(r.get('raw', [None])[0], ensure_ascii=False),
                      'Normalized top candidate: '+json.dumps(r.get('normalized', [None])[0], ensure_ascii=False), ''])
    (root/'output-review.md').write_text('\n\n'.join(lines)+'\n')
    print(json.dumps(out, indent=2))


if __name__ == '__main__':
    analyze(Path(sys.argv[1]))
