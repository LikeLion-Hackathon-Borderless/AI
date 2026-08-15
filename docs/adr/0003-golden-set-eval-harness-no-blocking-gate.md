- Title: Golden-set eval harness reports numbers, does not block on a gate
- Status: Accepted
- Date: 2026-08-15
- Context: 사용자가 이전 프로젝트(`planqa-eval-agent`)처럼 골든셋 기반 정확도 평가를
  `ditto-agent`에도 적용하길 원함. `planqa-eval-agent`를 조사한 결과, 과거에는
  `harness/confidence_gate.py`가 존재했다 — 계층화 샘플링으로 사람 블라인드 라벨을
  뽑고, matcher/judge 합치율이 90%/80%/rule-level 100% 임계값을 넘지 못하면 `2-2 full
  eval`이 `--force` 없이는 아예 실행되지 않는 구조. 이 게이트는 사용자가 2026-08-08에
  직접 삭제했다 — LLM-judge 앙상블의 `ambiguous` 플래그(멤버 간 표준편차로 자동 감지 +
  arbiter 재채점)가 생기면서 별도 사람 게이트가 중복이라 판단했기 때문(`docs/adr/
  0001-review-agent-output-contract.md`의 2026-08-08 Update, `docs/progress.md` 같은
  날짜 항목).
- Options:
  1. planqa의 예전 confidence_gate.py처럼, 임계값 미달 시 "이 상태로는 데모/배포 금지"를
     코드로 강제하는 게이트를 새로 만든다.
  2. planqa의 현재(게이트 삭제 후) 상태처럼, precision/recall/카테고리별 숫자를 계산해
     리포트로 보여주기만 하고 판단은 사람이 한다.
- Decision: Option 2. ditto는 (a) 해커톤 1주일 스코프라 게이트 구축·유지 비용을 들일
  타이밍이 아니고, (b) 애초에 태스크가 planqa보다 훨씬 단순해(문서 N:M 매칭이 아니라
  메시지 1개→카테고리 집합) 사람 블라인드 라벨링 같은 무거운 장치가 덜 필요하며,
  (c) 무엇보다 사용자가 이미 한 번 "게이트가 중복"이라고 실제로 판단해 지운 전례가
  있다 — 그 판단을 다시 뒤집을 근거가 없다.
- Consequences: `ditto-eval`은 항상 실행되고 항상 리포트를 남긴다 — CI에서 "정확도가
  기준 미달이면 머지 금지" 같은 자동화는 없다. 팀이 리포트를 보고 직접 판단해야 하며,
  숫자가 나빠도 코드가 막지 않는다. 나중에 실제로 반복적인 회귀(정확도가 알게 모르게
  나빠지는 사고)가 발생하면, 그때 planqa의 과거 임계값(90%/80%/100%) 같은 구체적
  숫자를 다시 참고해 게이트를 추가하는 걸 재검토한다.
