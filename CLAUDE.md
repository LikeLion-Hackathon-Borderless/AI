# ditto — 오해 방지 레이어 (Misunderstanding Prevention Layer)

Slack·Teams 등 협업툴 위에 붙는 AI 플러그인형 B2B SaaS. 비동기 메시지의 시간·요청
의도·결정 상태 모호성을 감지해, 발신자가 스스로 의도를 확인한 뒤 수신자에게 명시적인
업무 조건으로 전달하도록 돕는다. 멋쟁이사자처럼 14기 중앙해커톤 "보더리스 협업" 트랙
프로젝트.

이 저장소에서는 **AI 모델(LLM 프롬프트 + LangGraph 에이전트) 파트만** 다룬다
(`agent/`). FastAPI 라우터/DB/프론트엔드는 다른 팀원이 별도 저장소에서 만들며,
`agent/README.md`가 유일한 통합 접점이다.

# Workflow

## Collaboration

### Code Styles

- Use modern language features
- Limit lines to 120 characters maximum.
- Prefer pure functions where possible.
- NEVER write docstrings, function descriptions, or line-by-line comments.
- Only add inline comments to explain the *why* of non-obvious business logic, not the *what* of the code.

### Commit Template

`<category>: <short_summary>`

- categories: 'feat', 'fix', 'refactor', 'docs', 'test', 'chore', 'perf'
- example: `feat: add validation to prevent crash on special chars`
- **70 chars max**, imperative, English only
- NO body lines, NO co-authoring yourself.

## Progress Log

- Keep a running log of work in `docs/progress.md`.
- One dated section per work session (`## YYYY-MM-DD — short title`), newest at the bottom.
- Each entry: what was done, key results (tables/numbers where relevant), and a `### Next` list of
  what's left. This is the backup of "what Claude did" across sessions — write it so a fresh session
  (or teammate) can pick up context without re-reading the whole diff history.

## Architectural Decision Record (ADR)

- Save all ADRs in the `docs/adr/` folder.
- Use 4-digit numbers so the ADRs stay in order: `docs/adr/NNNN-decision-title.md`

### ADR Template

- Title: A short name (e.g., Use PostgreSQL for Database)
- Status: Draft, Accepted, Rejected, or Deprecated
- Date: Date & time
- Context: What is the problem and what rules limit your choices?
- Options: What other choices did you think about?
- Decision: What is the final choice and why?
- Consequences: The pros, cons, and trade-offs of this choice.
