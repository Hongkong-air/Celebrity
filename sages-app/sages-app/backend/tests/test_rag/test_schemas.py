"""
测试模块 7: RAG - 数据结构 (rag/schemas.py)
覆盖: QueryType 枚举、SourceType 枚举、RetrievalResult、RAGContext
"""
import pytest
from rag.schemas import QueryType, SourceType, RetrievalResult, RAGContext


class TestQueryType:
    """查询类型枚举"""

    def test_all_values(self):
        assert QueryType.CHITCHAT.value == "chitchat"
        assert QueryType.QUOTE.value == "quote"
        assert QueryType.BIOGRAPHY.value == "biography"
        assert QueryType.PHILOSOPHY.value == "philosophy"
        assert QueryType.GENERAL.value == "general"

    def test_from_string(self):
        assert QueryType("chitchat") == QueryType.CHITCHAT
        assert QueryType("general") == QueryType.GENERAL

    def test_total_types(self):
        assert len(QueryType) == 5


class TestSourceType:
    """来源类型枚举"""

    def test_all_values(self):
        assert SourceType.DIALOGUE.value == "dialogue"
        assert SourceType.ORIGINAL_WORK.value == "original_work"
        assert SourceType.BIOGRAPHY.value == "biography"


class TestRetrievalResult:
    """检索结果"""

    def test_creation_with_required_fields(self):
        r = RetrievalResult(text="测试文本", score=0.95, source_type="dialogue")
        assert r.text == "测试文本"
        assert r.score == 0.95
        assert r.source_type == "dialogue"
        assert r.source_work is None
        assert r.topic == []
        assert r.metadata == {}

    def test_creation_with_all_fields(self):
        r = RetrievalResult(
            text="仁者爱人",
            score=0.9,
            source_type="original_work",
            source_work="论语·颜渊",
            topic=["仁", "爱"],
            metadata={"chapter": "12"},
        )
        assert r.source_work == "论语·颜渊"
        assert r.topic == ["仁", "爱"]
        assert r.metadata["chapter"] == "12"


class TestRAGContext:
    """RAG 上下文"""

    def test_empty_results(self):
        ctx = RAGContext(
            query="test",
            query_type=QueryType.GENERAL,
            results=[],
            character="confucius",
        )
        assert ctx.formatted_context == ""

    def test_formatted_context_with_results(self):
        ctx = RAGContext(
            query="什么是仁",
            query_type=QueryType.PHILOSOPHY,
            results=[
                RetrievalResult(text="克己复礼为仁", score=0.95,
                                source_type="original_work", source_work="论语·颜渊"),
                RetrievalResult(text="仁者爱人", score=0.9,
                                source_type="dialogue"),
            ],
            character="confucius",
        )
        formatted = ctx.formatted_context
        assert "【参考资料】" in formatted
        assert "1. 克己复礼为仁（论语·颜渊）" in formatted
        assert "2. 仁者爱人" in formatted

    def test_formatted_context_without_source_work(self):
        ctx = RAGContext(
            query="test",
            query_type=QueryType.GENERAL,
            results=[
                RetrievalResult(text="无来源文本", score=0.8, source_type="dialogue"),
            ],
            character="confucius",
        )
        formatted = ctx.formatted_context
        assert "1. 无来源文本" in formatted
        assert "（）" not in formatted  # 不应有空括号
