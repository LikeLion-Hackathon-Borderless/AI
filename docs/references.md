# 참고 문헌 / 레퍼런스

이 프로젝트가 방법론을 가져온 논문·저장소 모음. 각 ADR/문서에서 이름만 언급한 것들의
전체 출처를 여기 모아둔다.

## 문화적 판단기준표 (`docs/문화_판단기준표_초안.md`)

- Erin Meyer, *The Culture Map: Breaking Through the Invisible Boundaries of Global
  Business*, PublicAffairs, 2014. — Scheduling/Evaluating/Disagreeing/Communicating
  4개 축 채택.
- Jiho Jin et al., "KoBBQ: Korean Bias Benchmark for Question Answering", *TACL* 2024,
  [arXiv:2307.16778](https://arxiv.org/abs/2307.16778) —
  [naver-ai/KoBBQ](https://github.com/naver-ai/KoBBQ). 3단계 문화 적응 분류
  (Simply-Transferred / Target-Modified / Sample-Removed) 방법론만 차용 — 데이터셋
  자체는 쓰지 않음.

## golden-set 평가 하네스 (`docs/adr/0003-golden-set-eval-harness-no-blocking-gate.md`)

- Lorenz Kuhn, Yarin Gal, Sebastian Farquhar, "CLAM: Selective Clarification for
  Ambiguous Questions with Generative Language Models",
  [arXiv:2212.07769](https://arxiv.org/abs/2212.07769) — ambiguous/clear 질문을
  **쌍(pair)**으로 만들어 평가하는 방식을 `agent/data/golden.json` 설계에 채택.
- Kun Zhou et al., "Don't Make Your LLM an Evaluation Benchmark Cheater",
  [arXiv:2311.01964](https://arxiv.org/abs/2311.01964) — "prompt contamination"
  (few-shot 예시를 평가셋에 그대로 재사용) 개념의 출처. `culture_criteria.py`의
  20개 phrase를 golden.json에 그대로 안 쓰고 패러프레이즈한 근거.
  EleutherAI [`lm-evaluation-harness` decontamination 문서](https://github.com/EleutherAI/lm-evaluation-harness/blob/main/docs/decontamination.md)도 같은 개념의
  실무적 설명으로 참고.
- Sewon Min et al., "AmbigQA: Answering Ambiguous Open-domain Questions", *EMNLP*
  2020 — [shmsw25/AmbigQA](https://github.com/shmsw25/AmbigQA). ambiguous/clear
  균형 잡힌 held-out 테스트셋 구성 방식을 검토 — 최종적으로는 CLAM의 pair 방식을
  채택했지만 설계 검토 과정에 참고.
- `planqa-eval-agent`(`tools/eval-agent/`, 사용자의 이전 프로젝트) — golden 파싱 →
  채점 → `report.json`/`report.md` 관례, `ConfusionCounts` 설계, 과거
  `harness/confidence_gate.py`(2026-08-08 삭제) 전례. 외부 출처는 아니지만 이
  하네스의 직접적인 구조적 원형이라 기록.

## LangGraph interrupt 아키텍처 (`docs/adr/0001-langgraph-interrupt-for-sender-confirmation.md`)

- [esurovtsev/langgraph-hitl-fastapi-demo](https://github.com/esurovtsev/langgraph-hitl-fastapi-demo)
  — `create`/`stream`/`resume` 3단 FastAPI 엔드포인트 구조 참고.
- [KirtiJha/langgraph-interrupt-workflow-template](https://github.com/KirtiJha/langgraph-interrupt-workflow-template)
  — interrupt + 체크포인터 조합 템플릿 참고.
