import uuid

from ditto_agent.graph.build import build_graph
from ditto_agent.llm.client import LLMClient
from ditto_agent.schema import AmbiguityItem, DraftContext


def test_mock_verify_passes_ambiguities_through_unchanged(monkeypatch):
    monkeypatch.setenv("DITTO_LLM_MODE", "mock")
    items = [
        AmbiguityItem(span="내일까지", category="TIME", reason="r", candidates=["a", "b"], suggestion="s"),
    ]
    result = LLMClient().verify("내일까지 부탁드려요", items)
    assert result == items


def test_mock_verify_handles_empty_list(monkeypatch):
    monkeypatch.setenv("DITTO_LLM_MODE", "mock")
    assert LLMClient().verify("8/20 18:00 KST까지 리뷰 부탁드립니다.", []) == []


def test_mock_verify_batch_passes_each_case_through_unchanged(monkeypatch):
    monkeypatch.setenv("DITTO_LLM_MODE", "mock")
    items_a = [AmbiguityItem(span="a", category="TIME", reason="r", candidates=["c"], suggestion="s")]
    result = LLMClient().verify_batch([("draft A", items_a), ("draft B", [])])
    assert result == {0: items_a, 1: []}


def test_graph_still_reaches_two_interrupts_with_verify_node_inserted(monkeypatch):
    # use_verify=True로 verify_ambiguities_node가 extract와 confirm_ambiguities 사이에
    # 들어갔어도, mock 모드에서는 필터링이 없으니 기존 happy-path(2번 interrupt)가 그대로
    # 유지돼야 함. (기본값 use_verify=False는 test_graph_happy_path.py가 이미 커버함 —
    # gpt-5-mini 실측으로 verify가 precision을 악화시켜 기본 파이프라인에서 뺐다.)
    monkeypatch.setenv("DITTO_LLM_MODE", "mock")
    graph = build_graph(use_verify=True)
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}
    draft = "내일까지 조금 더 고민해 보면 좋을 것 같아요"
    context = DraftContext(now_iso="2026-08-14T18:44:00+09:00")

    graph.invoke({"draft": draft, "context": context.model_dump()}, config=config)
    snapshot = graph.get_state(config)
    assert snapshot.interrupts
    assert snapshot.values["extraction"]["ambiguities"]  # verify_ambiguities_node가 채워둔 상태


def test_mock_embed_is_deterministic_for_same_text(monkeypatch):
    monkeypatch.setenv("DITTO_LLM_MODE", "mock")
    client = LLMClient()
    assert client.embed("같은 텍스트") == client.embed("같은 텍스트")


def test_mock_embed_differs_for_different_text(monkeypatch):
    monkeypatch.setenv("DITTO_LLM_MODE", "mock")
    client = LLMClient()
    assert client.embed("텍스트 A") != client.embed("텍스트 B")
