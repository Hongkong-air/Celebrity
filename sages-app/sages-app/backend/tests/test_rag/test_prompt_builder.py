"""
测试模块 6: RAG - Prompt 组装 (rag/prompt_builder.py)
覆盖: Chat 格式、纯文本格式、空 RAG、有历史
"""
import pytest
from rag.prompt_builder import build_prompt, build_prompt_text
from rag.schemas import RAGContext, RetrievalResult, QueryType


@pytest.fixture
def system_prompt():
    return "你是孔子，伟大的思想家。"


@pytest.fixture
def rag_context():
    return RAGContext(
        query="什么是仁",
        query_type=QueryType.PHILOSOPHY,
        results=[
            RetrievalResult(
                text="克己复礼为仁。",
                score=0.95,
                source_type="original_work",
                source_work="论语·颜渊",
            ),
            RetrievalResult(
                text="仁者爱人。",
                score=0.90,
                source_type="dialogue",
                source_work="论语·颜渊",
            ),
        ],
        character="confucius",
    )


@pytest.fixture
def empty_rag_context():
    return RAGContext(
        query="你好",
        query_type=QueryType.CHITCHAT,
        results=[],
        character="confucius",
    )


class TestBuildPrompt:
    """Chat 格式 Prompt 组装"""

    def test_basic_structure(self, system_prompt, rag_context):
        messages = build_prompt(system_prompt, rag_context, [], "什么是仁？")
        assert len(messages) == 2  # system + user
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
        assert messages[1]["content"] == "什么是仁？"

    def test_with_history(self, system_prompt, rag_context):
        history = [
            {"role": "user", "content": "老师好"},
            {"role": "assistant", "content": "你好，吾徒"},
        ]
        messages = build_prompt(system_prompt, rag_context, history, "什么是仁？")
        assert len(messages) == 4  # system + 2 history + user
        assert messages[1]["role"] == "user"
        assert messages[2]["role"] == "assistant"
        assert messages[3]["role"] == "user"

    def test_rag_context_injected(self, system_prompt, rag_context):
        messages = build_prompt(system_prompt, rag_context, [], "test")
        system_content = messages[0]["content"]
        assert "参考资料" in system_content
        assert "克己复礼为仁" in system_content
        assert "仁者爱人" in system_content
        assert "论语·颜渊" in system_content

    def test_empty_rag_no_context(self, system_prompt, empty_rag_context):
        messages = build_prompt(system_prompt, empty_rag_context, [], "你好")
        system_content = messages[0]["content"]
        assert "参考资料" not in system_content
        assert system_content == system_prompt

    def test_none_rag(self, system_prompt):
        messages = build_prompt(system_prompt, None, [], "test")
        assert messages[0]["content"] == system_prompt

    def test_no_history(self, system_prompt, rag_context):
        messages = build_prompt(system_prompt, rag_context, [], "test")
        assert len(messages) == 2

    def test_long_history(self, system_prompt, rag_context):
        history = [{"role": "user" if i % 2 == 0 else "assistant",
                     "content": f"消息{i}"} for i in range(20)]
        messages = build_prompt(system_prompt, rag_context, history, "新问题")
        assert len(messages) == 22  # system + 20 history + user


class TestBuildPromptText:
    """纯文本 Prompt 组装"""

    def test_basic_structure(self, system_prompt, rag_context):
        text = build_prompt_text(system_prompt, rag_context, [], "什么是仁？")
        assert "<system>" in text
        assert "<context>" in text
        assert "<user>" in text
        assert "<assistant>" in text

    def test_with_history(self, system_prompt, rag_context):
        history = [{"role": "user", "content": "你好"}]
        text = build_prompt_text(system_prompt, rag_context, history, "test")
        assert "<history>" in text
        assert "user: 你好" in text

    def test_no_history_no_history_tag(self, system_prompt, rag_context):
        text = build_prompt_text(system_prompt, rag_context, [], "test")
        assert "<history>" not in text

    def test_empty_rag_no_context_tag(self, system_prompt, empty_rag_context):
        text = build_prompt_text(system_prompt, empty_rag_context, [], "test")
        assert "<context>" not in text

    def test_rag_content_present(self, system_prompt, rag_context):
        text = build_prompt_text(system_prompt, rag_context, [], "test")
        assert "克己复礼为仁" in text
