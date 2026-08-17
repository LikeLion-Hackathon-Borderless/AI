from ditto_agent.eval import cache
from ditto_agent.eval.cli import (
    _chunks,
    _fetch_live_batch,
    _fetch_live_consistency,
    _fetch_live_sequential,
)
from ditto_agent.eval.golden import GoldenCase
from ditto_agent.schema import AmbiguityItem, ExtractionResult

_AMBIGUOUS_A = AmbiguityItem(span="s", category="TIME", reason="r", candidates=["c"], suggestion="s")
_RESULT_A = ExtractionResult(task="A", request_type="r", decision_status="d", ambiguities=[_AMBIGUOUS_A])
_RESULT_B = ExtractionResult(task="B", request_type="r", decision_status="d", ambiguities=[])


class _FakeClient:
    model = "fake-model"

    def __init__(self, batch_response, extract_response=None, batch_error=None, verify_batch_response=None):
        self._batch_response = batch_response
        self._extract_response = extract_response
        self._batch_error = batch_error
        self._verify_batch_response = verify_batch_response
        self.batch_calls: list[list] = []
        self.extract_calls: list[str] = []
        self.verify_batch_calls: list[list] = []

    def extract_batch(self, items):
        self.batch_calls.append(items)
        if self._batch_error is not None:
            raise self._batch_error
        return self._batch_response

    def extract(self, draft, context):
        self.extract_calls.append(draft)
        return self._extract_response

    def verify_batch(self, items):
        self.verify_batch_calls.append(items)
        return self._verify_batch_response


def _case(case_id: str) -> GoldenCase:
    return GoldenCase(id=case_id, draft=f"draft-{case_id}", expected_categories=frozenset())


def test_chunks_splits_evenly_and_remainder():
    assert list(_chunks([1, 2, 3, 4, 5], 2)) == [[1, 2], [3, 4], [5]]


def test_fetch_live_batch_uses_batch_result_when_complete(monkeypatch):
    monkeypatch.setattr(cache, "save", lambda *a, **k: None)
    client = _FakeClient(batch_response={0: _RESULT_A, 1: _RESULT_B})
    cases = [_case("X"), _case("Y")]

    results, aborted = _fetch_live_batch(client, cases, batch_size=10, pace=0)

    assert not aborted
    assert results == {"X": _RESULT_A, "Y": _RESULT_B}
    assert client.extract_calls == []  # 배치가 다 채워졌으면 개별 폴백 호출 없음


def test_fetch_live_batch_falls_back_per_case_when_batch_drops_an_index(monkeypatch):
    monkeypatch.setattr(cache, "save", lambda *a, **k: None)
    # 배치 응답에서 index 1(Y)이 통째로 빠짐 — 모델이 항목을 누락시킨 상황을 흉내
    client = _FakeClient(batch_response={0: _RESULT_A}, extract_response=_RESULT_B)
    cases = [_case("X"), _case("Y")]

    results, aborted = _fetch_live_batch(client, cases, batch_size=10, pace=0)

    assert not aborted
    assert results == {"X": _RESULT_A, "Y": _RESULT_B}
    assert client.extract_calls == ["draft-Y"]  # 누락된 것만 개별 재시도


def test_fetch_live_batch_aborts_on_rate_limit_but_keeps_partial_results(monkeypatch):
    monkeypatch.setattr(cache, "save", lambda *a, **k: None)

    class RateLimitError(Exception):
        pass

    client = _FakeClient(batch_response=None, batch_error=RateLimitError("429"))
    cases = [_case("X"), _case("Y")]

    results, aborted = _fetch_live_batch(client, cases, batch_size=10, pace=0)

    assert aborted
    assert results == {}


class _FakeSequentialClient:
    model = "fake-model"

    def __init__(self, extract_response, verify_filters_to: list | None = None):
        self._extract_response = extract_response
        self._verify_filters_to = verify_filters_to
        self.verify_calls = 0

    def extract(self, draft, context):
        return self._extract_response

    def verify(self, draft, ambiguities):
        self.verify_calls += 1
        return self._verify_filters_to if self._verify_filters_to is not None else ambiguities


def test_fetch_live_sequential_chains_verify_when_enabled(monkeypatch):
    monkeypatch.setattr(cache, "save", lambda *a, **k: None)
    client = _FakeSequentialClient(_RESULT_A, verify_filters_to=[])  # verify가 후보를 전부 제거
    cases = [_case("X")]

    results, aborted = _fetch_live_sequential(client, cases, verify=True, pace=0)

    assert not aborted
    assert client.verify_calls == 1
    assert results["X"].ambiguities == []  # extract는 1개 냈지만 verify가 걸러냄


def test_fetch_live_sequential_skips_verify_when_disabled(monkeypatch):
    monkeypatch.setattr(cache, "save", lambda *a, **k: None)
    client = _FakeSequentialClient(_RESULT_A, verify_filters_to=[])
    cases = [_case("X")]

    results, aborted = _fetch_live_sequential(client, cases, verify=False, pace=0)

    assert not aborted
    assert client.verify_calls == 0
    assert results["X"] == _RESULT_A  # verify 생략 — 1차 결과 그대로


def test_fetch_live_batch_chains_verify_batch_when_enabled(monkeypatch):
    monkeypatch.setattr(cache, "save", lambda *a, **k: None)
    # extract_batch가 X에 후보 1개(_AMBIGUOUS_A)를 냈지만, verify_batch가 전부 걸러냄(빈 리스트)
    client = _FakeClient(batch_response={0: _RESULT_A, 1: _RESULT_B}, verify_batch_response={0: [], 1: []})
    cases = [_case("X"), _case("Y")]

    results, aborted = _fetch_live_batch(client, cases, batch_size=10, pace=0, verify=True)

    assert not aborted
    assert len(client.verify_batch_calls) == 1  # 배치당 verify 호출도 1개로 고정
    assert results["X"].ambiguities == []  # extract는 1개 냈지만 verify_batch가 걸러냄
    assert results["Y"].ambiguities == []


def test_fetch_live_batch_skips_verify_batch_when_disabled(monkeypatch):
    monkeypatch.setattr(cache, "save", lambda *a, **k: None)
    client = _FakeClient(batch_response={0: _RESULT_A, 1: _RESULT_B}, verify_batch_response={0: [], 1: []})
    cases = [_case("X"), _case("Y")]

    results, aborted = _fetch_live_batch(client, cases, batch_size=10, pace=0, verify=False)

    assert not aborted
    assert client.verify_batch_calls == []
    assert results["X"] == _RESULT_A  # verify 생략 — 1차 결과 그대로


class _FakeConsistencyClient:
    model = "fake-model"

    def __init__(self, response=None, error=None):
        self._response = response
        self._error = error
        self.consistency_calls: list[tuple] = []

    def extract_consistent(self, draft, context, n, threshold):
        self.consistency_calls.append((draft, n, threshold))
        if self._error is not None:
            raise self._error
        return self._response


def test_fetch_live_consistency_calls_extract_consistent_per_case(monkeypatch):
    monkeypatch.setattr(cache, "save", lambda *a, **k: None)
    client = _FakeConsistencyClient(response=_RESULT_A)
    cases = [_case("X"), _case("Y")]

    results, aborted = _fetch_live_consistency(client, cases, n=3, threshold=2, pace=0)

    assert not aborted
    assert results == {"X": _RESULT_A, "Y": _RESULT_A}
    assert client.consistency_calls == [("draft-X", 3, 2), ("draft-Y", 3, 2)]


def test_fetch_live_consistency_aborts_on_rate_limit_but_keeps_partial_results(monkeypatch):
    monkeypatch.setattr(cache, "save", lambda *a, **k: None)

    class RateLimitError(Exception):
        pass

    client = _FakeConsistencyClient(error=RateLimitError("429"))
    cases = [_case("X"), _case("Y")]

    results, aborted = _fetch_live_consistency(client, cases, n=3, threshold=2, pace=0)

    assert aborted
    assert results == {}
