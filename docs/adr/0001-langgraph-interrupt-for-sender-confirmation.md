- Title: Use LangGraph `interrupt()` + checkpointer for sender confirmation
- Status: Accepted
- Date: 2026-08-14
- Context: 발신자는 시간 표현("내일까지")과 의미 모호성("조금 더 고민해 보면?")을
  AI가 임의로 확정하지 않고 반드시 스스로 확인해야 한다(핸드오프 문서 3·5절 — "AI가
  사람의 의도를 맞히는 것이 아니라, 추정하기 어려운 부분을 발견해 사람이 명시적으로
  확정하도록 돕는다"). 이 확인은 발신자가 실제로 답을 줄 때까지 임의의 시간이 걸릴 수
  있고, 답을 준 뒤에는 정확히 멈췄던 지점부터 이어서 실행돼야 한다. 또한 이 프로젝트는
  발표에서 "단순 챗봇과의 차별점"으로 사람 개입 지점을 강조해야 한다.
- Options:
  1. LangGraph 없이 FastAPI 세션/DB 플래그(`pending_confirmation` 컬럼)로 직접
     일시정지·재개를 구현.
  2. LangGraph `StateGraph` + 노드 안에서 `interrupt()` 호출, 체크포인터
     (`MemorySaver`/`SqliteSaver`)로 상태를 `thread_id` 기준 영속화, 재개는
     `Command(resume=...)`.
  3. 별도의 워크플로우 엔진(Temporal 등) 도입.
- Decision: Option 2. `interrupt()`는 그래프 상태를 자동으로 스냅샷하고 실행을
  멈추므로, 직접 상태 플래그를 관리하는 것보다 재개 시점의 버그(어느 노드부터 다시
  실행해야 하는지)를 줄일 수 있다. Option 3은 해커톤 규모에 비해 과함. 개발 초반에는
  `MemorySaver`로 그래프 로직 자체를 검증하고, 안정화되면 `SqliteSaver`로 교체한다
  (문서 4절이 DB로 SQLite를 명시했으므로 최종 상태는 Sqlite).
- Consequences: 그래프 밖(FastAPI 팀원)에서는 `thread_id`와 `interrupt()`가 반환한
  payload만 다루면 되고, 그래프 내부 노드 순서가 바뀌어도 인터페이스가 안 바뀐다.
  반면 LangGraph의 체크포인터 직렬화 방식에 상태 스키마가 종속되므로, `graph/state.py`
  타입을 바꿀 때는 기존에 저장된 체크포인트와의 호환성을 함께 고려해야 한다(해커톤
  스코프에서는 개발 중 체크포인트 DB를 자유롭게 초기화해도 무방).
- References: `docs/references.md`의 "LangGraph interrupt 아키텍처" 절.
