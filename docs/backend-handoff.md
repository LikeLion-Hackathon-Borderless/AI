# 백엔드 연동 체크리스트

AI 에이전트 파트(`agent/`)를 FastAPI 서버에 붙일 때 확인할 것들. 함수 시그니처·JSON
스키마·예시 코드 같은 상세는 **[`agent/README.md`](../agent/README.md)** 에 전부
있으니, 이 문서는 "받는 것 vs 직접 만들어야 하는 것"만 빠르게 훑는 용도로 보면 됨.

## 저장소에서 받는 것

`LikeLion-Hackathon-Borderless/AI` 레포 `main` 브랜치, `agent/` 폴더 전체.
`agent/README.md`가 이 패키지와의 유일한 통합 접점이니 먼저 그것부터 읽으면 됨.
공개 API는 이거 하나로 끝:

```python
from ditto_agent import configure, start, resume
from ditto_agent.schema import DraftContext, StartResult, InterruptPayload, ConfirmedCard, ConflictResult
```

- `configure(...)` — 서버 뜰 때 1번만 호출
- `start(draft, context)` / `resume(thread_id, answer)` — 메시지 하나 처리할 때마다 호출

## 직접 만들어야 하는 것 (연결하려면 필수 3가지)

**1. `conflict_checker` 함수** — `configure()`에 안 넘기면 9~18시 하드코딩된
placeholder가 그대로 쓰임(진짜 근무시간표/공휴일 반영 안 됨). 실제 근무시간표 DB를
조회하는 함수를 만들어서 넘겨줘야 함.

```python
def real_conflict_checker(time_confirmed: str, context: DraftContext) -> ConflictResult:
    ...  # 여기서 실제 근무시간/공휴일 DB 조회
```
참고 구현: `agent/src/ditto_agent/graph/conflict.py`의 `default_conflict_checker`.

**2. `checkpointer` 배선** — 안 넘기면 메모리에만 저장돼서 서버 재시작하면 진행 중이던
대화(`thread_id`)가 다 날아감. `SqliteSaver` 등으로 교체해서 넘겨야 함(예시 코드는
`agent/README.md` "프로덕션 배선" 절에 있음).

**3. 카드 저장할 도메인 DB** — 확정된 `ConfirmedCard`, 메시지/합의 기록은 이 패키지가
안 갖고 있음 — 각자 팀 DB에 저장해야 함. 체크포인터 DB(그래프 재개용)와는 다른
용도니 섞지 말 것.

## 환경변수 — 이건 직접 새로 만들어야 함

- `OPENAI_API_KEY` — AI 파트 개발할 때 쓴 키는 테스트용이라 **넘겨받지 말고 직접
  발급**받아야 함
- `DITTO_LLM_MODE=live`, `DITTO_OPENAI_MODEL=o3-mini`, `DITTO_CHECKPOINT_DB` —
  값은 `agent/.env.example` 그대로 쓰면 됨

## 설치

```bash
cd agent
uv sync
```

별도 배포 과정 없이 파이썬 패키지 의존성으로 그냥 붙이면 됨.

## 더 볼 것

- 인터럽트 화면 렌더링, 카드 필드 하나하나의 의미는 `agent/README.md`에 예시 JSON과
  같이 정리돼 있음
- "왜 정확도 옵션들이 다 기본 꺼짐이냐"가 궁금하면 `agent/README.md`의 "정확도 설정"
  절 참고 — recall(놓치지 않는 것)을 precision보다 우선한 이유 설명해둠
