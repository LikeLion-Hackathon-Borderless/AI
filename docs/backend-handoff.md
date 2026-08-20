# 백엔드 연동 체크리스트

## 연동에 필요한 것

- 레포: `LikeLion-Hackathon-Borderless/AI`, `main` 브랜치, `agent/` 폴더
- 설치: `cd agent && uv sync`
- 부르는 함수(서버 시작 시 `configure()` 1번, 메시지마다 `start()`/`resume()`):

```python
from ditto_agent import configure, start, resume
from ditto_agent.schema import DraftContext, StartResult, InterruptPayload, ConfirmedCard, ConflictResult
```

- 함수 시그니처·JSON 스키마·예시 코드는 **[`agent/README.md`](../agent/README.md)** 에
  전부 있음 — 그것부터 읽으면 됨

## .env 설정 — 직접 새로 만들어야 함

- `OPENAI_API_KEY` — AI 파트 개발용 키를 그대로 쓰지 말고, **백엔드 팀 계정으로
  새로 API 키를 발급받아서** `.env`에 넣을 것
- 나머지 값(`DITTO_LLM_MODE=live`, `DITTO_OPENAI_MODEL=o3-mini`,
  `DITTO_CHECKPOINT_DB`)은 `agent/.env.example` 그대로 쓰면 됨
