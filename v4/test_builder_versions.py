import hashlib
import json
from types import SimpleNamespace
import pytest
from rag_poc.builder_prompts import PROMPTS
from rag_poc.endpoints import Builder
from rag_poc.models import CATALOG_SCHEMA
from builder_expanded_eval import main


def test_existing_prompts_remain_frozen():
    expected={'v1':'ccd0041030e6713b3d139055789ff10c9d523b55fefc49321539503ccd3fa7e6',
              'v2':'e780d1818008174c8fd0f1d34409271eeb51887592525606f7959cd21df232be'}
    assert {v:hashlib.sha256(PROMPTS[v].encode()).hexdigest() for v in expected} == expected


@pytest.mark.asyncio
async def test_prompt_selection_keeps_payload_and_default():
    calls=[]
    class Endpoint:
        async def call(self,role,system,payload):
            calls.append((role,system,payload))
            return {'action':'wait'}
    endpoint=Endpoint()
    context=[{'role':'user','content':'Previous entity'}]
    for version in ['v1','v2','v3']:
        await Builder(endpoint,prompt_version=version).build('stock?',context,[],final=True)
    await Builder(endpoint).build('stock?',context,[],final=True)
    assert [s for _,s,_ in calls[:3]] == [CATALOG_SCHEMA+PROMPTS[v] for v in ['v1','v2','v3']]
    assert all(payload==calls[0][2] for _,_,payload in calls)
    assert calls[-1]==calls[0]


@pytest.mark.asyncio
@pytest.mark.parametrize('versions',[[],['v2','v2'],['unknown']])
async def test_bad_version_selection_fails_before_output_or_api(tmp_path,versions):
    out=tmp_path/'output'
    with pytest.raises(ValueError,match='distinct known'):
        await main(SimpleNamespace(versions=versions,cases=str(tmp_path/'nonexistent'),output_dir=str(out)))
    assert not out.exists()


@pytest.mark.asyncio
async def test_evaluator_uses_only_selected_versions(monkeypatch,tmp_path):
    import builder_expanded_eval as evaluator
    class Endpoint:
        model='fixture';thinking=None
        def __init__(self):self.metrics=[]
        async def call(self,*args):return {'action':'wait'}
        async def close(self):pass
    monkeypatch.setattr(evaluator.JSONEndpoint,'from_env',Endpoint)
    cases=tmp_path/'cases.json';out=tmp_path/'output'
    cases.write_text(json.dumps([dict(id='one',group='one',input=dict(text='um',confirmed_context=[],previous_queries=[],final=False),expected=dict(action='wait'))]))
    await main(SimpleNamespace(versions=['v2','v3'],cases=str(cases),output_dir=str(out)))
    rows=[json.loads(x) for x in (out/'results.jsonl').read_text().splitlines()]
    assert len(rows)==6 and {r['version'] for r in rows}=={'v2','v3'}
    assert set(json.loads((out/'prompts.json').read_text()))=={'v2','v3'}
    assert json.loads((out/'summary.json').read_text())['selected_versions']==['v2','v3']
