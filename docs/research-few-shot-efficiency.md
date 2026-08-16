# 리서치: few-shot 개수와 정확도/효율 관계

> 배경: golden.json 40/40 완주에서 T02/T04-explicit 같은 잔여 오탐이 있었고,
> 동시에 gpt-5 TPM(분당 토큰) 한도에 계속 걸렸다. "few-shot을 더 다듬으면 정확도가
> 오를까, 아니면 줄이는 게 정확도와 효율 둘 다에 도움이 될까"를 확인했다.

## 검색 결과

- **["Few-Shot Learning for LLMs"](https://tetrate.io/learn/ai/few-shot-learning-llms)**
  등 여러 자료: 많은 태스크에서 성능이 **5~7개 예시 이후 정체**된다. 추가해도 의미
  있는 개선이 없는 지점이 존재.
- **["When More Examples Make Your LLM Worse: Discovering Few-Shot Collapse"](https://shuntaro-okuma.medium.com/when-more-examples-make-your-llm-worse-discovering-few-shot-collapse-d3c97ff9eb01)**:
  예시 0개(67.23%) → 100개(53.94%)로 늘렸더니 **정확도가 오히려 13%p 하락**한
  사례. 예시가 과하면 모델이 지시를 정확히 못 따르고 산만해질 수 있음.
- **["Ensuring Reliable Few-Shot Prompt Selection for LLMs"](https://www.kdnuggets.com/2023/07/ensuring-reliable-fewshot-prompt-selection-llms.html)**:
  "3개의 잘 고른 예시가 10개의 중복된 예시보다 낫다" — 개수보다 **다양성/대표성**이
  중요.
- **AT-CoT(Ambiguity Type-Chain-of-Thought)**: 모호성 유형을 먼저 판단하게 하는
  기법 — 우리 스키마의 `category`/`reason` 필드가 이미 이 역할을 부분적으로 하고
  있음(참고만, 이번엔 반영 안 함).
- **Self-verification 2-pass**: 2차 LLM이 1차 결과를 재검증하면 오탐이 크게
  줄어든다는 연구(F1 +0.04~0.25)가 있으나, **호출이 2배로 늘어 이번 세션 내내
  겪은 RPD/TPM 문제를 악화**시킨다 — "효율적으로"라는 목표와 반대 방향이라 채택
  안 함.

## 결정

`culture_criteria.py`의 20개 중 OTHER(C01-04, 이미 제외) 외에 TIME/REQUEST_INTENT/
DECISION_STATUS 16개도 **카테고리당 대표 2개씩(T01/T03, F01/F04, D01/D03)만 남기고
축소** — 부정 예시 5개는 그대로 유지(이건 "예시가 없어서" 생긴 편향을 잡는 용도라
줄이면 안 됨).

- 예시 21개 → 11개
- 프롬프트 길이 ~5.2K자 → ~3.0K자 (약 42% 감소)
- 정확도·토큰 비용 둘 다 개선될 것으로 기대 — **실 API로 아직 재검증 못함**(한도
  문제, 다음 세션 TODO)

## 참고: 왜 하필 이 6개를 남겼나

카테고리 내에서 서로 다른 하위 패턴을 대표하도록 골랐다 — 중복 줄이고 다양성
확보(위 "3개의 잘 고른 예시" 원칙):

- T01(시간대 불명확) / T03(우선순위 모호성 — 다른 종류의 시간 모호성)
- F01(KR→US 완곡한 반대) / F04(US→KR 축소 해석 위험 — 반대 방향)
- D01(임시 vs 최종) / D03(승인 vs 단순 확인 — 다른 종류의 결정상태 모호성)

## 다음

- 실 API 쿼터 확보되면 `uv run ditto-eval`로 T02/T04-explicit 등 잔여 오탐이
  실제로 줄었는지 재확인.
- 만약 개선이 없거나 recall이 떨어지면, 6개가 너무 적을 수 있음 — 8~10개
  (카테고리당 3개 안팎)로 재조정 검토.
