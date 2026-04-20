"""
人类群星闪耀时 - 依赖注入
提供数据库会话、Redis 客户端、Qdrant 客户端等共享实例
"""
from typing import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from app.config import get_settings

settings = get_settings()


class Base(DeclarativeBase):
    """ORM 基类"""
    pass


def _create_engine():
    """创建数据库引擎（延迟创建，避免 import 时连接）"""
    url = settings.database_url
    kwargs = {
        "echo": settings.debug,
    }
    # SQLite 不支持 pool 参数
    if not url.startswith("sqlite"):
        kwargs.update({
            "pool_pre_ping": True,
            "pool_size": 10,
            "max_overflow": 20,
        })
    return create_async_engine(url, **kwargs)


# === SQLAlchemy 异步引擎（延迟创建） ===
_engine = None


def get_engine():
    global _engine
    if _engine is None:
        _engine = _create_engine()
    return _engine


def get_session_factory():
    return async_sessionmaker(
        get_engine(),
        class_=AsyncSession,
        expire_on_commit=False,
    )


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """获取数据库会话（FastAPI 依赖注入用）"""
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
