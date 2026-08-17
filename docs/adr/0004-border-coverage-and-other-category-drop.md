- Title: Cover Border 지리/문화/조직/언어 via existing card fields, drop OTHER category
- Status: Accepted
- Date: 2026-08-16
- Context: 멋쟁이사자처럼 트랙(Notion, https://likelion.notion.site/Track-3a344860a4f480b3b60edb40fc90706a)
  확인 결과 심사 기준이 4개 경계(지리/언어/문화/조직) 중 실제로 얼마나 넘었는지를
  가장 중요(*표시)하게 본다. 이 시점까지 `ditto_agent`는 지리(TIME)·문화
  (REQUEST_INTENT)만 실질적으로 커버했고, 조직(DECISION_STATUS)은 문화 축(Meyer의
  Deciding)에 억지로 맞추려다 근거가 약하다고 오판했었고, 언어는 완전히 비어있었다.
  동시에 골든셋 40/40 완주 결과 OTHER(C01-04, Communicating 축)만 recall 0/3이었고,
  문헌 조사로 "간접화법/톤 해석은 최고 성능 LLM도 사람 수준 미달"이라는 구조적 한계가
  확인됐다(`docs/research-other-category.md`).
- Options:
  1. OTHER를 억지로 살리려 스키마를 새로 설계(후보 선택이 아니라 경고 단발성 알림
     구조 등)하고, 조직/언어는 새 UI/새 필드로 별도 추가.
  2. OTHER는 스코프에서 빼고(스키마는 안전하게 유지), 조직·언어는 **기존 카드
     필드에 AI 출력을 더 정교하게 채우는 것만으로** 해결 — 새 UI 없이.
- Decision: Option 2.
  - **조직(Border 04)**: `decision_status`를 자유 텍스트 대신
    `DECISION_STATUS_VOCABULARY`(최종 확정/임시 시도(재논의 가능)/1차 완료(추가
    승인 필요)/제안(결정 아님)/보류/미정) 6개 고정 어휘로 정규화하도록 프롬프트
    지시 — "승인"/"완료"/"컨펌"의 조직별 의미 차이를 AI가 흡수. 카드의 기존
    `결정 상태` 필드가 그대로 이 값을 받는다.
  - **언어(Border 02)**: `DraftContext.receiver_lang` 추가, 그래프에
    `build_card_node` 다음 `translate_card_node`를 붙여 카드의 자유 텍스트
    (`task`/`request_type`/`interpretation_note`/`notes`)만 번역. **모호성 확정
    이후에만 번역**하도록 순서를 고정 — 먼저 번역하면 번역기가 여러 해석 중 하나를
    암묵적으로 골라버려 발신자가 명시적으로 확정하기 전에 모호성이 사라지는,
    이 프로젝트의 핵심 원칙(AI가 임의로 확정하지 않는다) 위반이 생긴다.
    `evidence`(원문)와 타임스탬프 등 구조화된 필드는 번역하지 않는다.
  - **OTHER**: `prompts.py`의 few-shot에서 카테고리 필터링으로 제외,
    `golden.json`에서 C01/C03 페어 삭제(C02는 TIME 부분만 남기고 재작성). 단
    `AmbiguityCategory` Literal과 `notes` 필드(카테고리 무관 캐치올)는 그대로 둬서
    live 모델이 어쩌다 OTHER를 내도 크래시 없이 안전하게 처리되게 유지 — 재도입
    비용을 낮게 유지.
- Consequences: 새 UI 컴포넌트 없이 기존 Figma 카드 슬롯만으로 3/4 경계(지리·문화·조직)를
  실질적으로 커버하고, 언어까지 더하면 4/4. 다만 `decision_status`는 강한 프롬프트
  지시일 뿐 하드 `Literal` 타입 검증은 아니다 — `confirm_ambiguities_node`가 사람이
  고른 candidate 문구를 그대로 `decision_status`에 꽂는 경로가 있어서, 그 문구가
  6개 어휘와 정확히 안 맞으면 정규화가 깨질 수 있다(추후 정규화 매핑 레이어 추가
  검토 여지). OTHER를 나중에 되살리려면 `prompts.py`의 필터 한 줄과
  `golden.json`에 페어를 다시 추가하면 된다 — 데이터/스키마는 안 지웠으므로 재도입
  비용이 낮다.
