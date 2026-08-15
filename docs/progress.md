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
