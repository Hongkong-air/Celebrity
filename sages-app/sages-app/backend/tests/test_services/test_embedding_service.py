"""
测试模块 11: Embedding 微服务 (embedding-service/app.py)
覆盖: 健康检查、模型未加载时的降级处理
"""
import importlib.util
from pathlib import Path

# 动态加载 embedding-service/app.py，避免与 backend.app 冲突
_spec = importlib.util.spec_from_file_location(
    "embedding_app",
    Path(__file__).resolve().parent.parent.parent.parent / "embedding-service" / "app.py",
)
_embedding_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_embedding_mod)
embed_app = _embedding_mod.app

import pytest
from httpx import AsyncClient, ASGITransport


@pytest.fixture
async def embed_client():
    transport = ASGITransport(app=embed_app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


class TestEmbeddingHealth:
    """Embedding 服务健康检查"""

    @pytest.mark.asyncio
    async def test_health_ok(self, embed_client):
        r = await embed_client.get("/health")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "ok"
        assert data["service"] == "embedding-service"

    @pytest.mark.asyncio
    async def test_ready_loading(self, embed_client):
        r = await embed_client.get("/health/ready")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] in ("loading", "ready")


class TestEmbeddingEndpoints:
    """Embedding 接口（模型未加载时）"""

    @pytest.mark.asyncio
    async def test_embed_without_model_returns_503(self, embed_client):
        r = await embed_client.post("/embed", json={"texts": ["测试文本"]})
        assert r.status_code == 503

    @pytest.mark.asyncio
    async def test_rerank_without_model_returns_503(self, embed_client):
        r = await embed_client.post("/rerank", json={
            "query": "测试查询",
            "documents": ["文档1", "文档2"],
        })
        assert r.status_code == 503

    @pytest.mark.asyncio
    async def test_embed_validation(self, embed_client):
        r = await embed_client.post("/embed", json={"texts": []})
        assert r.status_code == 422

    @pytest.mark.asyncio
    async def test_rerank_validation(self, embed_client):
        r = await embed_client.post("/rerank", json={
            "query": "test",
            "documents": [],
        })
        assert r.status_code == 422
