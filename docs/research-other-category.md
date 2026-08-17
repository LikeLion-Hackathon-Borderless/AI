# 리서치: OTHER 카테고리는 잘 짜여 있는가

> 배경: 골든셋 40개 실행 결과 TIME/REQUEST_INTENT/DECISION_STATUS는 recall 100%인데
> OTHER(C01-04, Communicating 축)만 recall 0%(3/3 전부 놓침)였다. few-shot 문구를
> 실제 발화 예시로 바꿔도 그대로였다(`fix: use real message text for OTHER few-shot`
> 커밋 참고). 이게 프롬프트를 더 다듬으면 풀리는 문제인지, 아니면 애초에 태스크
> 설계 자체가 안 맞는 건지 학술 문헌을 검색해 확인했다.

## OTHER가 감지하려는 것 (재정리)

| ID | 신호 | 성격 |
|---|---|---|
| C01 | 근거 없이 결론만 통보 | 저맥락 문화권 기대치 미충족 |
| C02 | 배경 설명 없는 직접 지시 | 위계/관계 맥락 생략 |
| C03 | 이모지/느낌표 톤 | 친근함 vs 진지함 부족, 해석 갈림 |
| C04 | 침묵(무응답) | 암묵적 동의 vs 미확인 — golden set에서 이미 제외 |

TIME/REQUEST_INTENT/DECISION_STATUS는 전부 "**이 표현이 A를 뜻하는가 B를 뜻하는가**"라는
**복수 해석(multiple-reading)** 구조인 반면, OTHER는 "**이 표현 방식이 문화권에 따라 다르게
받아들여질 수 있다**"는 **간접성/톤(indirectness·tone)** 신호에 가깝다 — 뜻 자체는
명확할 수 있다.

## 검색 결과

### 1. 이론적 뿌리는 확실함

High-context/low-context 커뮤니케이션은 Edward T. Hall의 *The Silent Language*(1959)에서
나온 확립된 커뮤니케이션 이론이다. 문제는 이론이 아니라 **이걸 자동 감지하는 NLP 태스크가
얼마나 성숙했는가**다.

### 2. 하위 신호별로 성숙도가 크게 다름

- **Hedging/politeness 탐지 (C01·C02에 가까움)**: 성숙한 태스크다. Danescu-Niculescu-Mizil
  et al. (2013)의 [Stanford Politeness Corpus](https://nlp.stanford.edu/pubs/politeness.pdf)가
  Brown & Levinson 공손 이론 기반 언어 자질로 SVM 분류기를 학습했고 지금은
  [ConvoKit](https://convokit.cornell.edu/documentation/wiki_politeness.html)에 통합돼
  있다. Hedging 탐지 자체도 Madaio et al. (2017) 81% 정확도 → Raphalen et al. (2022)
  weighted F1 0.97까지 발전했다. → **C01/C02는 원래 "복수 해석"보다 "탐지 가능한 별도
  분류 태스크"에 더 가깝다는 뜻** — 지금처럼 범용 모호성 프롬프트 안에 욱여넣기보다,
  전용 신호로 다루는 게 더 맞을 수 있다.

- **이모지 톤 모호성 (C03)**: 실재가 학술적으로 입증돼 있다. ["On the Context-Free
  Ambiguity of Emoji"](https://arxiv.org/pdf/2201.06302)는 이모지 30명 평가 기준 **완전히
  모호하지 않은 이모지가 1.2%뿐**이라고 밝혔다. 즉 C03이 잡으려는 현상 자체는 진짜다 —
  문제는 우리 스키마(candidates로 후보 나열)가 이 신호를 표현하기에 적합하냐다.

- **근거/맥락 누락 탐지 (C01)**: LLM 기반 접근이 존재하지만 다른 도메인(소프트웨어
  요구사항 명세, ["Improving Requirements Completeness"](https://arxiv.org/html/2308.03784v2))
  이라 캐주얼 업무 메시지에 그대로 전이될지는 불확실.

- **침묵/암묵적 동의 (C04)**: "침묵의 해석은 단순한 의미 보류가 아니라 다면적 의미
  구성 과정"이라는 게 화용론 문헌의 공통된 결론(pragmatics survey,
  [arXiv:2502.12378](https://arxiv.org/html/2502.12378v1)) — 형식화가 특히 어렵다.
  golden set에서 애초에 제외한 결정이 맞았다는 뜻.

### 3. 결정적 근거 — 간접화법은 LLM이 구조적으로 약한 영역

**["Evaluating Large Language Models on Understanding Korean Indirect Speech Acts"](https://arxiv.org/abs/2502.10995)**
(arXiv:2502.10995): 한국어 간접화법(실제 의도가 표면적 의미와 다른 발화) 이해력을
LLM에 테스트한 논문. 최고 성능인 **Claude 3 Opus조차 MCQ 71.94% / OEQ 65%**에 그쳤고,
**"어떤 LLM도 사람 수준에 도달하지 못했다"**. 원인으로 지목된 건 **"LLM은 발화를
간접화행이 아니라 직접화행으로 해석하려는 강한 경향이 있다"**는 점 — 이게 정확히
우리가 관찰한 실패 패턴과 일치한다: `C03 "완전 좋아요!!! 👍👍"`를 모델이 톤 모호성이
아니라 문자 그대로 "동의"(DECISION_STATUS)로 읽어버린 것.

## 결론

1. **프롬프트를 더 다듬는다고 풀릴 문제가 아니다** — 간접화법/톤 해석은 최고 성능
   모델도 사람 수준에 못 미치는, 학술적으로 입증된 LLM의 구조적 약점이다.
2. **OTHER 내부도 성격이 갈린다**: C01/C02(맥락·헤징류)는 탐지 가능한 태스크로
   재설계할 여지가 있지만, C03/C04(톤·침묵)는 지금 스키마(복수 해석 후보 제시)
   자체가 안 맞는다.
3. **스키마 자체의 한계**: `AmbiguityItem`(span/category/**candidates**/suggestion)은
   "여러 해석 중 하나를 고르게" 하는 구조라 TIME/REQUEST_INTENT/DECISION_STATUS엔
   맞지만, "이 표현이 이렇게도 읽힐 수 있다"는 경고성 신호(OTHER)엔 억지로 끼워 맞춘
   형태다.

## 권고

- **단기(이번 스코프)**: OTHER는 정식 지원 범위에서 빼고 TIME/REQUEST_INTENT/
  DECISION_STATUS 3개만 보장한다. 논문 결론("고위험 간접 커뮤니케이션 해석엔 사람
  검토가 낫다")과도 맞는 방향 — 억지로 대충 도는 4번째 카테고리보다, 3개를 확실히
  잘하는 게 데모/제품 신뢰도에 낫다.
- **장기**: OTHER를 다시 붙이려면 (a) C01/C02는 hedging/politeness 전용 분류기로
  분리, (b) C03/C04는 "후보 선택"이 아니라 "이렇게 읽힐 수 있다는 단발성 경고" 같은
  다른 스키마로 재설계하는 걸 검토.
