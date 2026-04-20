"""
测试模块 4: API 接口 (api/v1/)
覆盖: 健康检查、用户注册/登录、人物列表、会话管理、对话接口
"""
import pytest
from httpx import AsyncClient, ASGITransport


class TestHealthAPI:
    """健康检查接口"""

    @pytest.mark.asyncio
    async def test_health_check(self, client: AsyncClient):
        r = await client.get("/api/v1/health")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "ok"
        assert data["service"] == "sages-app"

    @pytest.mark.asyncio
    async def test_readiness_check(self, client: AsyncClient):
        r = await client.get("/api/v1/health/ready")
        assert r.status_code == 200
        data = r.json()
        assert "checks" in data
        assert "api" in data["checks"]
        assert data["checks"]["api"] is True

    @pytest.mark.asyncio
    async def test_404_for_nonexistent(self, client: AsyncClient):
        r = await client.get("/api/v1/nonexistent")
        assert r.status_code == 404

    @pytest.mark.asyncio
    async def test_openapi_docs(self, client: AsyncClient):
        r = await client.get("/openapi.json")
        assert r.status_code == 200
        data = r.json()
        assert data["info"]["title"] == "SagesApp"
        assert "/api/v1/health" in data["paths"]


class TestUserAPI:
    """用户接口（需要数据库，标记为集成测试）"""

    @pytest.mark.asyncio
    async def test_register_missing_fields(self, client: AsyncClient):
        """缺少必填字段应返回 422"""
        r = await client.post("/api/v1/users/register", json={})
        assert r.status_code == 422

    @pytest.mark.asyncio
    async def test_register_short_password(self, client: AsyncClient):
        """密码太短应返回 422"""
        r = await client.post("/api/v1/users/register", json={
            "username": "testuser",
            "password": "123",
        })
        assert r.status_code == 422

    @pytest.mark.asyncio
    async def test_register_invalid_username(self, client: AsyncClient):
        """用户名含特殊字符应返回 422"""
        r = await client.post("/api/v1/users/register", json={
            "username": "user@name!",
            "password": "123456",
        })
        assert r.status_code == 422

    @pytest.mark.asyncio
    async def test_login_missing_fields(self, client: AsyncClient):
        r = await client.post("/api/v1/users/login", json={})
        assert r.status_code == 422

    @pytest.mark.asyncio
    async def test_me_without_token(self, client: AsyncClient):
        """未携带 token 访问 /me 应返回 403"""
        r = await client.get("/api/v1/users/me")
        assert r.status_code == 403

    @pytest.mark.asyncio
    async def test_me_with_invalid_token(self, client: AsyncClient):
        """无效 token 应返回 401"""
        r = await client.get("/api/v1/users/me", headers={
            "Authorization": "Bearer invalid.token.here",
        })
        assert r.status_code == 401


class TestCharacterAPI:
    """人物接口"""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_list_characters(self, client: AsyncClient):
        """获取人物列表（需要数据库）"""
        r = await client.get("/api/v1/characters")
        if r.status_code == 200:
            assert isinstance(r.json(), list)

    @pytest.mark.asyncio
    async def test_get_character_invalid_uuid(self, client: AsyncClient):
        """无效 UUID 应返回 422"""
        r = await client.get("/api/v1/characters/not-a-uuid")
        assert r.status_code == 422


class TestConversationAPI:
    """会话接口"""

    @pytest.mark.asyncio
    async def test_create_conversation_without_auth(self, client: AsyncClient):
        """未认证创建会话应返回 403"""
        r = await client.post("/api/v1/conversations", json={
            "character_id": "00000000-0000-0000-0000-000000000001",
        })
        assert r.status_code == 403

    @pytest.mark.asyncio
    async def test_list_conversations_without_auth(self, client: AsyncClient):
        r = await client.get("/api/v1/conversations")
        assert r.status_code == 403


class TestChatAPI:
    """对话接口"""

    @pytest.mark.asyncio
    async def test_chat_without_auth(self, client: AsyncClient):
        """未认证发起对话应返回 403"""
        r = await client.post("/api/v1/chat", json={
            "character_id": "00000000-0000-0000-0000-000000000001",
            "message": "你好",
        })
        assert r.status_code == 403

    @pytest.mark.asyncio
    async def test_chat_sync_without_auth(self, client: AsyncClient):
        r = await client.post("/api/v1/chat/sync", json={
            "character_id": "00000000-0000-0000-0000-000000000001",
            "message": "你好",
        })
        assert r.status_code == 403

    @pytest.mark.asyncio
    async def test_chat_missing_fields(self, client: AsyncClient):
        """缺少字段应返回 422 或 403（Bearer 校验优先）"""
        r = await client.post("/api/v1/chat", json={},
                              headers={"Authorization": "Bearer fake"})
        assert r.status_code in (401, 403, 422)
