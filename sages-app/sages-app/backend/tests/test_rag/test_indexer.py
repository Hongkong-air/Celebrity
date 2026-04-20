"""
测试模块: 索引构建器 (rag/indexer.py)
覆盖: build_index 的文件读取、批量入库、JSONL 解析（mock Qdrant + embedding）
"""
import json
import pytest
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock
from rag.indexer import build_index


class TestBuildIndexFileReading:
    """JSONL 文件读取"""

    @pytest.mark.asyncio
    async def test_reads_jsonl_files(self):
        """应读取目录下所有 .jsonl 文件"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建测试 JSONL 文件
            data_dir = Path(tmpdir)
            (data_dir / "part1.jsonl").write_text(
                json.dumps({"text": "学而时习之", "source_type": "dialogue"}) + "\n"
                + json.dumps({"text": "有朋自远方来", "source_type": "dialogue"}) + "\n",
                encoding="utf-8",
            )
            (data_dir / "part2.jsonl").write_text(
                json.dumps({"text": "温故而知新", "source_type": "original_work"}) + "\n",
                encoding="utf-8",
            )

            mock_client = AsyncMock()
            mock_retriever = AsyncMock()

            # mock embedding 返回
            from rag.encoder import EmbedOutput
            mock_embeddings = [
                EmbedOutput(dense=[0.1] * 128, sparse={1: 0.5}),
                EmbedOutput(dense=[0.2] * 128, sparse={2: 0.3}),
                EmbedOutput(dense=[0.3] * 128, sparse={3: 0.7}),
            ]

            with patch("rag.indexer.AsyncQdrantClient", return_value=mock_client):
                with patch("rag.indexer.HybridRetriever", return_value=mock_retriever):
                    with patch("rag.indexer.embedding_client") as mock_embed:
                        mock_embed.embed = AsyncMock(return_value=mock_embeddings)
                        with patch("rag.indexer.settings") as mock_settings:
                            mock_settings.qdrant_collection = "test_collection"
                            await build_index(data_dir, character="confucius", batch_size=2)

            # 验证 upsert 被调用（batch_size=2，3条数据 → 2次 upsert）
            assert mock_client.upsert.call_count == 2

    @pytest.mark.asyncio
    async def test_empty_directory(self):
        """空目录不应调用 upsert"""
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_client = AsyncMock()
            mock_retriever = AsyncMock()

            with patch("rag.indexer.AsyncQdrantClient", return_value=mock_client):
                with patch("rag.indexer.HybridRetriever", return_value=mock_retriever):
                    with patch("rag.indexer.settings") as mock_settings:
                        mock_settings.qdrant_collection = "test_collection"
                        await build_index(tmpdir, character="confucius")

            mock_client.upsert.assert_not_called()

    @pytest.mark.asyncio
    async def test_skips_empty_lines(self):
        """跳过空行"""
        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = Path(tmpdir)
            (data_dir / "data.jsonl").write_text(
                json.dumps({"text": "有效行"}) + "\n"
                + "\n"  # 空行
                + "   \n"  # 空白行
                + json.dumps({"text": "另一有效行"}) + "\n",
                encoding="utf-8",
            )

            mock_client = AsyncMock()
            mock_retriever = AsyncMock()

            from rag.encoder import EmbedOutput
            mock_embeddings = [
                EmbedOutput(dense=[0.1] * 128, sparse={1: 0.5}),
                EmbedOutput(dense=[0.2] * 128, sparse={2: 0.3}),
            ]

            with patch("rag.indexer.AsyncQdrantClient", return_value=mock_client):
                with patch("rag.indexer.HybridRetriever", return_value=mock_retriever):
                    with patch("rag.indexer.embedding_client") as mock_embed:
                        mock_embed.embed = AsyncMock(return_value=mock_embeddings)
                        with patch("rag.indexer.settings") as mock_settings:
                            mock_settings.qdrant_collection = "test_collection"
                            await build_index(data_dir, character="confucius")

            # 只入库了 2 条有效记录
            call_args = mock_client.upsert.call_args
            assert len(call_args[1]["points"]) == 2


class TestBuildIndexPayload:
    """入库 payload 构造"""

    @pytest.mark.asyncio
    async def test_payload_fields(self):
        """验证 payload 包含正确的字段"""
        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = Path(tmpdir)
            record = {
                "text": "三人行必有我师",
                "source_type": "dialogue",
                "source_work": "论语·述而",
                "topic": ["学习", "谦虚"],
                "emotion": "谦虚",
            }
            (data_dir / "data.jsonl").write_text(
                json.dumps(record) + "\n", encoding="utf-8",
            )

            mock_client = AsyncMock()
            mock_retriever = AsyncMock()

            from rag.encoder import EmbedOutput
            mock_embeddings = [
                EmbedOutput(dense=[0.1] * 128, sparse={1: 0.5}),
            ]

            with patch("rag.indexer.AsyncQdrantClient", return_value=mock_client):
                with patch("rag.indexer.HybridRetriever", return_value=mock_retriever):
                    with patch("rag.indexer.embedding_client") as mock_embed:
                        mock_embed.embed = AsyncMock(return_value=mock_embeddings)
                        with patch("rag.indexer.settings") as mock_settings:
                            mock_settings.qdrant_collection = "test_collection"
                            await build_index(data_dir, character="confucius")

            # 检查 payload
            call_args = mock_client.upsert.call_args
            point = call_args[1]["points"][0]
            payload = point.payload
            assert payload["character"] == "confucius"
            assert payload["text"] == "三人行必有我师"
            assert payload["source_type"] == "dialogue"
            assert payload["source_work"] == "论语·述而"
            assert payload["topic"] == ["学习", "谦虚"]
            assert payload["emotion"] == "谦虚"

    @pytest.mark.asyncio
    async def test_payload_defaults(self):
        """缺少可选字段时使用默认值"""
        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = Path(tmpdir)
            # 只有必填字段 text
            (data_dir / "data.jsonl").write_text(
                json.dumps({"text": "测试"}) + "\n", encoding="utf-8",
            )

            mock_client = AsyncMock()
            mock_retriever = AsyncMock()

            from rag.encoder import EmbedOutput
            mock_embeddings = [
                EmbedOutput(dense=[0.1] * 128, sparse={1: 0.5}),
            ]

            with patch("rag.indexer.AsyncQdrantClient", return_value=mock_client):
                with patch("rag.indexer.HybridRetriever", return_value=mock_retriever):
                    with patch("rag.indexer.embedding_client") as mock_embed:
                        mock_embed.embed = AsyncMock(return_value=mock_embeddings)
                        with patch("rag.indexer.settings") as mock_settings:
                            mock_settings.qdrant_collection = "test_collection"
                            await build_index(data_dir, character="libai")

            call_args = mock_client.upsert.call_args
            payload = call_args[1]["points"][0].payload
            assert payload["character"] == "libai"
            assert payload["source_type"] == "dialogue"  # 默认值
            assert payload["source_work"] == ""  # 默认空字符串
            assert payload["topic"] == []  # 默认空列表
            assert payload["emotion"] == ""  # 默认空字符串
