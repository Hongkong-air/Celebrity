"""
测试模块: 混合检索器 (rag/retriever.py)
覆盖: HybridRetriever 初始化、连接、检索逻辑（mock Qdrant）
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from rag.retriever import HybridRetriever


class TestHybridRetrieverInit:
    """检索器初始化"""

    def test_default_state(self):
        retriever = HybridRetriever()
        assert retriever.client is None
        assert retriever.collection is not None

    def test_collection_name_from_settings(self):
        retriever = HybridRetriever()
        # collection 名来自 settings.qdrant_collection
        assert isinstance(retriever.collection, str)
        assert len(retriever.collection) > 0


class TestHybridRetrieverConnect:
    """连接管理"""

    @pytest.mark.asyncio
    async def test_connect_creates_client(self):
        retriever = HybridRetriever()
        mock_client = AsyncMock()

        with patch("rag.retriever.AsyncQdrantClient", return_value=mock_client):
            await retriever.connect()
            assert retriever.client is mock_client

    @pytest.mark.asyncio
    async def test_connect_idempotent(self):
        """重复调用 connect 不会创建新客户端"""
        retriever = HybridRetriever()
        mock_client = AsyncMock()

        with patch("rag.retriever.AsyncQdrantClient", return_value=mock_client) as mock_cls:
            await retriever.connect()
            await retriever.connect()
            # 只调用了一次 AsyncQdrantClient
            assert mock_cls.call_count == 1


class TestHybridRetrieverEnsureCollection:
    """Collection 管理"""

    @pytest.mark.asyncio
    async def test_ensure_collection_creates_when_missing(self):
        retriever = HybridRetriever()
        mock_client = AsyncMock()
        retriever.client = mock_client

        # 模拟 collection 不存在
        mock_collections = MagicMock()
        mock_collections.collections = []
        mock_client.get_collections = AsyncMock(return_value=mock_collections)

        with patch("rag.retriever.models") as mock_models:
            await retriever.ensure_collection()
            mock_client.create_collection.assert_called_once()

    @pytest.mark.asyncio
    async def test_ensure_collection_skips_when_exists(self):
        retriever = HybridRetriever()
        mock_client = AsyncMock()
        retriever.client = mock_client

        # 模拟 collection 已存在
        mock_collections = MagicMock()
        mock_collections.collections = [MagicMock(name=retriever.collection)]
        mock_client.get_collections = AsyncMock(return_value=mock_collections)

        await retriever.ensure_collection()
        mock_client.create_collection.assert_not_called()


class TestHybridRetrieverSearch:
    """检索逻辑"""

    @pytest.mark.asyncio
    async def test_search_returns_retrieval_results(self):
        retriever = HybridRetriever()
        mock_client = AsyncMock()
        retriever.client = mock_client

        # 模拟 Qdrant 查询结果
        mock_point = MagicMock()
        mock_point.score = 0.85
        mock_point.payload = {
            "text": "学而时习之，不亦说乎",
            "source_type": "dialogue",
            "source_work": "论语·学而",
            "topic": ["学习"],
        }

        mock_result = MagicMock()
        mock_result.points = [mock_point]
        mock_client.query = AsyncMock(return_value=mock_result)

        with patch("rag.retriever.models") as mock_models:
            with patch("rag.retriever.settings") as mock_settings:
                mock_settings.qdrant_collection = retriever.collection
                results = await retriever.search(
                    query_dense=[0.1] * 128,
                    query_sparse={1: 0.5, 2: 0.3},
                    character="confucius",
                    top_k=5,
                )

        assert len(results) == 1
        assert results[0].text == "学而时习之，不亦说乎"
        assert results[0].score == 0.85
        assert results[0].source_type == "dialogue"
        assert results[0].source_work == "论语·学而"
        assert results[0].topic == ["学习"]

    @pytest.mark.asyncio
    async def test_search_empty_results(self):
        """无匹配结果时返回空列表"""
        retriever = HybridRetriever()
        mock_client = AsyncMock()
        retriever.client = mock_client

        mock_result = MagicMock()
        mock_result.points = []
        mock_client.query = AsyncMock(return_value=mock_result)

        with patch("rag.retriever.models"):
            with patch("rag.retriever.settings") as mock_settings:
                mock_settings.qdrant_collection = retriever.collection
                results = await retriever.search(
                    query_dense=[0.1] * 128,
                    query_sparse={1: 0.5},
                    character="confucius",
                )

        assert results == []

    @pytest.mark.asyncio
    async def test_search_handles_missing_payload(self):
        """payload 字段缺失时使用默认值"""
        retriever = HybridRetriever()
        mock_client = AsyncMock()
        retriever.client = mock_client

        mock_point = MagicMock()
        mock_point.score = 0.5
        mock_point.payload = None  # payload 为 None

        mock_result = MagicMock()
        mock_result.points = [mock_point]
        mock_client.query = AsyncMock(return_value=mock_result)

        with patch("rag.retriever.models"):
            with patch("rag.retriever.settings") as mock_settings:
                mock_settings.qdrant_collection = retriever.collection
                results = await retriever.search(
                    query_dense=[0.1] * 128,
                    query_sparse={1: 0.5},
                    character="confucius",
                )

        assert len(results) == 1
        assert results[0].text == ""
        assert results[0].source_type == "unknown"
        assert results[0].source_work is None
