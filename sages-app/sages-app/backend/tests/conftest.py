"""
pytest 全局 fixtures
提供测试用的 FastAPI 客户端、内存数据库等
"""
import os
import sys

# === 关键：在 import 任何项目模块之前设置测试环境变量 ===
os.environ["SAGES_DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["SAGES_JWT_SECRET_KEY"] = "test-secret-key-for-testing"
os.environ["SAGES_JWT_ALGORITHM"] = "HS256"
os.environ["SAGES_JWT_EXPIRE_MINUTES"] = "60"

# 确保 embedding-service 可导入
sys.path.insert(0, str(__file__).rsplit("/tests", 1)[0] + "/../embedding-service")

import asyncio
import uuid
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport


@pytest.fixture(scope="session")
def event_loop():
    """创建全局事件循环"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """创建测试用 HTTP 客户端"""
    from app.main import app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.fixture
def test_user_data():
    """测试用户数据"""
    return {"username": "testuser", "password": "test123456"}


@pytest.fixture
def test_character_id():
    """测试用人物 ID"""
    return "00000000-0000-0000-0000-000000000001"
