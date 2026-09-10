import json

import httpx
import pytest

from rag_poc.endpoints import Answerer, Builder, JSONEndpoint, LLMChecker
from rag_poc.models import ContractError, Query


def endpoint(response):
    def handle(request):
        return httpx.Response(200, json={"choices": [{"message": {"content": json.dumps(response)}}]})
    client = httpx.AsyncClient(transport=httpx.MockTransport(handle))
    return JSONEndpoint(base_url="http://contract.test/v1", model="scripted", client=client), client


@pytest.mark.parametrize("data", [
    {"sql": "DROP TABLE northwind_products"}, {"limit": 1000}, {"limit": True},
    {"order": "price; DROP TABLE x"}, {"min_price": -1}, {"min_price": float("nan")},
    {"in_stock": "yes"}, {"category_id": True}, {"name": ""}, {"min_price": 9, "max_price": 1},
])
def test_query_contract_rejects_unsafe_or_unsupported_input(data):
    with pytest.raises(ContractError):
        Query.parse(data)


@pytest.mark.asyncio
async def test_builder_json_contract_and_request_shape():
    requests = []

    def handle(request):
        requests.append(json.loads(request.content))
        assert request.url.path == "/v1/chat/completions"
        assert request.headers["authorization"] == "Bearer test-only"
        return httpx.Response(200, json={"choices": [{"message": {"content":
            '{"action":"retrieve","query":{"name":"Chai","in_stock":true}}'}}]})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as client:
        ep = JSONEndpoint(base_url="http://contract.test/v1", model="fixture", api_key="test-only", client=client)
        plan = await Builder(ep).build("in stock?", [{"role": "user", "content": "Chai"}], [], final=True)
        assert plan.query == Query(name="Chai", in_stock=True)
        payload = json.loads(requests[0]["messages"][1]["content"])
        assert payload["final"] is True and payload["confirmed_context"][0]["content"] == "Chai"
        assert ep.metrics[0]["status"] == "ok"
        assert "test-only" not in str(ep.metrics)


@pytest.mark.asyncio
@pytest.mark.parametrize("bad_id", [999, "1", True])
async def test_checker_rejects_unknown_or_invalid_task_id(bad_id):
    ep, client = endpoint({"candidate_id": bad_id})
    try:
        with pytest.raises(ContractError):
            await LLMChecker(ep).select("Chai", [], Query(name="Chai"),
                [{"id": 1, "query": Query(name="Chai").json(), "completed": False}])
    finally:
        await client.aclose()


@pytest.mark.asyncio
async def test_answerer_validates_rewrite_and_budget():
    ep, client = endpoint({"action": "retrieve", "query": {"name": "Chai"}})
    try:
        action = await Answerer(ep).respond("Chai", [], [], can_rewrite=True)
        assert action["query"] == Query(name="Chai")
        with pytest.raises(ContractError):
            await Answerer(ep).respond("Chai", [], [], can_rewrite=False)
    finally:
        await client.aclose()


@pytest.mark.asyncio
async def test_malformed_endpoint_does_not_count_as_valid_output():
    async with httpx.AsyncClient(transport=httpx.MockTransport(lambda r: httpx.Response(
            200, json={"choices": [{"message": {"content": "not json"}}]}))) as client:
        ep = JSONEndpoint(base_url="http://contract.test/v1", model="scripted", client=client)
        with pytest.raises(ValueError):
            await Builder(ep).build("Chai", [], [], final=True)
        assert ep.metrics[0]["status"] == "error"


def test_no_implicit_endpoint(monkeypatch, tmp_path):
    monkeypatch.delenv("RAG_LLM_BASE_URL", raising=False)
    monkeypatch.delenv("RAG_LLM_MODEL", raising=False)
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    with pytest.raises(ValueError, match="Configure"):
        JSONEndpoint.from_env(env_file=tmp_path / "missing.env")


@pytest.mark.asyncio
async def test_deepseek_non_thinking_json_request(monkeypatch, tmp_path):
    monkeypatch.setenv("RAG_LLM_BASE_URL", "https://api.deepseek.com")
    monkeypatch.setenv("RAG_LLM_MODEL", "deepseek-v4-flash")
    monkeypatch.setenv("RAG_LLM_THINKING", "disabled")
    monkeypatch.setenv("RAG_LLM_API_KEY_ENV", "DEEPSEEK_API_KEY")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-only")
    def handle(request):
        body = json.loads(request.content)
        assert request.url.path == "/chat/completions"
        assert request.headers["authorization"] == "Bearer test-only"
        assert body["thinking"] == {"type": "disabled"}
        assert body["response_format"] == {"type": "json_object"}
        assert "JSON" in body["messages"][0]["content"]
        return httpx.Response(200, json={"choices": [{"finish_reason": "stop",
            "message": {"content": '{"action":"wait"}'}}]})
    ep = JSONEndpoint.from_env(env_file=tmp_path / "missing.env")
    await ep.close()
    async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as client:
        ep.client = client
        assert await ep.call("builder", "A query", {}) == {"action": "wait"}


@pytest.mark.asyncio
@pytest.mark.parametrize("content,reason", [("", "stop"), (None, "stop"), ('{}', "length")])
async def test_incomplete_output_rejected(content, reason):
    async with httpx.AsyncClient(transport=httpx.MockTransport(lambda r: httpx.Response(
            200, json={"choices": [{"finish_reason": reason, "message": {"content": content}}]}))) as client:
        ep = JSONEndpoint(base_url="http://contract.test", model="test", client=client)
        with pytest.raises(ContractError):
            await ep.call("checker", "JSON", {})
        assert ep.metrics[0]["status"] == "error"


@pytest.mark.asyncio
async def test_key_only_dotenv_and_environment_precedence(monkeypatch, tmp_path):
    for name in ("RAG_LLM_BASE_URL", "RAG_LLM_MODEL", "RAG_LLM_API_KEY_ENV", "RAG_LLM_THINKING", "DEEPSEEK_API_KEY"):
        monkeypatch.delenv(name, raising=False)
    config = tmp_path / ".env"
    config.write_text("DEEPSEEK_API_KEY='test-${literal}'\nRAG_LLM_MODEL=file-model\n")
    monkeypatch.setenv("RAG_LLM_MODEL", "process-model")
    ep = JSONEndpoint.from_env(env_file=config)
    try:
        assert ep.url == "https://api.deepseek.com/chat/completions"
        assert ep.model == "process-model"
        assert ep.api_key == "test-${literal}"
        assert ep.thinking == "disabled"
    finally:
        await ep.close()


@pytest.mark.asyncio
async def test_custom_endpoint_does_not_inherit_deepseek_secret(monkeypatch, tmp_path):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "deepseek-test-only")
    monkeypatch.setenv("RAG_LLM_BASE_URL", "https://other.example/v1")
    monkeypatch.setenv("RAG_LLM_MODEL", "other")
    for name in ("RAG_LLM_API_KEY_ENV", "RAG_LLM_API_KEY", "RAG_LLM_THINKING"):
        monkeypatch.delenv(name, raising=False)
    ep = JSONEndpoint.from_env(env_file=tmp_path / "missing.env")
    try:
        assert ep.api_key is None
        assert ep.thinking is None
    finally:
        await ep.close()

@pytest.mark.asyncio
async def test_cancelled_request_is_not_reported_as_api_failure():
    import asyncio
    async def handle(request):
        raise asyncio.CancelledError()
    async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as client:
        ep = JSONEndpoint(base_url="http://contract.test", model="test", client=client)
        with pytest.raises(asyncio.CancelledError):
            await ep.call("builder", "JSON", {})
        assert ep.metrics[0]["status"] == "cancelled"
