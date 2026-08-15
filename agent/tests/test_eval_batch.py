from ditto_agent.eval import cache
from ditto_agent.eval.cli import _chunks, _fetch_live
from ditto_agent.eval.golden import GoldenCase
from ditto_agent.schema import ExtractionResult

_RESULT_A = ExtractionResult(task="A", request_type="r", decision_status="d", ambiguities=[])
_RESULT_B = ExtractionResult(task="B", request_type="r", decision_status="d", ambiguities=[])


class _FakeClient:
    model = "fake-model"

    def __init__(self, batch_response, extract_response=None, batch_error=None):
        self._batch_response = batch_response
        self._extract_response = extract_response
        self._batch_error = batch_error
        self.batch_calls: list[list] = []
        self.extract_calls: list[str] = []

    def extract_batch(self, items):
        self.batch_calls.append(items)
        if self._batch_error is not None:
            raise self._batch_error
        return self._batch_response

    def extract(self, draft, context):
        self.extract_calls.append(draft)
        return self._extract_response


def _case(case_id: str) -> GoldenCase:
    return GoldenCase(id=case_id, draft=f"draft-{case_id}", expected_categories=frozenset())


def test_chunks_splits_evenly_and_remainder():
    assert list(_chunks([1, 2, 3, 4, 5], 2)) == [[1, 2], [3, 4], [5]]


def test_fetch_live_uses_batch_result_when_complete(monkeypatch):
    monkeypatch.setattr(cache, "save", lambda *a, **k: None)
    client = _FakeClient(batch_response={0: _RESULT_A, 1: _RESULT_B})
    cases = [_case("X"), _case("Y")]

    results, aborted = _fetch_live(client, cases, batch_size=10, pace=0)

    assert not aborted
    assert results == {"X": _RESULT_A, "Y": _RESULT_B}
    assert client.extract_calls == []  # 배치가 다 채워졌으면 개별 폴백 호출 없음


def test_fetch_live_falls_back_per_case_when_batch_drops_an_index(monkeypatch):
    monkeypatch.setattr(cache, "save", lambda *a, **k: None)
    # 배치 응답에서 index 1(Y)이 통째로 빠짐 — 모델이 항목을 누락시킨 상황을 흉내
    client = _FakeClient(batch_response={0: _RESULT_A}, extract_response=_RESULT_B)
    cases = [_case("X"), _case("Y")]

    results, aborted = _fetch_live(client, cases, batch_size=10, pace=0)

    assert not aborted
    assert results == {"X": _RESULT_A, "Y": _RESULT_B}
    assert client.extract_calls == ["draft-Y"]  # 누락된 것만 개별 재시도


def test_fetch_live_aborts_on_rate_limit_but_keeps_partial_results(monkeypatch):
    monkeypatch.setattr(cache, "save", lambda *a, **k: None)

    class RateLimitError(Exception):
        pass

    client = _FakeClient(batch_response=None, batch_error=RateLimitError("429"))
    cases = [_case("X"), _case("Y")]

    results, aborted = _fetch_live(client, cases, batch_size=10, pace=0)

    assert aborted
    assert results == {}
