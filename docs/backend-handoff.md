# 백엔드 연동 체크리스트

AI 에이전트 파트(`agent/`)를 FastAPI 백엔드에 연결하기 위해 필요한 것들 정리.
API 상세(함수 시그니처, JSON 스키마, 예시 코드)는 **[`agent/README.md`](../agent/README.md)**
에 전부 있음 — 이 문서는 "무엇을 넘기고 무엇을 직접 만들어야 하는지"만 요약.

## 1. 저장소 접근

`LikeLion-Hackathon-Borderless/AI` 레포, `main` 브랜치. `agent/` 폴더가 이 팀의 전체
산출물이고, `agent/README.md`가 유일한 실제 통합 접점.

## 2. 공개 API (`from ditto_agent import ...`)

- `configure(conflict_checker, checkpointer, ...)` — 서버 시작 시 1번 호출
- `start(draft, context)` / `resume(thread_id, answer)` — 메시지 처리 진입점
- 스키마: `DraftContext`, `StartResult`, `InterruptPayload`, `ConfirmedCard`,
  `ConflictResult`, `AmbiguityItem`

## 3. 백엔드가 직접 구현해야 하는 것 (연결하려면 필수)

- **`conflict_checker` 함수** — 기본값은 9~18시 하드코딩 placeholder. 진짜
  근무시간표/공휴일 DB 조회로 교체해서 `configure(conflict_checker=...)`에 넘겨야 함.
  시그니처: `(time_confirmed: str, context: DraftContext) -> ConflictResult`
  (`agent/src/ditto_agent/graph/conflict.py`의 `default_conflict_checker` 참고 구현)
- **`checkpointer`** — 기본은 메모리라 서버 재시작하면 대화 상태(진행 중이던
  `thread_id`)가 날아감. `SqliteSaver`(또는 다른 백엔드)를 배선해서
  `configure(checkpointer=...)`에 넘겨야 함(`agent/README.md`에 예시 코드 있음).
- **도메인 DB** — 확정된 `ConfirmedCard`, 메시지/합의 기록 저장은 이 패키지 밖의
  일. 체크포인터 DB(그래프 재개 상태 전용)와 섞지 말 것.

## 4. 환경변수 — 본인 계정으로 새로 발급

- `OPENAI_API_KEY` — ⚠️ AI 파트 개발용 `.env`의 키는 테스트용이라 **그대로 넘기면
  안 됨**. 백엔드 팀이 자기 계정으로 새로 발급받아야 함
- `DITTO_LLM_MODE=live`, `DITTO_OPENAI_MODEL=o3-mini`, `DITTO_CHECKPOINT_DB` —
  `agent/.env.example` 그대로 참고

## 5. 설치

```bash
cd agent
uv sync
```

별도 배포 없이 파이썬 패키지 의존성으로 붙이면 됨.

## 참고

- 인터럽트 응답 렌더링, 카드 필드 의미 등 세부 사항은 `agent/README.md`에 예시
  JSON까지 다 있음
- 정확도 설정(`use_verify`/`use_consistency`/`use_rag`)이 왜 다 기본 꺼짐인지는
  `agent/README.md`의 "정확도 설정" 절 참고
