# Progress Log

## 2026-08-14 — Repo scaffold + agent package skeleton (Claude 담당 파트)

### Done

- 저장소 생성(`~/Downloads/ditto`), `CLAUDE.md`/`.gitignore`는 `git-claude` 개인
  템플릿 기반.
- 역할 분담 확정: 이 저장소는 **AI 모델(LLM 프롬프트 + LangGraph 에이전트)** 파트만
  다룬다. FastAPI/DB/프론트는 다른 팀원이 별도 저장소에서 담당 — `agent/README.md`가
  통합 접점.
- `agent/` uv 프로젝트 스캐폴드: `src/ditto_agent/{schema,llm,graph,interface}.py`,
  `tests/`, `examples/cli_demo.py`.
- ADR 2건 작성: `0001-langgraph-interrupt-for-sender-confirmation.md`,
  `0002-combine-c2-c3-c4-into-single-claude-call.md`.
- `docs/문화_판단기준표_초안.md`는 **원본 파일을 디스크에서 찾지 못해** 빈 템플릿 +
  작성 가이드만 만들어둠 — 실제 20개 항목은 팀원이 인터뷰/리서치로 채워야 함.

### Notes

- LLM 프로바이더는 **OpenAI(GPT)**로 확정 — 팀 공유 키가 OpenAI 조직 플랜 키라
  바로 쓸 수 있음(핸드오프 문서 4절의 "Claude API" 초기 결정을 실사용 키 기준으로
  뒤집음). `llm/client.py`는 `DITTO_LLM_MODE=mock`이 기본값이고, `OPENAI_API_KEY`
  세팅 후 `live`로 바로 전환 가능 — 더 이상 키 발급 대기 블로커 아님.
- LangGraph interrupt 패턴은 `esurovtsev/langgraph-hitl-fastapi-demo`,
  `KirtiJha/langgraph-interrupt-workflow-template` 두 레퍼런스로 구조 확인 후 적용:
  체크포인터(`MemorySaver` → 안정화 후 `SqliteSaver`) + `interrupt()` + `Command(resume=...)`.
- 프론트엔드 참고용 인터랙티브 프로토타입(`prototype (1).html`)은 이 저장소 스코프
  밖 — 다른 팀원이 갖고 있는 파일이며 복사하지 않음.

### Next

- `schema.py`/`prompts.py` → `llm/client.py`(mock) → 그래프(`state/nodes/build`,
  interrupt 2곳) → `interface.py`/`cli_demo.py` → 테스트 → README 순서로 진행.
- `SqliteSaver`로 체크포인터 최종 교체.
- `OPENAI_API_KEY` 세팅 후 live 모드 대조 테스트.
- 판단기준표 20개 항목, 팀원 리서치 완료되는 대로 few-shot에 반영.

---

## 2026-08-14 (계속) — agent 패키지 end-to-end 구현 완료

### Done

- `agent/src/ditto_agent/` 전체 구현: `schema.py`(문서 5절 JSON 스키마 그대로
  `AmbiguityItem`/`InterruptPayload` + `ExtractionResult`/`ConfirmedCard`),
  `llm/{prompts,client}.py`(OpenAI `chat.completions.parse` + structured output,
  `DITTO_LLM_MODE=mock` 고정 응답 fallback), `graph/{state,nodes,conflict,build}.py`
  (`extract → time_confirm(interrupt) → interp_confirm(interrupt) → conflict_check →
  build_card → END`), `interface.py`(`start()`/`resume()`/`configure()` 공개 계약).
- **LLM 프로바이더는 OpenAI(GPT)로 확정** — 사용자가 팀 공유 키(OpenAI 조직 플랜)를
  바로 쓰기로 결정, 문서 4절의 "Claude API" 최초안 대체. ADR 0002 갱신.
- `uv run python examples/cli_demo.py`로 mock 모드 수동 검증: "내일까지 조금 더
  고민해 보면 좋을 것 같아요" 입력 → time_confirm interrupt → interp_confirm
  interrupt → `ConfirmedCard` 정상 생성 확인.
- pytest 7개 전부 통과: mock 추출기의 모호성 감지/억제, 그래프 happy-path(interrupt
  2회 → 카드), 모호성 없을 때 interrupt 스킵, interrupt payload가 문서 5절 스키마와
  일치하는지, `start`/`resume`이 같은 `thread_id`로 정확히 이어지는지.
- `SqliteSaver.from_conn_string()` + `configure(checkpointer=...)` 조합도 수동
  스모크 테스트로 확인 — 프로덕션 배선 그대로 동작.
- `agent/README.md`에 FastAPI 팀원용 통합 계약(함수 시그니처, `InterruptPayload`/
  `ConfirmedCard` 예시 JSON, `conflict_checker`/`checkpointer` 주입 방법) 작성.
- GitHub 레포 확인: `LikeLion-Hackathon-Borderless/AI` — 기본 placeholder README만
  있는 빈 상태. 이번에 만든 `agent/` 내용을 여기로 푸시할 예정(아직 미푸시 — 사용자
  확인 후 진행).

### Notes

- `graph/conflict.py`의 `default_conflict_checker`는 09-18시 하드코딩 placeholder다
  — 실제 근무시간/공휴일 로직(C-5/C-6)은 스코프 밖(다른 팀원)이며,
  `configure(conflict_checker=...)`로 교체하는 게 전제.
- 판단기준표는 여전히 빈 템플릿 — `llm/prompts.py`의 `FEW_SHOT_EXAMPLES`에 두 개의
  범용 예시(시간/의미 모호성 각 1개)만 하드코딩해둔 상태.

### Next

- 팀원이 `agent/README.md` 계약대로 FastAPI에서 `start()`/`resume()` 연동.
- `OPENAI_API_KEY` 넣고 `DITTO_LLM_MODE=live`로 실제 GPT 응답이 스키마를 지키는지
  대조 확인(현재는 mock만 검증됨).
- GitHub 레포에 push할지 사용자 확인 후 진행.

---

## 2026-08-14 (계속) — 문화 판단기준표 20개 항목 반영

### Done

- 사용자가 실제 판단기준표(T01-05 Scheduling, F01-06 Evaluating/Disagreeing, D01-05
  Deciding, C01-04 Communicating — Culture Map 4축 + KoBBQ 3단계 분류, 전부 미검증)를
  제공 — `docs/문화_판단기준표_초안.md`를 placeholder에서 실제 내용으로 교체.
- `agent/src/ditto_agent/llm/culture_criteria.py` 신설: 20개 항목을 구조화된
  `CULTURE_CRITERIA`로 옮기고(id/category/direction/phrase/reason/candidates/
  suggestion/verified), `as_few_shot_examples()`로 `AmbiguityItem` 모양의 few-shot
  20개를 생성. 축 매핑: Scheduling→TIME, Evaluating/Disagreeing→REQUEST_INTENT,
  Deciding→DECISION_STATUS, Communicating→OTHER.
- `llm/prompts.py`의 `FEW_SHOT_EXAMPLES`가 이 20개를 그대로 씀 — 이전에 내가 임의로
  넣었던 예시 2개(플레이스홀더)는 제거. 시스템 프롬프트 길이 약 5.2K자로 컨텍스트
  여유 충분.
- `uv run pytest` 7개 재검증 통과(few-shot 내용 변경이 mock 추출 로직에는 영향 없음
  — 별도 라이브 모드 대조 테스트는 여전히 키 확보 후 진행 필요).

### Next

- 인터뷰 검증 후 `culture_criteria.py`의 `verified` 필드 갱신.
- 위와 동일: FastAPI 연동, live 모드 대조, GitHub push 여부 확인.

---

## 2026-08-15 — PR #1 코드 리뷰 반영

### Done

`/code-review`(백그라운드 서브에이전트) 결과 8건 전부 수정:

- **DECISION_STATUS/OTHER 모호성이 확인 안 되고 버려지던 문제**: `time_confirm_node`/
  `interp_confirm_node` 2개 고정 노드를 `confirm_ambiguities_node` 1개로 교체 —
  `extraction.ambiguities`에 담긴 항목 전부를 카테고리 무관하게 순서대로 interrupt로
  확인받는다. `InterruptPayload`도 `kind/question/candidates` 중복 필드를 걷어내고
  `step/total/item`으로 단순화(질문/후보는 `item.suggestion`/`item.candidates`에
  이미 있었음).
- **카테고리당 첫 항목만 쓰던 문제**: `build_card_node`가 TIME/REQUEST_INTENT/
  DECISION_STATUS 각각 첫 번째 확인 답만 지정 필드(`deadline_confirmed`/
  `interpretation_note`/`decision_status`)에 반영하고, 그 이후(같은 카테고리 중복
  또는 OTHER)는 새로 추가한 `ConfirmedCard.notes: list[str]`에 쌓아 — 어떤 확인
  항목도 조용히 버려지지 않게 함.
- **`DITTO_LLM_MODE` 오타 시 애매한 `AttributeError`**: `LLMClient.__init__`이
  `"mock"`/`"live"` 외 값이면 생성 시점에 바로 `ValueError`.
- **`interface.py` 전역 `_graph` 싱글턴 레이스**: `threading.Lock`으로 체크-then-set
  보호(double-checked locking).
- **mock 추출기가 명시적 기한을 "명시된 기한 없음"으로 잘못 표시**: `_mock_deadline_raw`
  가 "내일" 외에도 "...까지" 패턴을 감지해 `deadline_raw`를 채움.
- **CLAUDE.md "no docstrings" 위반 3건**: `interface.py`(`configure`),
  `cli_demo.py`, `culture_criteria.py`의 docstring을 제거하고 필요한 것만 짧은
  인라인 "why" 주석으로 대체.
- 리팩터 과정에서 `StateSnapshot.next`가 "다음 노드"를, `StateSnapshot.interrupts`가
  "미해결 interrupt"를 가리키는 서로 다른 필드라는 걸 재확인 — 노드 하나 안에서
  `interrupt()`를 여러 번 부르는 구조(이번 리팩터)에서는 `.next`가 비어 있어도
  `.interrupts`는 차 있을 수 있음. `_read_state`가 이제 `.interrupts`를 봄.
- 새 테스트 `test_build_card_node.py`(중복/OTHER 카테고리가 notes로 가는지) +
  `test_invalid_llm_mode_raises_clear_error` 추가. 기존 그래프 테스트는 새
  `InterruptPayload` 모양에 맞게 갱신. `uv run pytest` 10개 전부 통과, ruff clean.
- `agent/README.md`의 `InterruptPayload`/`ConfirmedCard` 예시 JSON을 새 스키마로
  갱신.

### Next

- PR #1에 이 수정 커밋 push, 필요하면 재리뷰.
- FastAPI 연동, live 모드 대조, GitHub push 여부는 이전 항목과 동일하게 남아있음.
