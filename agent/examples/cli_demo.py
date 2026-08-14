"""Exercises start()/resume() end-to-end without needing the FastAPI teammate's server.

Run: uv run python examples/cli_demo.py
"""

from ditto_agent import start, resume
from ditto_agent.schema import StartResult


def _print_interrupt(result: StartResult) -> None:
    assert result.interrupt is not None
    print(f"\n[{result.interrupt.kind}] {result.interrupt.question}")
    for i, c in enumerate(result.interrupt.candidates):
        print(f"  {i}) {c}")


def main() -> None:
    draft = "이 부분 검토 부탁드려요. 내일까지 조금 더 고민해 보면 좋을 것 같아요."
    print(f"draft: {draft}")

    result = start(draft)
    while result.status == "interrupt":
        _print_interrupt(result)
        answer = result.interrupt.candidates[0]
        print(f"  -> 자동 선택: {answer}")
        result = resume(result.thread_id, answer)

    print("\n=== 공동 이해 카드 ===")
    print(result.card.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
