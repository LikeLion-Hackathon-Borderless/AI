- Title: Combine C-2/C-3/C-4 into one structured LLM call
- Status: Accepted
- Date: 2026-08-14
- Context: 발신자 초안 하나에서 세 가지를 뽑아야 한다 — (C-2) 업무/담당자/기한/요청
  유형/결정 상태 구조 추출, (C-3) 시간 모호성 감지, (C-4) 의미 모호성 감지(3가지 후보
  해석). 핸드오프 문서가 "지연시간과 비용 절감을 위해 하나의 API 호출로 통합,
  structured JSON output으로 한 번에 반환받는다(다중 호출 체이닝 지양)"고 명시했다.
  프로바이더는 팀이 실사용 가능한 키(OpenAI 조직 플랜) 기준으로 GPT로 확정했다
  (문서 4절의 "Claude API" 최초안을 실사용 키 기준으로 대체) — OpenAI의 구조화
  출력(JSON Schema 강제) 기능으로 스키마 준수를 강제한다.
- Options:
  1. C-2 → C-3 → C-4를 별도 호출 3번으로 체이닝(각 단계 결과를 다음 프롬프트에 주입).
  2. 시스템 프롬프트 하나에 세 작업을 모두 지시하고, 문서 5절 JSON 스키마
     (`span/category/reason/candidates/suggestion` + 구조화 필드)로 한 번에
     응답받기.
- Decision: Option 2. `llm/client.py`는 OpenAI SDK로 `extract()` 함수 하나만 공개하고,
  `llm/prompts.py`의 단일 시스템 프롬프트가 C-2/C-3/C-4 지시와 판단기준표 few-shot을
  모두 포함한다. `graph/nodes.py`의 `extract_node` 하나가 이 함수를 호출해 그래프
  상태에 결과를 채운다 — 별도의 `time_node`/`interp_node` LLM 호출은 만들지 않는다
  (시간·의미 확인을 위한 interrupt 노드는 LLM을 다시 부르지 않고, extract 단계에서
  이미 나온 후보를 사람에게 보여주고 답만 받는다).
- Consequences: 호출 1회로 지연시간·비용은 줄지만, 프롬프트 하나가 여러 역할을 겸해
  스키마가 복잡해진다 — `schema.py`의 `ExtractionResult`가 이 복잡도를 흡수하는
  단일 지점이 되도록 설계한다. 추후 카테고리가 늘어나 프롬프트가 지나치게 커지면
  이 결정을 재검토(체이닝으로 되돌림)할 수 있다.
