# ditto — 오해 방지 레이어 (Misunderstanding Prevention Layer)

Slack·Teams 등 협업툴 위에 붙는 AI 플러그인형 B2B SaaS. 비동기 메시지의 시간·요청
의도·결정 상태 모호성을 감지해, 발신자가 스스로 의도를 확인한 뒤 수신자에게 명시적인
업무 조건으로 전달하도록 돕는다. 멋쟁이사자처럼 14기 중앙해커톤 "보더리스 협업" 트랙
프로젝트.

**이 저장소는 AI 모델(LLM 프롬프트 + LangGraph 에이전트) 파트만 다룬다** — FastAPI
라우터/DB/프론트엔드는 다른 팀원이 별도 저장소에서 관리한다.

## 구조

```
agent/    ← 전부 여기. LangGraph 에이전트, 골든셋 평가 하네스, 테스트.
docs/     ← 판단기준표(문화/조직 경계 대응 근거)
```

## 무엇을 하는가

메시지 하나를 넣으면:
1. TIME(모호한 기한) / REQUEST_INTENT(완곡한 의사표현) / DECISION_STATUS(조직마다
   다른 "완료"의 뜻) 세 카테고리로 모호성을 감지
2. 모호성이 있으면 LangGraph `interrupt()`로 멈춰서 발신자가 직접 확정하게 함
   (모호성이 없으면 안 멈추고 바로 진행 — 불필요한 확인 요청 안 함)
3. 확정된 내용으로 수신자용 "공동 이해 카드"를 만들어 반환(시간대 변환, 근무시간
   충돌 검사, 필요 시 번역까지 포함)

## 시작하기

```bash
cd agent
cp .env.example .env   # DITTO_LLM_MODE=mock이면 OPENAI_API_KEY 없이도 동작
uv sync
uv run pytest
uv run python examples/cli_demo.py   # 서버 없이 터미널에서 전체 흐름 확인
```

백엔드/프론트엔드 연동에 필요한 전부(`start()`/`resume()`/`configure()` API,
정확도 옵션, 환경변수)는 **[`agent/README.md`](agent/README.md)** 에 있다 — 이
저장소와의 유일한 통합 접점.

## 현재 상태

- 판단기준표(`docs/culture-criteria.md`) 16개 항목, 설문(n=12~15)·인터뷰로 1차 검증
- 골든셋(36케이스) 기준 recall 0.810 / precision 0.761 — 오해 방지 도구 특성상 모호성을
  놓치는 것(FN)이 과탐지(FP)보다 치명적이라 recall 우선으로 튜닝(근거:
  `agent/README.md`의 "정확도 설정" 절)
- self-consistency·RAG 동적 few-shot 둘 다 구현·실측했으나 이 규모에서는 기본
  파이프라인보다 낫지 않아 옵션으로만 유지(기본 꺼짐)

## 백엔드 연동

**[`docs/backend-handoff.md`](docs/backend-handoff.md)** — 무엇을 넘기고 무엇을
직접 구현해야 하는지 체크리스트.
