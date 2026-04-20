"""
人物服务 - CRUD 操作
"""
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.character import Character


class CharacterService:
    """人物业务逻辑"""

    @staticmethod
    async def get_all(
        db: AsyncSession,
        active_only: bool = True,
    ) -> list[Character]:
        """获取所有人物列表"""
        query = select(Character)
        if active_only:
            query = query.where(Character.is_active == True)  # noqa: E712
        query = query.order_by(Character.created_at)
        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def get_by_id(
        db: AsyncSession,
        character_id: uuid.UUID,
    ) -> Character | None:
        """根据 ID 获取人物"""
        result = await db.execute(
            select(Character).where(Character.id == character_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_slug(
        db: AsyncSession,
        slug: str,
    ) -> Character | None:
        """根据 slug 获取人物"""
        result = await db.execute(
            select(Character).where(Character.slug == slug)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def create(
        db: AsyncSession,
        **kwargs,
    ) -> Character:
        """创建人物"""
        character = Character(id=uuid.uuid4(), **kwargs)
        db.add(character)
        await db.flush()
        await db.refresh(character)
        return character

    @staticmethod
    async def update(
        db: AsyncSession,
        character_id: uuid.UUID,
        **kwargs,
    ) -> Character | None:
        """更新人物信息"""
        character = await CharacterService.get_by_id(db, character_id)
        if not character:
            return None
        for key, value in kwargs.items():
            if hasattr(character, key):
                setattr(character, key, value)
        await db.flush()
        await db.refresh(character)
        return character
