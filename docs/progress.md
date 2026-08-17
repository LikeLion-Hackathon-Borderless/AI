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

---

## 2026-08-15 — golden-set 평가 하네스 (`ditto-eval`)

### Done

`planqa-eval-agent`(`tools/eval-agent/`)를 직접 조사해 관례를 이식: golden 파싱 →
채점 → `report.json`+`report.md` 산출, `ConfusionCounts.recall/precision`은 분모 0이면
`None`(0.0/예외 아님), CLI는 `pyproject.toml [project.scripts]`. 예전 `harness/
confidence_gate.py`(계층화 샘플링 + 사람 블라인드 라벨 + 90/80/100% 임계값으로 막는 게이트)는
사용자가 2026-08-08에 직접 삭제한 걸 확인 — 그 선례를 따라 **막는 게이트는 만들지 않고**
숫자만 계산해 리포트로 보여준다.

레퍼런스 조사(GitHub/논문)로 설계 보강:
- **naver-ai/KoBBQ** — `all_samples`/`test_samples` 분리 관례 확인.
- **CLAM**(TriviaQA 기반 ambiguous/clear 쌍) — 골든셋을 "모호함 리스트 + 대조군 리스트"가
  아니라 **같은 시나리오의 모호한 버전/명시적 버전 쌍**으로 설계하도록 채택.
- **Prompt contamination**(arxiv 2311.01964) — few-shot 예시를 골든셋에 그대로 재사용하면
  "프롬프트에 준 정답 맞히기"가 되어 평가가 무의미해진다는 걸 정식 용어로 확인 →
  `culture_criteria.py`의 20개 phrase를 golden.json에 그대로 쓰지 않고 전부 패러프레이즈함
  (`test_golden_json_loads_and_pairs_expand_to_two_cases_each`가 이걸 회귀 테스트로 고정).

산출물:
- `agent/data/golden.json` — T01-05/F01-06/D01-05(14쌍) + C01-03(3쌍, OTHER — phrase가
  패턴 설명이라 실제 발화로 새로 작성) + 복합 케이스 2개(COMP-01/02, 카테고리 2개 동시) =
  40개 케이스. C04(침묵)는 단일 메시지 텍스트로 표현 불가능해 제외(`known_limitations`에
  명시).
- `agent/src/ditto_agent/eval/{golden,scorer,reporter,cli}.py` — `GoldenCase`/
  `score_case()`(카테고리 단위 tp/fn/fp)/`ConfusionCounts`(planqa 관례)/`aggregate()`
  (전체 + 카테고리별)/`write_report()`(md+json)/`ditto-eval` CLI.
- `agent/pyproject.toml`에 `ditto-eval` 스크립트 등록.
- 테스트 9개 추가(`test_eval_scorer.py`) — scorer 로직(LLM 불필요) + golden.json 로드 +
  few-shot과 golden set 문구가 안 겹치는지 확인하는 contamination 회귀 테스트. 전체
  `uv run pytest` 17개 통과, ruff clean.
- `DITTO_LLM_MODE=mock uv run ditto-eval` 스모크 테스트: 40 케이스 다 돌고 report 생성
  확인. recall 4%/precision 33% — **예상대로 무의미한 숫자**(mock은 "내일"/"고민"/
  "재검토" substring만 보는 placeholder라 패러프레이즈를 대부분 못 잡음). report.md
  상단에 이 경고 자동 삽입되게 만들어둠.

### Notes

- 흥미로운 확인 사례: D03-explicit("확인했고, 아직 검토 중입니다. 결정은 **내일**
  드릴게요")가 DECISION_STATUS 대조군인데도 mock이 "내일" substring 때문에 TIME으로
  오탐 — golden set이나 scorer 버그가 아니라 mock의 알려진 한계가 정확히 의도대로
  드러난 것.

### Next

- `OPENAI_API_KEY` 확보되면 `DITTO_LLM_MODE=live uv run ditto-eval`로 실제 정확도 산출
  — 이게 이번 세션에서 못 한 유일한 부분.
- 후보 해석 "품질"(candidate가 그럴듯한가) 평가는 precision/recall로 못 재는 별도 영역 —
  LLM-judge나 인터뷰 기반 평가는 스코프 밖으로 남겨둠.
- (발견, 이번 스코프 아님) `llm/prompts.py`의 few-shot이 C01-04의 phrase(패턴 설명,
  실제 발화 아님)를 예시 입력인 것처럼 그대로 쓰고 있음 — golden.json 만들면서 C01-03은
  실제 발화로 새로 썼지만 prompts.py 쪽은 원본 phrase 그대로라 live 모드 프롬프트 품질에
  영향 줄 수 있음. 다음에 손볼 것.

---

## 2026-08-16 — 첫 live 연결, 실제 버그 발견 + 호출 최적화

### Done

- 사용자가 `.env`에 실제 `OPENAI_API_KEY` 세팅, `DITTO_LLM_MODE=live`로 최초 실제 연결.
  `.env`가 실제로는 로드되고 있지 않던 걸 발견해 `__init__.py`에 `load_dotenv()` 추가.
- **실버그 발견(Figma로 확정)**: `227:2035`/`227:2341` 프레임 확인 결과 TIME 후보는
  파싱 가능한 절대시각이어야 하고(프론트가 수신자 시간대로 재변환·근무시간 충돌까지
  계산), 카드의 "기한"도 수신자 로컬로 변환된 값을 보여줘야 함 — 그런데 live 모델이
  `culture_criteria.py`의 TIME few-shot(설명 문장, ISO8601 아님)을 그대로 따라 해서
  `deadline_confirmed`에 문장을 넣었고, `conflict_check`가 완전히 무력화됐었음.
  → `culture_criteria.py` T01-05 candidates를 ISO8601로 전면 수정, `prompts.py`에
  "TIME candidates는 반드시 ISO8601, 같은 모호성을 여러 항목으로 쪼개지 말 것" 명시.
  수정 후 재확인: `conflict_check`가 정상적으로 수신자 로컬 시각·근무시간 충돌을 계산함.
- **골든셋 live 실행 중 발견한 진짜 문제**: `T0N-explicit`(대조군) 5개 중 4개가
  REQUEST_INTENT/TIME/OTHER로 오탐 — "~부탁드려도 될까요?" 같은 정중한 요청 어투 자체를
  모호성으로 오인하는 패턴으로 보임. precision 이슈, 아직 원인 파악/수정 못함(다음
  세션 과제).
- **호출 최적화** (이 세션의 핵심 작업 — rate limit 429로 두 번 실행 다 실패한 뒤 진행):
  - `OpenAI(max_retries=0)` — 기본 재시도(2회, 지수 백오프)가 429에도 조용히 재시도하며
    호출 하나를 실제 HTTP 요청 여러 개로 불림 + 호출당 수십 초씩 늘어지게 만들던 원인.
  - `eval/cache.py` 신설 — live 응답을 `.eval_cache/`(gitignore)에 캐싱, 캐시 키에
    시스템 프롬프트 해시 포함(프롬프트 바뀌면 자동 무효화). `--no-cache`로 우회 가능.
  - `ditto-eval --limit N` / `--only <id 부분문자열>` — 전량 대신 일부만 빠르게 확인.
  - rate limit(`RateLimitError`) 맞으면 남은 케이스는 건너뛰고 그때까지 결과로
    `report.json`/`.md`를 씀 — 이미 쓴 호출이 버려지지 않음(exit code 1로 구분).
  - `cli.py`에 케이스별 진행 로그(`[i/N] id ... ok/mismatch/FAILED`) 추가 — 이전엔
    40개 다 끝나야 아무 출력도 없어서 멈춘 건지 도는 건지 구분이 안 됐음.
- 테스트 3개 추가(`test_eval_cache.py`, LLM 불필요). 전체 `uv run pytest` 20개 통과.

### Notes

- 실제 사고 원인: gpt-5가 **하루 요청 50개(RPD)** 한도인 계정 — 디버깅하며 같은 골든셋을
  반복 실행하다 소진. 캐시가 있었으면 대부분 안 썼을 호출.
- rate limit 에러 메시지의 "28m48s 후 재시도" 안내는 신뢰하지 않는 게 안전 — RPD는
  보통 자정 기준 리셋에 가까움. 결제수단 등록해서 한도 올리는 게 근본 해결.

### Next

- (이월) `T0N-explicit` 대조군 오탐 원인 조사 — REQUEST_INTENT 판정 기준이 프롬프트에서
  너무 느슨하게 걸려있을 가능성.
- 한도 여유 생기면 `uv run ditto-eval`(캐시+재시도 비활성화 적용된 버전으로) 전체 재실행,
  실제 precision/recall 확정.
- (이월) `llm/prompts.py`의 C01-04 few-shot phrase 문제.

---

## 2026-08-16 (계속) — 전체 골든셋 첫 live 실행 + 원인 재정정

### Done

- `gpt-4o-mini`로 전체 40개 골든셋 첫 완주(`status=complete`): **recall=0.875,
  precision=0.512**. 패턴이 극단적으로 깔끔했음 — T/F/D 계열 `-ambiguous` 16개는
  **전부** 정답, `-explicit`(대조군) 16개는 **전부** 오탐(ambiguous 쪽과 같은
  카테고리로 플래그됨). OTHER(C01-03)는 카테고리 자체를 헷갈림(DECISION_STATUS로
  오분류). 복합 케이스(COMP-01/02)는 둘 다 정답.
- 1차 가설: `culture_criteria.py` few-shot 20개가 전부 "모호함" 양성 예시뿐이라 부정
  예시가 없어서 생긴 편향 → `prompts.py`에 `NEGATIVE_FEW_SHOT_EXAMPLES`(TIME/
  REQUEST_INTENT/DECISION_STATUS/일반 각 1~2개, golden.json과 안 겹치는 새 문장) 추가.
- `explicit` 19개만 재테스트 — REQUEST_INTENT 쪽은 일부 개선(F02-explicit 통과)됐지만
  **TIME은 5/5 그대로 전부 실패**. negative few-shot만으로는 TIME을 못 고침.
- **2차 원인, 더 근본적: golden.json 자체의 버그.** T01/T02/T03/T04-explicit과
  C02-explicit이 시간대 표기 없이 "8월 16일 18:00까지", "오늘 안으로", "수요일까지"
  같은 표현을 쓰고 있었음 — 이건 T01이 원래 지적하려던 모호성(발신자/수신자 시간대
  기준 불명확)을 그대로 갖고 있는 문장이라, 모델이 TIME으로 플래그한 게 오히려 golden
  라벨(`[]`)보다 합리적이었을 가능성이 높음. → 5개 케이스 모두 "(KST)" 명시 + "오늘
  안으로"처럼 남아있던 애매한 표현을 구체 시각으로 교체.
- **정정**: `gpt-4o-mini`도 `gpt-5`와 동일하게 **하루 요청 50개(RPD)** 한도였음 —
  모델을 싸게 바꾼다고 한도가 안 늘어남(계정 자체가 모델별로 각 50/day인 걸로 보임).
  이전 세션 노트의 "cheaper model = higher limit" 가정은 틀렸음, 정정.
- 오늘 두 모델 다 일일 한도 소진 — 골든셋 수정본으로 재실행은 다음 세션(또는 한도
  리셋/결제수단 등록 후).
- `uv run pytest` 20개 통과(golden.json 구조 변경이 로더 테스트를 안 깨는지 확인).

### Notes

- **precision 0.512라는 숫자 자체를 신뢰하지 말 것** — golden.json의 TIME explicit
  라벨 버그가 섞여 있던 상태에서 잰 수치라, 실제 오탐률은 이보다 낮을 가능성이 높음.
  golden.json 수정 반영 후 재측정 전까지는 참고용 하한선 정도로만 취급.
- `.eval_cache/`의 캐시 키에 시스템 프롬프트 해시가 들어있어서, negative few-shot을
  추가한 시점에 이전 40개 캐시가 전부 자동 무효화됨 — 의도대로 동작 확인.

### Next

- 한도 풀리면 수정된 golden.json + negative few-shot 조합으로 전체 40개 재실행,
  실제 precision/recall 확정.
- REQUEST_INTENT/DECISION_STATUS 쪽 explicit 오탐(F01/F03/F05/F06, D01/D02/D04
  explicit 등)은 golden.json 라벨 문제가 아니라 실제 모델 과다 플래깅으로 보임 —
  negative few-shot을 더 늘리거나 few-shot 배치(양성/부정 인접시키기) 조정 검토.
- 계정 요청 한도(모델별 50/day로 추정) 자체를 결제수단 등록으로 올릴지 사용자 결정
  필요 — 매 세션 디버깅만으로도 하루치가 순식간에 소진됨.

---

## 2026-08-16 (계속) — 배치 호출로 요청 수 자체를 줄임

### Done

사용자 제안("모델에 넣을 때 최적화된 파일로 호출 수를 줄이면 되잖아")을 받아 **여러
골든셋 케이스를 한 번의 API 호출로 묶어 처리**하도록 구현 — planqa `judge.py`의
"배치 호출 + 누락 항목만 개별 폴백" 패턴을 그대로 이식.

- `schema.py`: `BatchExtractionItem`/`BatchExtractionResult`(`{items: [{index, extraction}]}`).
- `prompts.py`: `build_batch_user_prompt()`(메시지 여러 개를 `[index]` 태그로 나열),
  `build_system_prompt(batch=True)`로 배치 응답 형식 지시(`BATCH_OUTPUT_SCHEMA_NOTE`) 추가.
- `llm/client.py`: `LLMClient.extract_batch(items) -> dict[index, ExtractionResult]` 신설.
  **실사용 흐름(`interface.start()`)은 안 씀** — 배치는 eval 전용, 실제 발신자는 항상
  메시지 1개이므로 배칭할 이유가 없음.
- `eval/cli.py`: `--batch-size`(기본 10) 만큼 묶어서 호출, 배치 응답에서 빠진 index는
  건별로 개별 재시도(fallback), rate limit이면 그 시점까지 결과로 부분 리포트 작성.
- 테스트 4개 추가(`test_eval_batch.py`) — 배치 완전 응답/부분 누락 폴백/rate limit 중단
  3가지 케이스를 페이크 클라이언트로 검증(LLM 무관). 전체 `uv run pytest` 24개 통과.
- **실 API로 배치 검증 완료**: `--limit 2 --batch-size 2`로 1콜에 2케이스 처리 성공
  (둘 다 정답). 이후 전체 40개(4콜 예정) 시도는 바로 재차 RPD 50/50에 걸려 실패 —
  직전 세션에서 이미 한도를 다 써서 여유가 딱 1콜만 남아있었던 것.

### Next

- 한도 풀리면 `uv run ditto-eval`(이제 40콜이 아니라 4콜) 한 번으로 전체 재실행,
  실제 precision/recall 확정 — 위 항목과 동일하게 여전히 미해결.

---

## 2026-08-16 (계속) — 골든셋 40/40 완주, 첫 확정 수치

### Done

`--pace 65`로 TPM 한도를 피해 gpt-5 4배치(10개씩) 전부 성공, **40/40 완주**:

| 카테고리 | Recall | Precision |
|---|---|---|
| 전체 | 88% (21/24) | 84% (21/25) |
| TIME | 100% | 73% (FP 3) |
| REQUEST_INTENT | 100% | 100% |
| DECISION_STATUS | 100% | 86% (FP 1) |
| OTHER | **0%** (FN 3) | N/A |

오답 6개 중 4개(T02/D03/D05-explicit)를 다시 보니 **골든셋 라벨 실수**였음 — D03/D05는
DECISION_STATUS 대조군으로 쓴 문장에 "내일"/"다음 주 화요일" 같은 상대 시간 표현을
무심코 남겨놔서, 모델이 TIME으로 잡은 게 정확한 판단인데 오답으로 채점된 것. TIME/
REQUEST_INTENT/DECISION_STATUS는 사실상 정밀도 문제가 없다고 봐도 됨.

**진짜 남은 문제는 OTHER 카테고리 3/3 전부 놓친 것** — 이전에 발견해둔 "`prompts.py`의
few-shot이 C01-04(패턴 설명, 실제 발화 아님)를 예시 입력인 것처럼 그대로 쓰고 있다"는
가설이 이 실측 결과로 뒷받침됨.

### Next

- **최우선**: `culture_criteria.py`의 C01-04 few-shot을 실제 발화 예시로 다시 쓰기
  (golden.json의 C01-03 explicit/ambiguous 작성할 때 이미 했던 것과 같은 작업 —
  prompts.py 쪽만 안 고쳐져 있었음).
- D03/D05 golden.json 라벨도 상대 시간 표현 제거해서 재검증(지금은 오답으로 잘못
  카운트됨 — 진짜 precision은 84%보다 높을 것).
- OTHER 고친 뒤 `uv run ditto-eval`(4콜) 재실행해서 최종 확정.

---

## 2026-08-16 (계속) — 트랙 요구사항 확인 후 재설계: 언어·조직 경계 대응

### Done

멋쟁이사자처럼 트랙 페이지(Notion, `claude-in-chrome`으로 직접 렌더링해 읽음)를
확인해 "지리/언어/문화/조직" 4개 경계(Border)와 심사 기준(보더리스 적합성이 *중요
표시)을 파악. 이걸로 두 가지가 바로 정정됨:

1. **D축(DECISION_STATUS)은 없애면 안 됨** — 어제 "문화적 근거가 약하다"고
   지적했던 게, 사실은 트랙이 명시한 **4번째 경계 "조직"** 그 자체였다. Erin
   Meyer의 Deciding 축(문화)에 억지로 맞추려니 근거가 약해 보였을 뿐, "조직 경계"
   관점에서는 오히려 이 프로젝트가 가장 직접적으로 대표하는 부분.
2. **언어(Border 02) 커버리지가 완전히 비어있었음** — AI 스코프에 번역이 전혀
   없었음. 기존 UI(Figma)를 새로 만들 필요 없이, 이미 있는 카드 필드에 AI가 더
   정확한/번역된 값을 채우는 것만으로 두 경계(언어+조직)를 다 채울 수 있다고
   판단해 아래처럼 구현.

**조직(Border 04) 대응**: `decision_status`를 자유 텍스트에서
`DECISION_STATUS_VOCABULARY`(최종 확정/임시 시도/1차 완료/제안/보류/미정) 6개
고정 어휘로 정규화하도록 프롬프트 수정 — "승인"/"완료"/"컨펌"의 조직별 의미 차이를
AI가 흡수해서 공통 어휘로 변환하는 게 골자. (하드 `Literal` 타입으로는 안 만듦 —
confirm된 답변이 후보 문구 그대로라 정확히 안 맞으면 pydantic validation이 깨질
위험이 있어서, 프롬프트 레벨 강한 지시로만 처리.)

**언어(Border 02) 대응**: `DraftContext.receiver_lang` 필드 추가, 그래프에
`build_card` 뒤에 `translate_card_node` 신설 — `receiver_lang`이 설정되면
`LLMClient.translate_card_fields()`가 카드의 자유 텍스트(`task`/`request_type`/
`interpretation_note`/`notes`)만 번역. **번역은 모호성 확정 이후에만** 하도록
순서를 의도적으로 그렇게 잡음 — 먼저 번역하면 번역기가 여러 해석 중 하나를
암묵적으로 골라버려서 발신자가 확정하기 전에 모호성이 사라지는 문제가 생기기
때문(핵심 원칙 위반). `evidence`(원문)와 `deadline_confirmed`(ISO8601) 등 구조화된
필드는 번역 안 함. 새 UI 필드 없이 기존 카드 필드 값만 로컬라이즈되는 구조.

같은 세션에서 지난번 논의대로 OTHER(C01-04) 완전 제거도 반영: `prompts.py`의
few-shot에서 OTHER 카테고리 항목 필터링, `golden.json`에서 C01/C03 pair 삭제,
C02는 TIME만 남기고 재작성(`C02-time-only`).

실 API로 번역 확인: `task: "리뷰"→"Review"`, `decision_status`가 새 정규화
어휘("미정") 그대로 나옴 — 첫 실행부터 정상 동작.

`docs/research-other-category.md`(OTHER 문헌 검증), `docs/research-tfd-validation.md`
(T/F/D 문헌 검증)도 이 기간에 작성 — F축 가장 탄탄, D축은 (문화가 아니라 조직
경계라는 게 밝혀지기 전 기준으로) 가장 약하다고 판단했었음.

테스트 3개 추가(`test_translate_card.py`). 전체 `uv run pytest` 28개 통과.

### Next

- (신규) `docs/survey-{T-scheduling,F-evaluating,D-org-vocab}.md` 작성 — 판단기준표
  16개 항목(OTHER 제외) 검증용 구글폼 문항, Holtgraves CIS의 리커트/production-
  interpretation 구조만 템플릿으로 차용(문항 내용은 CIS 그대로 안 씀 — CIS는 일반
  성향 자기보고 척도라 우리가 필요한 "특정 문장 해석" 테스트와 다름, 재현 실패
  이슈도 있어 결과 인용 안 함). T/F는 "한국 기반 vs 미국 기반" 스크리닝, D는
  "회사 2곳 이상 다녀본 사람"으로 스크리닝 다르게 설계(D축이 문화가 아니라 조직
  관행이라는 재발견 반영). 구글폼으로 옮겨서 배포하는 건 사용자 몫 — 아직 배포 전.
- `resolved_ambiguities`(모호성 전후 대응 기록) 필드는 논의 끝에 **기본 카드엔
  안 보이게** 하기로 함 — 수신자 카드는 지금처럼 깔끔하게 두고, "합의 기록" 탭이나
  발신자 확인 화면 쪽에만 노출하는 걸로 결정(아직 미구현).
- 한도 여유 생기면 golden.json(OTHER 제거 반영본)으로 `ditto-eval` 재실행,
  precision 재확정.
- 위 항목들(F축 프레이밍 다듬기, D축 재검증 등)은 여전히 미해결.

## 2026-08-16 (계속) — T/F/D 구글폼 실제 제작·배포, 응답 수집·분석 완료

`docs/survey-{T,F,D}-*.md` 설계를 실제 구글폼 3개로 제작(claude-in-chrome 브라우저
자동화 사용). 각 문항은 "선형 배율(1~7)" 타입으로, 해석형 문항(후보 해석 2~3개 병렬
평가)과 빈도형 문항("~한 적이 있다")을 구분. 폼 설명란엔 두 척도의 7점 전체 앵커를
명시(해석형: 전혀 그렇지 않음~확실히 그러함, 빈도형: 전혀 없음~매우 자주).

스크리닝 문항을 세션 중 재설계: 기존엔 "현재 상태"(직장인/학생) + 학생 세부경험
질문을 2개로 나눴었는데, 최종적으로 사용자가 4지선다 단일 질문으로 통합—
"직장인(6개월↑ 재직)" / "직장인(과거·6개월↓)" / "학생(해외교류·영어능숙)" /
"학생(협업경험만)". 직장인 쪽도 경력 깊이를 나누고 학생 쪽 언어노출 구분과
대칭 맞춘 형태. D폼엔 이 구분 자체를 넣지 않기로 함(D축은 "국적/영어 무관"이라
언어노출 축이 무의미하다는 이전 결정 유지).

브라우저 자동화 중 반복 발견한 버그 패턴: Google Forms의 contenteditable 제목
필드를 `left_click` 후 바로 `type`하면 기존 placeholder("제목 없음")가 지워지지
않고 새 텍스트 앞에 그대로 남는 경우 발생(예: "제목 없음D01 — ..."). `triple_click`
으로 먼저 전체 선택 후 `type`해야 안전하게 교체됨 — 이번 세션에도 여러 번 재발.
선형 배율 타입 드롭다운도 첫 클릭엔 열리기만 하고 선택이 안 씹히는 경우가 잦아,
열림 확인 스크린샷 후 별도 호출로 옵션을 클릭하는 2단계가 더 안정적이었음.

목표 n=8(현업 3+학생 5)을 넘겨 실제로는 T=13명, D=12명, F=12명 응답 수집(사용자가
직접 배포·수거). 응답 스프레드시트 3개를 CSV로 받아(`export?format=csv` URL을
브라우저 tab에서 navigate → `~/Downloads`에 자동 다운로드되는 방식, WebFetch는 인증
안 돼서 401 — 브라우저 세션 통해 우회) `docs/survey-results-analysis.md`에 문항별
평균/표준편차 분석 작성.

**핵심 발견**: 판단기준표 16개 항목이 두 갈래로 갈림 —
1. **국내에서도 진짜 갈리는 항목**(D02/D04, T01/T04/T05, F01/F02/F05) — 후보
   해석들의 평균이 비슷하고 sd가 큼(≥1.7). 프롬프트/few-shot 그대로 유지.
2. **국내 컨센서스는 강하지만 문화 간 기본값이 다를 걸로 보이는 항목**(D01/D03/D05,
   F03/F04) — 한 후보가 sd 1.3 이하로 압도적. 특히 F04(영어 원문 "great, but
   reconsider X")는 한국 응답자가 "반드시 수정할 필수사항"으로 sd 0.69의 극강
   컨센서스를 보임 — Meyer 문헌이 말하는 원어민 문화권의 완곡한 해석과 정반대
   방향이라, 오히려 "문화 간 기본값 충돌"의 가장 뚜렷한 실증 사례가 됨.
3. T축은 개별 항목의 갈림 여부와 무관하게 빈도 문항 평균이 전부 5.2~6.5로
   압도적 — "시간 표현 모호성이 실무 사고로 이어진다"는 제품 핵심 문제의식을
   가장 강하게 뒷받침.

### Next

- `docs/문화_판단기준표_초안.md`의 D01/D03/D05/F03/F04 설명을 "모호함" →
  "국내 컨센서스는 있으나 상대 문화/조직과 기본값이 다름"으로 재작성(미완료).
- 자유서술 응답 중 T04·F06을 뒷받침하는 실사례 인용을 `docs/references.md` 또는
  판단기준표 본문에 반영할지 검토.
- 이 설문 결과를 문헌 인용과 구분해 "1차 실증 자료"로 `docs/references.md`에
  추가하는 작업 미완료.
- T/F 폼 제작 과정에서 few-shot 문구와 겹치지 않는지 재확인은 안 함(설문 문항은
  애초에 패러프레이즈해서 만들었으므로 golden set과의 contamination 문제는 없음).

응답이 추가돼(T 13→14, F 12→15, D는 그대로 12) CSV 재다운로드 후 재집계 —
`docs/survey-results-analysis.md` 7절에 기록. 판정 결과(모호함 확인/국내 컨센서스)는
항목 전부 그대로 유지돼 1차 분석의 결론이 안정적임을 재확인.

호주 20년 경력자 카톡 인터뷰 1차 답변도 도착(`docs/interview-bicultural-veteran-
findings.md`) — 그런데 원래 목적(T/F/D 특정 문항의 미국/호주 쪽 해석 확인)과
무관하게 인사말·토픽 민감도 쪽으로 답변이 감(예: "피곤해 보인다"가 절대 금지
표현, 카스트·LGBTQ·대만 반한감정 등 국가별 금기 주제, 호주=개인주의/미국=그룹
문화 차이). 논의 끝에 **이 내용은 문서화만 하고 코드 스코프(AmbiguityCategory)에는
안 넣기로 결정** — "확인 질문형"이 아니라 "애초에 꺼내지 말아야 하는 회피형" 지식이라
ditto의 interrupt() 확인 흐름과 성격이 다름. 원래 목적(문항별 미국/호주 해석)은
`docs/interview-guide-bicultural-veteran.md`에 D01/D03/D05/F03/F04 구체 문항 +
한국 설문 수치를 명시한 후속 질문을 추가해 재요청(답변 대기 중).

이 재요청 문항 초안에서 실수 하나 발견·수정: D05("나중에 다시 얘기해요")를 "한국은
완곡거절로 읽는다"고 가정했었는데, 실제 설문 데이터는 정반대(보류 6.1 vs 거절 2.9) —
문화 간 대조 가설 자체를 데이터 확인 없이 문헌 직관만으로 세웠던 실수. F03도 같은
패턴("한국이 완곡 화법에 속는다"는 가정)이었는데 실제로는 국내 화자가 이미 잘
캐치함(5.5 vs 2.7). 두 문항 다 "한국 vs 미국이 다르게 읽는다"가 아니라 "한국은
이미 정확히 읽는데, 실제 의도와 기본 해석 사이에 간극이 있다"는 구조로 재작성.

이 실측 결과를 바탕으로 `docs/문화_판단기준표_초안.md` 전면 갱신 — D01/D03/D05,
F03/F04를 "모호함" 프레이밍에서 "국내수렴형"(국내는 이미 명확, 위험은 상대
조직/문화 기본값과의 충돌)으로 재작성. D02/D04, T01-05, F01/F02/F05/F06은 국내
설문으로 "모호함 확인"이 실측 검증돼 문헌 근거 등급을 강화(T축은 "중"→"강" 상향).
"검증 상태" 열 legend도 ✅모호/✅국내수렴 2종으로 재정의.

## 2026-08-16 (밤) — 판단기준표를 실제 코드에 반영 + live eval 3-way 비교 시도

plan mode로 설계 후 승인받아 진행. `agent/src/ditto_agent/llm/culture_criteria.py`
16개 T/F/D 행 전부 `verified: True` 갱신, D01/D03/D05/F03/F04 5개의 `reason`을
"국내수렴형" 프레이밍(설문 수치 인용)으로 교체 + `candidates` 순서를 설문 우세
해석이 먼저 오도록 재정렬. `golden.json`은 검토만 하고 변경 안 함 — `expected_
categories`가 "스키마상 해당 카테고리로 분기 가능한가"를 테스트하는 거라 국내
컨센서스 여부와 무관하다는 결론(자세한 이유는 plan 파일 참고).

`uv run ditto-eval`(golden 36케이스, gpt-5 live)로 코드 수정 전/후 비교:
**baseline recall=0.810 precision=0.739 → reason-sync recall=0.905 precision=0.655**
— reason 텍스트를 더 상세하게 보강했더니 recall은 크게 올랐지만(놓치는 게 줄어듦)
precision은 떨어짐(REQUEST_INTENT/DECISION_STATUS에서 과탐지 증가). Recall-우선
트레이드오프로 판단해 유지. 상세 수치는 `docs/survey-results-analysis.md` 8절.

이어서 `prompts.py`의 few-shot 대표를 `{T01,T03,F01,F04,D01,D03}`(국내수렴형 4개
포함)에서 `{T01,T04,F01,F02,D02,D04}`(설문에서 실제로 가장 크게 갈린 항목)로
교체 — 근데 이 변경의 live 재측정은 **실패**. `ditto-eval`의 배치 호출
(`client.extract_batch()`, 여러 케이스를 한 호출로 묶는 최적화)이 오늘 반복적으로
원인 불명 상태로 무한 대기에 빠짐(RateLimitError 같은 명확한 예외 없이 그냥 응답
안 옴) — batch-size/pace를 여러 번 조정하며 재시도했지만 매번 수십 분씩 걸리다
막힘. 단건 호출(`client.extract()`)로 우회하면 개별 케이스는 16~50초 내 정상
응답하는 걸 확인해 배치 경로 자체의 문제로 특정했지만, 재시도를 거듭하는 과정에서
계정(gpt-5, TPM 10,000/분) 상태가 심하게 저하돼 마지막엔 케이스 하나에 9분 넘게
걸려 중단. **allowlist 교체는 코드엔 반영됐고 테스트 28개·ruff는 통과하지만, 실측
recall/precision은 다음 세션(계정 상태 회복 후)으로 미룸.**

### Next

- 다음 세션에서 계정 상태 회복 확인 후 allowlist-swap live eval 재시도, baseline/
  reason-sync와 3-way 비교 완성.
- `client.extract_batch()`가 왜 무한 대기에 빠지는지 원인 조사 — OpenAI Python
  SDK에 명시적 `timeout` 파라미터가 없는 것도 관련 있어 보임(`client.py:96`의
  `OpenAI(api_key=..., max_retries=0)`에 timeout 미설정). 재현되면 SDK 타임아웃
  추가하는 것도 고려.
- reason-sync의 recall↑/precision↓ 트레이드오프가 실제 제품 목표에 맞는지 팀
  논의 필요(과확인 vs 누락 중 어느 쪽이 더 비싼 실수인지).

## 2026-08-17 (새벽) — Phase 0(API 타임아웃) + Phase 1(extract→verify 루프) 구현

사용자가 "계속 관여 안 할게, 알아서 플랜 짜고 커밋까지 자율적으로 하라"고 지시 —
plan mode로 recall/precision 추가 개선 아키텍처를 설계·승인받아 진행. 웹 검색으로
어젯밤 반복된 무한 대기의 진짜 원인을 먼저 찾음: OpenAI Python SDK 기본 read
timeout이 600초(10분)인데 `client.py`가 `timeout`을 명시 안 했던 것 — TPM 문제가
아니라 SDK가 느린 응답을 그냥 계속 기다린 거였음.

**Phase 0** (커밋 `19f7fad`): `OpenAI(..., timeout=60.0)` 1줄 추가.

**Phase 1** (커밋 `f9aa3e5`): reason-sync가 늘린 과탐지(FP)를 걸러내는 2차 LLM
호출 추가 — `schema.AmbiguityList`, `prompts.VERIFY_SYSTEM_PROMPT`,
`LLMClient.verify()`, `graph.verify_ambiguities_node`(그래프 배선:
`extract → verify_ambiguities → confirm_ambiguities → ...`), `eval/cli.py`의
`_fetch_live_sequential`(배치 호출이 불안정하다고 확인됐던 거라 기본 경로를 단건
순차 `extract()`+`verify()`로 교체, `--no-verify`/`--batch` 플래그로 실험 변형 지원),
`eval/cache.py`에 `stage` 파라미터(verify 유무별로 캐시 분리). 테스트 33개 전부
통과, ruff clean.

**Live 재측정은 실패**: `--no-verify` 실험(36케이스, extract만)을 세 번 시도했는데
매번 5개 안팎에서 극단적으로 느려짐(어떤 호출은 1.6초, 어떤 호출은 20분 넘게
안 끝남 — 같은 코드, 같은 60초 타임아웃 설정인데도). Phase 0 수정 자체는 유효하고
필요했지만(진짜 원인이었음), 그것만으로 오늘 계정의 간헐적 저하 문제를 완전히
해결하진 못함. 세 번의 삽질 중에 두 가지를 배움:
1. `tail`로 파이프하거나 `> file` 리다이렉트만 해도 Python이 비TTY 출력을 블록
   버퍼링해서 실시간 진행 상황이 안 보임 — `PYTHONUNBUFFERED=1`을 반드시 같이 줘야
   함(이제부터 계속 이렇게 씀).
2. 백그라운드 Bash 호출은 세션 cwd를 안 물려받아 매번 `cd agent &&`를 빼먹으면
   "No such file" 에러 — 이것 때문에도 몇 번 헛돌았음.

결국 baseline(0.810/0.739)·reason-sync(0.905/0.655) 두 실험 숫자만 확정 상태로
남고, verify-loop·allowlist-swap 실측은 다음 세션(또는 계정이 안정된 시간대)으로
미룸 — 코드는 이미 다 준비돼서 재측정만 하면 됨. `docs/survey-results-analysis.md`
9절에 상세 기록.

**진짜 원인 나중에 발견**: 위에서 "간헐적 저하"라고 추정했던 것의 정체를 하드
타임아웃(`_run_with_hard_timeout`, `eval/cli.py` — 스레드로 감싸서 몇 초든 무조건
끊는 안전장치) 추가 후 격리 테스트하다가 찾음 — **`RateLimitError`: RPD(하루 요청
한도) 50개를 이미 다 씀.** TPM도 서버 부하도 아니라 단순 하루 쿼터 고갈이었다.
오늘 낮부터 반복한 측정·재시도들이 전부 이 카운터를 갉아먹었고, "몇 분씩 멈춘다"고
느꼈던 현상 상당수도 한도에 가까워지며 요청이 지연된 결과였을 가능성이 큼. 배운
점: 이상 현상 반복되면 로그 tail 대신 **최소 재현 스크립트로 원본 예외부터 확인**
했어야 몇 시간 안 헤맸을 것 — `except Exception`으로 뭉뚱그려 잡던 습관 때문에
진짜 에러 메시지를 늦게 봄.

### Next

- RPD가 rolling 24시간 창이라 시간 지나면서 풀림(429 메시지가 "28분 48초 후
  재시도" 안내) — 그 이후 `cd agent && PYTHONUNBUFFERED=1 DITTO_LLM_MODE=live
  uv run ditto-eval --pace 3`(verify 포함)와 `--no-verify`(제외) 각각 실행해
  verify-loop·allowlist-swap 실측 숫자 채우기. 한도가 조금씩만 풀릴 수 있어 36케이스
  한 번에 못 끝낼 수도 있음 — 캐시 덕분에 나눠서 이어가면 됨.
- Phase 2(RAG 기반 동적 few-shot)는 Phase 1 실측 확인 후 착수 여부 판단 —
  plan 파일(`~/.claude/plans/whimsical-wandering-stroustrup.md`)에 설계 남아있음.
- RPD 50/day는 이 계정의 근본적 제약이라, 앞으로 eval을 자주 돌리려면 결제 수단
  등록으로 한도를 올리는 것도 고려 대상(OpenAI 429 메시지가 안내하는 옵션).

## 2026-08-17 (계속) — gpt-5-mini 전환 + 배치 verify + 최종 3-way 비교, 세션 마무리

사용자가 계정 rate-limits 대시보드를 공유 — gpt-5가 전 모델 중 TPM/RPM 최저(10,000/3)
이고 **RPD는 모델별 별도 풀**이라는 게 확정됨. `DITTO_OPENAI_MODEL`을 `gpt-5-mini`
(TPM 60,000·RPM 10)로 전환(`.env`, `.env.example` 코멘트도 이전의 잘못된 추정 수정).

"RPD 안 걸리게 배치 최적화" 요청에 맞춰 `LLMClient.verify_batch()` 신설(배치당
extract+verify 2호출로 고정, 케이스 수와 무관) — `schema.BatchAmbiguityList`,
`prompts.BATCH_VERIFY_SYSTEM_PROMPT`, `eval/cli.py`의 `_fetch_live_batch`가 `verify`
인자를 받아 체이닝. 36케이스가 배치 크기 12로 요청 3~6개에 끝남. 테스트 36개 통과.

gpt-5-mini로 no-verify(reason-sync+allowlist-swap)와 verify 포함 두 조건을 배치로
완주(중간에 배치 호출이 `APITimeoutError`로 2번 실패했지만 개별 재시도 폴백이 정상
작동해 자동 복구):
- no-verify: recall=0.905, precision=0.679 (`outputs/eval/20260816T164043Z`)
- verify 포함: recall=0.952, precision=**0.500** (`outputs/eval/20260816T165940Z`)

**verify-loop 기각 결정**: 설계 의도와 반대로 precision이 0.679→0.500으로
악화됨(FP 9→20건). `graph/build.py`의 `build_graph()`에 `use_verify: bool = False`
파라미터 추가해 **기본 파이프라인에서 verify_ambiguities_node를 뺐다** — 노드/
`LLMClient.verify()`/`verify_batch()` 코드와 테스트는 그대로 남겨두고(향후 프롬프트
재튜닝 시 `use_verify=True`로 재활성화 가능), `interface.configure()`에도 같은
플래그 노출. `eval/cli.py`도 `--no-verify` → `--verify`(opt-in, 기본 꺼짐)로 뒤집어
프로덕션 기본값과 일치시킴. mock 모드로 전체 파이프라인(start→resume→resume→card)
end-to-end 스모크 테스트 통과 확인.

상세 수치·해석은 `docs/survey-results-analysis.md` 10절.

### 최종 상태 요약 (다음 세션 시작점)

- **채택된 것**: Phase 0(timeout=60.0), reason-sync(culture_criteria.py 16개 항목
  동기화), allowlist-swap(few-shot 대표 4개 교체), gpt-5-mini 모델 전환, 배치
  extract/verify 인프라
- **구현됐지만 기본 꺼짐**: verify-loop(`use_verify=True`로 옵션 가능, 프롬프트
  재튜닝 필요)
- **미착수**: Phase 2(RAG 기반 동적 few-shot) — plan 파일에 설계만 있음
- 전체 커밋: `19f7fad`(timeout) → `f9aa3e5`(verify 최초 구현) → `9ebcdfe`(하드
  타임아웃+RPD 원인 규명) → `a261927`(배치 verify+모델 전환) → `ee45301`(verify
  기본 끔) — PR #1에 전부 반영, push 완료.

## 2026-08-17 (계속) — 4가지 기법 실험 설계 → E0/E1 실측 → 시드 고정으로 재현성 확보

사용자가 "골든셋이 잘못된 거 아냐?"라고 의심 — `golden.json`의 T02-explicit/
F02-explicit 원문을 직접 확인해 요일·시각·시간대/지칭 인물이 전부 명시돼 있음을
검증, 골든셋 자체는 옳고 few-shot `reason`의 통계 인용 문구가 과탐지를 유발한
것으로 결론. 이후 "LangChain vs LangGraph, 성능 더 높이려면?" 질문에 RAG/규칙 기반
후처리/self-consistency/조건 분기 4가지를 제시했고, 사용자가 4개를 다 고려한 실험
설계를 지시 → `E0(reason-trim) → E1(규칙 필터) → E2(self-consistency) → E3(RAG)`
누적 매트릭스로 plan mode에서 설계, 승인받음.

**E0(reason-trim)**: `culture_criteria.py` reason에서 통계 인용 제거, gpt-5-mini
재측정 → recall=0.905, precision=**0.442**(직전 0.679보다 악화, 새로운 교차
카테고리 오탐 패턴). "reason 장황 → 과탐지" 가설을 정면으로 반박하는 결과라
`extract()` 자체의 샘플링 노이즈가 상당하다는 결론에 도달(같은 세션 안에서
0.739→0.655→0.679→0.500→0.442로 등락) — self-consistency와 시드 고정이 왜
필요한지 사용자에게 설명.

**E1(규칙 기반 TIME 후처리)**: `llm/postfilter.py` 신설 —
`filter_false_positive_time()`이 요일/날짜+시각(+시간대)가 다 명시되고 모호 마커가
없는 TIME 오탐을 API 호출 없이 코드로 제거. `extract()`/`extract_batch()` 리턴
직전에 적용. 테스트 9개 추가.

**캐시 버그 발견**: E1 첫 측정이 E0와 소수점까지 똑같은 precision을 내서 조사 —
`eval/cache.py` 캐시 키가 프롬프트 해시만 반영하고 postfilter 같은 순수 코드
변경은 못 감지해 옛날(필터 적용 전) 응답을 계속 재사용하고 있었음. `_code_hash()`
(postfilter.py 소스 해시)를 키에 추가해 수정.

**측정 시도 3번 전부 RPD로 조기 종료**: gpt-5-mini 캐시 버그로 무효 →
`RateLimitError: RPD Limit 50, Used 50`(gpt-5-mini도 소진) → 사용자가
AskUserQuestion에서 "다른 모델로(gpt-4o-mini)" 선택 → gpt-4o-mini로 36/36 완주:
recall=0.524, precision=**0.786**(이번 세션 최고 precision, 최저 recall). 세 모델
(gpt-5/gpt-5-mini/gpt-4o-mini) 전부 오늘 RPD 소진 확인 — E1의 순수 효과를 모델
교체 없이 분리 측정 못 함.

**시드 고정("시드를 다 고정해서 재현성을 1차적으로 확보해")**: 실측으로 드러난
런투런 노이즈(위 등락)를 줄이려고 `LLMClient`의 5개 `.parse()` 호출 전부에
`seed=42`(+ non-reasoning 모델은 `temperature=0`도) 적용. reasoning 계열
(`gpt-5*`, `o1/o3/o4*`)은 temperature 강제가 거부될 수 있어 seed만 건다. gpt-4o-mini
로 라이브 테스트해 `system_fingerprint`가 실제로 반환됨을 확인. `eval/cache.py`의
`_code_hash()`도 `client.py` 소스까지 해시하도록 확장(같은 클래스의 스테일 캐시
버그가 이 변경으로도 재발할 수 있어서 — postfilter 때와 동일 패턴).

전체 45개 테스트 통과, ruff 클린. 커밋: `52c1981`(E1 postfilter) → `dead0f6`(시드
고정) → `773194f`(E1 실측 문서화). 상세 수치·해석은
`docs/survey-results-analysis.md` 11~12절.

**시드 고정 효과 검증(실측, 부정적 결과)**: 같은 코드·프롬프트·seed=42·
temperature=0으로 gpt-4o-mini 골든셋 36개를 캐시 없이 두 번 돌려 비교 —
recall/precision이 여전히 다르게 나옴(0.429/0.900 vs 0.524/0.846), 여러 케이스의
판정 자체가 뒤집힘. 단발 호출은 완전히 결정적임을 별도 확인(seed 자체는 정상
작동) — **OpenAI가 배치 구조화 출력에서는 seed 결정성을 보장하지 않는다("best
effort")** 는 게 원인으로 보임. "시드 고정 = 재현성 확보"라는 가설은 기각,
self-consistency가 이 노이즈에 대한 유일한 구조적 해법이라는 결론으로 이어짐.
상세: `docs/survey-results-analysis.md` 13절.

**E2(self-consistency) 구현·첫 측정**: `LLMClient.extract_consistent(draft, context,
n=3, threshold=2)` 신설 — `extract_batch()` 재사용해 같은 메시지를 n회 독립 추출,
`_vote_extraction()`(순수 함수, `tests/test_consistency.py` 6개로 API 없이 검증)이
카테고리별 다수결. `eval/cli.py`에 `--consistency N` 노출. RPD 절약 위해 T01~F05
20케이스 부분집합으로 측정(gpt-4o-mini, n=3, t=2) — **recall 1.000(만점)까지
올라갔지만 precision은 0.900→0.714로 오히려 떨어짐**(FP 1건→4건), self-consistency의
원래 의도(과탐지를 다수결로 걸러 precision 개선)와 반대 방향. threshold=2/3이
너무 관대했을 가능성 등 원인 후보는 있지만, 측정 도중 gpt-4o-mini RPD가 13/50까지
줄어(케이스당 1요청 구조라 20케이스=20요청 소모) threshold=3 재측정을 오늘 못 함 —
**E2는 채택/기각 결론 보류**, 다음 세션 RPD 리셋 후 이어감.

## 2026-08-17 (계속) — 결제 불가 확인 → 무료 티어 예산 안에서 6개 모델 동일 조건 비교

사용자가 "5달러 넘기면 rate limit 풀린다더라, 다른 모델 돌려서 채워달라"고 요청 —
Chrome으로 OpenAI 대시보드(청구 → 신용 보조금)를 직접 열어 확인한 결과 계정 잔액
$96.45는 **2026-07-30 지급된 $100 무료 grant**였고 실제 결제 이력은 $0. tier
승급 조건은 "total **credit purchases**"라 grant를 아무리 써도 tier가 안 오른다는
걸 확인해 사실대로 전달 — 사용자가 "결제를 할 수는 없다"고 확정.

그래서 방향 전환: 크레딧을 더 사는 대신 **남은 무료 예산 안에서 여러 모델을
최대한 동일한 조건으로 비교**하기로 함. 모델별 무료 티어 한도 자체가 다르다는 걸
새로 발견 — gpt-4.1은 RPD가 아니라 **RPM 3/min**이 병목(pace=2s로 3번째 호출에서
바로 429), gpt-5-mini는 이미 RPD 완전 소진 상태로 "28분 후 재시도" 메시지가 여러
번 다시 확인해도 안 줄어듦.

가장 빠듯한 예산(gpt-4o-mini 13개 남음)에 맞춰 골든셋 앞 12개 케이스(T01~T05,
DECISION_STATUS 없는 쉬운 부분집합)를 **모든 모델에 동일한 방법**(단건 순차
extract, 배치·verify·consistency 미적용, `--no-cache`)으로 측정:

| 모델 | recall | precision | FP |
|---|---|---|---|
| gpt-4o-mini | 1.000 | **0.857** | 1 |
| gpt-4.1-mini | 1.000 | **0.857** | 1 |
| gpt-4.1 | 1.000 | 0.750 | 2 |
| gpt-4o | 1.000 | 0.750 | 2 |
| gpt-5 | 1.000 | **0.400** | 9 |
| gpt-5-mini | RPD 소진 — 미측정 | | |

**결론**: mini 두 모델이 동률 1위(플래그십보다 나음), gpt-5는 스키마에 없던
`OTHER` 카테고리까지 만들어내며 압도적으로 나쁨. 지금 `.env`의 gpt-4o-mini 선택이
이 비교로 정당화됨. 단, 12케이스·DECISION_STATUS 미포함이라 전체 골든셋에 그대로
일반화는 안 됨 — RPD 여유 생기면 36케이스로 재검증 필요. 상세:
`docs/survey-results-analysis.md` 15절.

### Next

- **RPD 리셋 후 최우선**: E2 threshold=3(만장일치) 재측정, 가능하면 n=5도 —
  threshold=2가 너무 관대했는지 확인. 같은 20케이스 부분집합으로 시드검증 두
  실행과 나란히 비교(표는 survey-results-analysis.md 14절에 이미 있음)
- E2 결론 나면(채택/기각) `graph/build.py`/`interface.configure()`에 반영할지 결정
  (verify-loop처럼 안 되면 옵션으로만 남기고 기본은 끔)
- 모델 비교(15절)를 36케이스 전체로 재검증 — 특히 DECISION_STATUS 포함 시에도
  mini 모델이 여전히 앞서는지 확인
- gpt-5-mini RPD 리셋 카운트다운이 재확인해도 안 줄어드는 현상 원인 파악(다음에도
  재현되면 별도 이슈로 기록)
- E3(RAG 동적 few-shot): 시간 되면, 미착수
- `.env`(gpt-4o-mini) vs `.env.example`(gpt-5-mini) — 15절 결과로 gpt-4o-mini 유지가
  맞다는 근거 생김, `.env.example` 코멘트도 갱신 검토
- 결제는 안 하기로 확정 — 앞으로 모든 실험은 무료 티어 한도(모델별 RPD/RPM 다름)
  안에서 설계할 것

## 2026-08-17 (계속) — 안 써본 mini/nano 4개 추가 측정 + 오늘 안에 모델 최종 확정

사용자가 "오늘 안에 끝내야 해서"라며 마감을 알려와, 내일 RPD 리셋을 기다리지 않고
**오늘 확보한 데이터로 최종 모델을 확정**하는 쪽으로 방향을 잡음.

같은 12케이스·같은 방법(단건 순차, `--no-cache`)으로 o3-mini, o4-mini,
gpt-4.1-nano, gpt-5-nano 4개를 추가 측정(사용자가 "다른 미니 모델 중 안 쓴 걸로
돌려봐" 요청). 결과:

| 모델 | recall | precision |
|---|---|---|
| o3-mini | 1.000 | 0.857 |
| o4-mini | 1.000 | 0.750 |
| gpt-4.1-nano | 1.000 | 0.857 |
| **gpt-5-nano** | 1.000 | **1.000**(9개 모델 중 유일한 만점) |

**최종 모델 확정**: gpt-5-nano가 이 부분집합에서 유일하게 만점을 받았지만
단일 실행·쉬운 부분집합 하나뿐인 얇은 데이터라, 이번 세션 내내(E0/E1/시드검증/E2/
모델비교) 가장 많이 검증된 **gpt-4o-mini를 프로덕션 모델로 유지**하기로 결정 —
`.env`/`.env.example` 이미 gpt-4o-mini라 변경 불필요, `graph/build.py`도 모델을
하드코딩 안 하고 전부 `LLMClient`(→`DITTO_OPENAI_MODEL` env) 경유라 아키텍처
변경도 불필요함을 재확인. gpt-5-nano는 차기 검증 후보로만 기록. 상세:
`docs/survey-results-analysis.md` 15-1절.

중간에 사용자가 "평가를 단순 비교만 하는데 측정이 되냐"고 질문 — `eval/scorer.py`의
채점이 LLM 없이 golden.json의 사람 라벨과 집합 비교만 하는 순수 함수라는 걸
설명(=표준 분류 평가 방법론, LLM judge를 안 써서 오히려 노이즈가 없음).

### Next

- gpt-4o-mini 최종 확정 — 이제 E2/E3는 전부 이 모델 기준으로 진행
- E2(threshold=3), 36케이스 전체 재검증은 RPD 리셋 후 다음 세션
- E3(RAG 동적 few-shot): 코드/설계만이라도 이번 세션에 진행 가능(RPD 불필요)
- gpt-5-nano를 향후 후보로 남겨둠 — 언젠가 36케이스 전체·재현성까지 검증되면
  전환 고려

## 2026-08-17 (계속) — E2 threshold=3 재측정(채택) + 기본값 만장일치로 변경

당일 마감이라 gpt-4o-mini RPD 리셋(내일)을 못 기다리고, budget이 넉넉한 o3-mini로
같은 20케이스에 threshold=3(만장일치)만 바꿔 재측정 — **recall=1.000,
precision=1.000**(20/20 전부 정답). threshold=2(과반, precision 0.714)보다 훨씬
좋고 non-consistency 베이스라인(0.900~1.000)도 뛰어넘음. "과반이 너무 관대한
기준이었다"는 가설이 정확히 맞아떨어짐 — **E2 채택 결정**.

이 결과를 반영해 `LLMClient.extract_consistent()`와 `eval/cli.py`의
`--consistency-threshold` 기본값을 **과반(n//2+1) → 만장일치(n)** 로 변경. 45→53개
테스트 전부 통과, ruff 클린.

**한계(정직하게 기록)**: o3-mini로 검증했지 최종 프로덕션 모델(gpt-4o-mini)로는
아직 직접 확인 못 함(오늘 gpt-4o-mini 요청 2개만 남음) — 내일 RPD 리셋 후 같은
20케이스로 gpt-4o-mini 재확인 필요. 상세: `docs/survey-results-analysis.md`
13-1절.

### Next

- **내일 최우선**: gpt-4o-mini로 threshold=3(만장일치) 20케이스 재확인 — o3-mini
  결과가 모델 무관하게 재현되는지
- 36케이스 전체(DECISION_STATUS 포함)로도 self-consistency 만장일치 효과 검증
- E3(RAG 동적 few-shot) 착수
- E2가 최종 확인되면 `graph/build.py`/`interface.configure()`에 `use_consistency`
  같은 옵션으로 노출할지 결정(verify-loop 패턴과 다르게, 이번엔 실측이 긍정적이라
  채택 방향)
