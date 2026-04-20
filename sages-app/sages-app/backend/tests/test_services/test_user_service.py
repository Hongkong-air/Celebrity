"""
测试模块: 用户服务 (services/user_service.py)
覆盖: 注册、登录认证、按ID查询（使用内存 SQLite）
"""
import pytest
import uuid
from unittest.mock import AsyncMock, patch
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.dependencies import Base
from models.user import User
from services.user_service import UserService


@pytest.fixture
def engine():
    e = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    yield e
    e.sync_engine.dispose()


@pytest.fixture
async def session(engine):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as s:
        yield s


class TestUserServiceRegister:
    """用户注册"""

    @pytest.mark.asyncio
    async def test_register_success(self, session):
        """正常注册"""
        user = await UserService.register(
            db=session,
            username="newuser",
            password="secure123",
        )
        assert user.id is not None
        assert user.username == "newuser"
        assert user.password_hash is not None
        assert user.password_hash != "secure123"  # 已加密

    @pytest.mark.asyncio
    async def test_register_duplicate_username(self, session):
        """重复用户名应抛出 ValueError"""
        await UserService.register(db=session, username="dup", password="pw1")

        with pytest.raises(ValueError, match="已被注册"):
            await UserService.register(db=session, username="dup", password="pw2")

    @pytest.mark.asyncio
    async def test_register_generates_uuid(self, session):
        """注册后应生成 UUID"""
        user = await UserService.register(db=session, username="uuid_test", password="pw")
        assert isinstance(user.id, uuid.UUID)


class TestUserServiceAuthenticate:
    """用户登录认证"""

    @pytest.mark.asyncio
    async def test_authenticate_success(self, session):
        """正确密码登录"""
        await UserService.register(db=session, username="auth_user", password="mypass")

        user, token = await UserService.authenticate(
            db=session,
            username="auth_user",
            password="mypass",
        )
        assert user.username == "auth_user"
        assert isinstance(token, str)
        assert len(token) > 0

    @pytest.mark.asyncio
    async def test_authenticate_wrong_password(self, session):
        """错误密码应抛出 ValueError"""
        await UserService.register(db=session, username="auth_user", password="correct")

        with pytest.raises(ValueError, match="用户名或密码错误"):
            await UserService.authenticate(
                db=session,
                username="auth_user",
                password="wrong",
            )

    @pytest.mark.asyncio
    async def test_authenticate_nonexistent_user(self, session):
        """不存在的用户应抛出 ValueError"""
        with pytest.raises(ValueError, match="用户名或密码错误"):
            await UserService.authenticate(
                db=session,
                username="ghost",
                password="anything",
            )


class TestUserServiceGetById:
    """按 ID 查询用户"""

    @pytest.mark.asyncio
    async def test_get_existing_user(self, session):
        """查询存在的用户"""
        created = await UserService.register(db=session, username="findme", password="pw")
        found = await UserService.get_by_id(db=session, user_id=created.id)
        assert found is not None
        assert found.username == "findme"

    @pytest.mark.asyncio
    async def test_get_nonexistent_user(self, session):
        """查询不存在的用户返回 None"""
        found = await UserService.get_by_id(
            db=session,
            user_id=uuid.uuid4(),
        )
        assert found is None
