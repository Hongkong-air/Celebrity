"""
测试模块: 重排序模块 (rag/reranker.py)
覆盖: rerank 函数的空结果、正常排序、top_k 截断
"""
import pytest
from unittest.mock import AsyncMock, patch
from rag.reranker import rerank
from rag.schemas import RetrievalResult


def _make_results(texts: list[str]) -> list[RetrievalResult]:
    """快速构造 RetrievalResult 列表"""
    return [
        RetrievalResult(text=t, score=0.5, source_type="dialogue")
        for t in texts
    ]


class TestRerankEmpty:
    """空结果处理"""

    @pytest.mark.asyncio
    async def test_empty_results_returns_empty(self):
        """空列表直接返回，不调用 rerank 服务"""
        result = await rerank(query="测试", results=[])
        assert result == []


class TestRerankNormal:
    """正常重排序"""

    @pytest.mark.asyncio
    async def test_rerank_reorders_by_score(self):
        """重排序应按 rerank 服务返回的顺序排列"""
        results = _make_results(["文档A", "文档B", "文档C"])

        # 模拟 rerank 服务返回：文档C(0.9) > 文档A(0.7) > 文档B(0.3)
        mock_ranked = [(2, 0.9), (0, 0.7), (1, 0.3)]

        with patch("rag.reranker.embedding_client") as mock_client:
            mock_client.rerank = AsyncMock(return_value=mock_ranked)
            ranked = await rerank(query="测试查询", results=results)

        assert len(ranked) == 3
        assert ranked[0].text == "文档C"
        assert ranked[1].text == "文档A"
        assert ranked[2].text == "文档B"

    @pytest.mark.asyncio
    async def test_rerank_passes_correct_arguments(self):
        """验证传给 embedding_client.rerank 的参数"""
        results = _make_results(["文本1", "文本2"])

        with patch("rag.reranker.embedding_client") as mock_client:
            mock_client.rerank = AsyncMock(return_value=[(0, 0.8)])
            await rerank(query="查询", results=results, top_k=1)

            mock_client.rerank.assert_called_once_with(
                "查询",
                ["文本1", "文本2"],
                top_k=1,
            )


class TestRerankTopK:
    """top_k 截断"""

    @pytest.mark.asyncio
    async def test_rerank_respects_top_k(self):
        """只返回 top_k 个结果"""
        results = _make_results(["A", "B", "C", "D", "E"])

        mock_ranked = [(0, 0.9), (1, 0.8), (2, 0.7)]
        with patch("rag.reranker.embedding_client") as mock_client:
            mock_client.rerank = AsyncMock(return_value=mock_ranked)
            ranked = await rerank(query="q", results=results, top_k=3)

        assert len(ranked) == 3

    @pytest.mark.asyncio
    async def test_rerank_default_top_k(self):
        """默认 top_k=3"""
        results = _make_results(["A", "B", "C", "D"])

        mock_ranked = [(0, 0.9), (1, 0.8), (2, 0.7)]
        with patch("rag.reranker.embedding_client") as mock_client:
            mock_client.rerank = AsyncMock(return_value=mock_ranked)
            ranked = await rerank(query="q", results=results)

        assert len(ranked) == 3
        # 验证默认 top_k=3 被传递
        mock_client.rerank.assert_called_once()
        call_kwargs = mock_client.rerank.call_args
        assert call_kwargs[1]["top_k"] == 3
