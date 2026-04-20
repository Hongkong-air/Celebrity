"""
测试模块 8: RAG - Encoder 客户端 (rag/encoder.py)
覆盖: EmbeddingClient 初始化、请求构造（不实际调用远程服务）
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from rag.encoder import EmbeddingClient, EmbedOutput


class TestEmbedOutput:
    """Embedding 输出数据结构"""

    def test_creation(self):
        out = EmbedOutput(
            dense=[0.1, 0.2, 0.3],
            sparse={1: 0.5, 10: 0.8},
        )
        assert out.dense == [0.1, 0.2, 0.3]
        assert out.sparse == {1: 0.5, 10: 0.8}

    def test_empty_sparse(self):
        out = EmbedOutput(dense=[0.0] * 1024, sparse={})
        assert len(out.dense) == 1024
        assert out.sparse == {}


class TestEmbeddingClient:
    """Embedding 客户端"""

    def test_init_default_url(self):
        client = EmbeddingClient()
        assert "localhost:8001" in client.base_url

    def test_init_custom_url(self):
        client = EmbeddingClient(base_url="http://custom:9000")
        assert client.base_url == "http://custom:9000"

    def test_url_trailing_slash_removed(self):
        client = EmbeddingClient(base_url="http://localhost:8001/")
        assert client.base_url == "http://localhost:8001"

    @pytest.mark.asyncio
    async def test_embed_calls_correct_endpoint(self):
        client = EmbeddingClient(base_url="http://test:8001")
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "dense_embeddings": [[0.1, 0.2]],
            "sparse_embeddings": [{"1": "0.5"}],
        }
        mock_response.raise_for_status = MagicMock()

        with patch("rag.encoder.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_cls.return_value = mock_client

            results = await client.embed(["测试文本"])
            assert len(results) == 1
            assert results[0].dense == [0.1, 0.2]
            assert results[0].sparse == {1: "0.5"}  # JSON values are strings

            # 验证调用了正确的端点
            mock_client.post.assert_called_once()
            call_args = mock_client.post.call_args
            assert "http://test:8001/embed" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_embed_single(self):
        client = EmbeddingClient(base_url="http://test:8001")
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "dense_embeddings": [[0.1]],
            "sparse_embeddings": [{}],
        }
        mock_response.raise_for_status = MagicMock()

        with patch("rag.encoder.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_cls.return_value = mock_client

            result = await client.embed_single("单条文本")
            assert result.dense == [0.1]

    @pytest.mark.asyncio
    async def test_rerank_calls_correct_endpoint(self):
        client = EmbeddingClient(base_url="http://test:8001")
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "results": [
                {"index": 1, "document": "文档2", "score": 0.9},
                {"index": 0, "document": "文档1", "score": 0.7},
            ]
        }
        mock_response.raise_for_status = MagicMock()

        with patch("rag.encoder.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_cls.return_value = mock_client

            results = await client.rerank("查询", ["文档1", "文档2"], top_k=2)
            assert results == [(1, 0.9), (0, 0.7)]

            call_args = mock_client.post.call_args
            assert "http://test:8001/rerank" in call_args[0][0]
