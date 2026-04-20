"""
用户服务 - 注册、登录、用户管理
"""
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User
from middleware.auth import hash_password, verify_password, create_access_token


class UserService:
    """用户业务逻辑"""

    @staticmethod
    async def register(
        db: AsyncSession,
        username: str,
        password: str,
    ) -> User:
        """
        注册新用户

        Args:
            db: 数据库会话
            username: 用户名（唯一）
            password: 明文密码

        Returns:
            创建的用户对象

        Raises:
            ValueError: 用户名已存在
        """
        # 检查用户名是否已存在
        existing = await db.execute(
            select(User).where(User.username == username)
        )
        if existing.scalar_one_or_none():
            raise ValueError(f"用户名 '{username}' 已被注册")

        user = User(
            id=uuid.uuid4(),
            username=username,
            password_hash=hash_password(password),
        )
        db.add(user)
        await db.flush()
        await db.refresh(user)
        return user

    @staticmethod
    async def authenticate(
        db: AsyncSession,
        username: str,
        password: str,
    ) -> tuple[User, str]:
        """
        用户登录认证

        Args:
            db: 数据库会话
            username: 用户名
            password: 明文密码

        Returns:
            (用户对象, JWT token)

        Raises:
            ValueError: 用户名或密码错误
        """
        result = await db.execute(
            select(User).where(User.username == username)
        )
        user = result.scalar_one_or_none()

        if not user or not verify_password(password, user.password_hash):
            raise ValueError("用户名或密码错误")

        token = create_access_token(data={"sub": str(user.id)})
        return user, token

    @staticmethod
    async def get_by_id(
        db: AsyncSession,
        user_id: uuid.UUID,
    ) -> User | None:
        """根据 ID 获取用户"""
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()
