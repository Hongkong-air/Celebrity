"""
会话服务 - 创建、查询、管理对话会话
"""
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.conversation import Conversation
from models.message import Message


class ConversationService:
    """会话业务逻辑"""

    @staticmethod
    async def create(
        db: AsyncSession,
        user_id: uuid.UUID,
        character_id: uuid.UUID,
        title: str | None = None,
    ) -> Conversation:
        """创建新会话"""
        conversation = Conversation(
            id=uuid.uuid4(),
            user_id=user_id,
            character_id=character_id,
            title=title,
        )
        db.add(conversation)
        await db.flush()
        await db.refresh(conversation)
        return conversation

    @staticmethod
    async def get_by_id(
        db: AsyncSession,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID | None = None,
    ) -> Conversation | None:
        """根据 ID 获取会话（可选用户权限校验）"""
        query = select(Conversation).options(selectinload(Conversation.messages))
        query = query.where(Conversation.id == conversation_id)
        if user_id:
            query = query.where(Conversation.user_id == user_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def list_by_user(
        db: AsyncSession,
        user_id: uuid.UUID,
        character_id: uuid.UUID | None = None,
        limit: int = 20,
    ) -> list[Conversation]:
        """获取用户的会话列表"""
        query = select(Conversation).where(Conversation.user_id == user_id)
        if character_id:
            query = query.where(Conversation.character_id == character_id)
        query = query.order_by(Conversation.updated_at.desc()).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def add_message(
        db: AsyncSession,
        conversation_id: uuid.UUID,
        role: str,
        content: str,
        rag_sources: list | None = None,
    ) -> Message:
        """向会话添加消息"""
        message = Message(
            id=uuid.uuid4(),
            conversation_id=conversation_id,
            role=role,
            content=content,
            rag_sources=rag_sources or [],
        )
        db.add(message)
        await db.flush()
        await db.refresh(message)
        return message

    @staticmethod
    async def get_messages(
        db: AsyncSession,
        conversation_id: uuid.UUID,
        limit: int = 50,
    ) -> list[Message]:
        """获取会话的消息历史"""
        query = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc())
            .limit(limit)
        )
        result = await db.execute(query)
        return list(result.scalars().all())
