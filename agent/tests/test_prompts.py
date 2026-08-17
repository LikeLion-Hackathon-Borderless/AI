from ditto_agent.llm.prompts import build_system_prompt


def test_build_system_prompt_default_uses_fixed_allowlist():
    default_prompt = build_system_prompt()
    # 고정 allowlist에 있는 T01 예시 phrase가 기본 프롬프트에 들어있어야 함
    assert "내일까지 부탁드려요" in default_prompt


def test_build_system_prompt_with_few_shot_ids_overrides_allowlist():
    # T01만 골랐을 때 고정 allowlist에만 있는 다른 항목(F02 예시 phrase)은 빠져야 함
    rag_prompt = build_system_prompt(few_shot_ids={"T01"})
    default_prompt = build_system_prompt()
    assert rag_prompt != default_prompt
    assert "내일까지 부탁드려요" in rag_prompt


def test_build_system_prompt_empty_few_shot_ids_produces_no_positive_examples():
    prompt = build_system_prompt(few_shot_ids=set())
    assert "내일까지 부탁드려요" not in prompt
