"""
测试模块 5: RAG - 查询路由 (rag/query_router.py)
覆盖: 各类查询分类、检索参数调整
"""
import pytest
from rag.query_router import classify_query, get_retrieval_params
from rag.schemas import QueryType


class TestClassifyQuery:
    """查询分类"""

    @pytest.mark.parametrize("query,expected", [
        # 闲聊
        ("你好", QueryType.CHITCHAT),
        ("嗨", QueryType.CHITCHAT),
        ("hello", QueryType.CHITCHAT),
        ("早上好", QueryType.CHITCHAT),
        ("谢谢", QueryType.CHITCHAT),
        ("再见", QueryType.CHITCHAT),
        ("你是谁", QueryType.CHITCHAT),
        ("你叫什么", QueryType.CHITCHAT),
        # 引用
        ("论语里关于孝的原话", QueryType.QUOTE),
        ("这句话出自哪篇", QueryType.QUOTE),
        ("子曰的原话是什么", QueryType.QUOTE),
        ("出处是哪里", QueryType.QUOTE),
        # 生平
        ("孔子的生平", QueryType.BIOGRAPHY),
        ("他什么时候出生的", QueryType.BIOGRAPHY),
        ("孔子哪里人", QueryType.BIOGRAPHY),
        ("他的弟子有哪些", QueryType.BIOGRAPHY),
        ("周游列国的故事", QueryType.BIOGRAPHY),
        # 哲学
        ("什么是仁", QueryType.PHILOSOPHY),
        ("孔子的思想", QueryType.PHILOSOPHY),
        ("如何修身养性", QueryType.PHILOSOPHY),
        ("什么是中庸之道", QueryType.PHILOSOPHY),
        ("治国理念", QueryType.PHILOSOPHY),
        ("忠孝仁义", QueryType.PHILOSOPHY),
        # 通用
        ("今天天气怎么样", QueryType.GENERAL),
        ("帮我写一首诗", QueryType.GENERAL),
        ("推荐一本书", QueryType.GENERAL),
    ])
    def test_classify(self, query, expected):
        assert classify_query(query) == expected

    def test_empty_query(self):
        assert classify_query("") == QueryType.GENERAL

    def test_whitespace_query(self):
        assert classify_query("   ") == QueryType.GENERAL

    def test_case_insensitive(self):
        assert classify_query("HELLO") == QueryType.CHITCHAT
        assert classify_query("Hello") == QueryType.CHITCHAT


class TestGetRetrievalParams:
    """检索参数"""

    def test_chitchat_no_retrieval(self):
        params = get_retrieval_params(QueryType.CHITCHAT)
        assert params["top_k"] == 0

    def test_quote_prioritizes_original_work(self):
        params = get_retrieval_params(QueryType.QUOTE)
        assert params["top_k"] == 15
        assert params["source_type_weights"]["original_work"] > params["source_type_weights"]["biography"]

    def test_biography_prioritizes_biography(self):
        params = get_retrieval_params(QueryType.BIOGRAPHY)
        assert params["source_type_weights"]["biography"] > params["source_type_weights"]["original_work"]

    def test_philosophy_balanced(self):
        params = get_retrieval_params(QueryType.PHILOSOPHY)
        assert params["top_k"] == 12
        assert params["source_type_weights"]["dialogue"] > 1.0

    def test_general_default(self):
        params = get_retrieval_params(QueryType.GENERAL)
        assert params["top_k"] == 10
        assert all(v == 1.0 for v in params["source_type_weights"].values())

    def test_all_params_have_required_keys(self):
        for qt in QueryType:
            params = get_retrieval_params(qt)
            assert "top_k" in params
            assert "min_score" in params
            assert "source_type_weights" in params
            assert "dialogue" in params["source_type_weights"]
            assert "original_work" in params["source_type_weights"]
            assert "biography" in params["source_type_weights"]
