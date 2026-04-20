"""
测试模块: 会话服务 (services/conversation_service.py)
覆盖: 创建会话、按ID查询、用户会话列表、添加消息、获取消息历史
"""
import pytest
import uuid
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.dependencies import Base
from models.user import User
from models.character import Character
from models.conversation import Conversation
from models.message import Message
from services.conversation_service import ConversationService


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


@pytest.fixture
async def seeded_data(session):
    """预置用户、人物数据"""
    user = User(username="testuser", password_hash="hashed")
    char = Character(slug="confucius", name="孔子", system_prompt="你是孔子。")
    session.add(user)
    session.add(char)
    await session.flush()
    await session.refresh(user)
    await session.refresh(char)
    return user, char


class TestConversationServiceCreate:
    """创建会话"""

    @pytest.mark.asyncio
    async def test_create_success(self, session, seeded_data):
        user, char = seeded_data
        conv = await ConversationService.create(
            db=session,
            user_id=user.id,
            character_id=char.id,
            title="与孔子的对话",
        )
        assert conv.id is not None
        assert conv.user_id == user.id
        assert conv.character_id == char.id
        assert conv.title == "与孔子的对话"

    @pytest.mark.asyncio
    async def test_create_without_title(self, session, seeded_data):
        """不传 title 时应为 None"""
        user, char = seeded_data
        conv = await ConversationService.create(
            db=session,
            user_id=user.id,
            character_id=char.id,
        )
        assert conv.title is None


class TestConversationServiceGetById:
    """按 ID 查询会话"""

    @pytest.mark.asyncio
    async def test_get_existing(self, session, seeded_data):
        user, char = seeded_data
        conv = await ConversationService.create(
            db=session, user_id=user.id, character_id=char.id,
        )
        found = await ConversationService.get_by_id(db=session, conversation_id=conv.id)
        assert found is not None
        assert found.title is None

    @pytest.mark.asyncio
    async def test_get_with_user_filter(self, session, seeded_data):
        """user_id 过滤：只返回该用户的会话"""
        user, char = seeded_data
        conv = await ConversationService.create(
            db=session, user_id=user.id, character_id=char.id,
        )
        # 正确的用户
        found = await ConversationService.get_by_id(
            db=session, conversation_id=conv.id, user_id=user.id,
        )
        assert found is not None

        # 错误的用户
        wrong_user_id = uuid.uuid4()
        not_found = await ConversationService.get_by_id(
            db=session, conversation_id=conv.id, user_id=wrong_user_id,
        )
        assert not_found is None

    @pytest.mark.asyncio
    async def test_get_nonexistent(self, session):
        found = await ConversationService.get_by_id(
            db=session, conversation_id=uuid.uuid4(),
        )
        assert found is None

    @pytest.mark.asyncio
    async def test_get_with_messages(self, session, seeded_data):
        """查询会话时应预加载消息"""
        user, char = seeded_data
        conv = await ConversationService.create(
            db=session, user_id=user.id, character_id=char.id,
        )
        await ConversationService.add_message(
            db=session, conversation_id=conv.id, role="user", content="你好",
        )
        await ConversationService.add_message(
            db=session, conversation_id=conv.id, role="assistant", content="你好呀",
        )

        found = await ConversationService.get_by_id(db=session, conversation_id=conv.id)
        assert found is not None
        assert len(found.messages) == 2
        assert found.messages[0].content == "你好"
        assert found.messages[1].content == "你好呀"


class TestConversationServiceGetByUser:
    """获取用户会话列表"""

    @pytest.mark.asyncio
    async def test_user_conversations(self, session, seeded_data):
        user, char = seeded_data
        await ConversationService.create(db=session, user_id=user.id, character_id=char.id)
        await ConversationService.create(db=session, user_id=user.id, character_id=char.id)

        convs = await ConversationService.get_by_user(db=session, user_id=user.id)
        assert len(convs) == 2

    @pytest.mark.asyncio
    async def test_user_conversations_limit(self, session, seeded_data):
        """limit 参数限制返回数量"""
        user, char = seeded_data
        for _ in range(5):
            await ConversationService.create(db=session, user_id=user.id, character_id=char.id)

        convs = await ConversationService.get_by_user(db=session, user_id=user.id, limit=3)
        assert len(convs) == 3

    @pytest.mark.asyncio
    async def test_user_conversations_ordered(self, session, seeded_data):
        """按 updated_at 降序排列"""
        user, char = seeded_data
        c1 = await ConversationService.create(db=session, user_id=user.id, character_id=char.id)
        c2 = await ConversationService.create(db=session, user_id=user.id, character_id=char.id)

        convs = await ConversationService.get_by_user(db=session, user_id=user.id)
        # c2 更新时间更晚，应排在前面
        assert convs[0].id == c2.id
        assert convs[1].id == c1.id

    @pytest.mark.asyncio
    async def test_other_user_empty(self, session, seeded_data):
        """其他用户无会话"""
        user, char = seeded_data
        await ConversationService.create(db=session, user_id=user.id, character_id=char.id)

        other_id = uuid.uuid4()
        convs = await ConversationService.get_by_user(db=session, user_id=other_id)
        assert convs == []


class TestConversationServiceAddMessage:
    """添加消息"""

    @pytest.mark.asyncio
    async def test_add_user_message(self, session, seeded_data):
        user, char = seeded_data
        conv = await ConversationService.create(
            db=session, user_id=user.id, character_id=char.id,
        )
        msg = await ConversationService.add_message(
            db=session, conversation_id=conv.id, role="user", content="你好孔子",
        )
        assert msg.id is not None
        assert msg.role == "user"
        assert msg.content == "你好孔子"
        assert msg.rag_sources == []

    @pytest.mark.asyncio
    async def test_add_message_with_rag_sources(self, session, seeded_data):
        """带 RAG 来源的消息"""
        user, char = seeded_data
        conv = await ConversationService.create(
            db=session, user_id=user.id, character_id=char.id,
        )
        sources = [
            {"text": "学而时习之", "score": 0.9, "source_type": "dialogue"},
        ]
        msg = await ConversationService.add_message(
            db=session,
            conversation_id=conv.id,
            role="assistant",
            content="学而时习之，不亦说乎。",
            rag_sources=sources,
        )
        assert msg.rag_sources == sources

    @pytest.mark.asyncio
    async def test_add_message_default_rag_sources(self, session, seeded_data):
        """不传 rag_sources 时默认为空列表"""
        user, char = seeded_data
        conv = await ConversationService.create(
            db=session, user_id=user.id, character_id=char.id,
        )
        msg = await ConversationService.add_message(
            db=session,
            conversation_id=conv.id,
            role="assistant",
            content="回复",
        )
        assert msg.rag_sources == []


class TestConversationServiceGetMessages:
    """获取消息历史"""

    @pytest.mark.asyncio
    async def test_get_messages_ordered(self, session, seeded_data):
        """消息按 created_at 升序排列"""
        user, char = seeded_data
        conv = await ConversationService.create(
            db=session, user_id=user.id, character_id=char.id,
        )
        m1 = await ConversationService.add_message(
            db=session, conversation_id=conv.id, role="user", content="第一",
        )
        m2 = await ConversationService.add_message(
            db=session, conversation_id=conv.id, role="assistant", content="第二",
        )
        m3 = await ConversationService.add_message(
            db=session, conversation_id=conv.id, role="user", content="第三",
        )

        messages = await ConversationService.get_messages(db=session, conversation_id=conv.id)
        assert len(messages) == 3
        assert messages[0].id == m1.id
        assert messages[1].id == m2.id
        assert messages[2].id == m3.id

    @pytest.mark.asyncio
    async def test_get_messages_limit(self, session, seeded_data):
        """limit 限制返回条数"""
        user, char = seeded_data
        conv = await ConversationService.create(
            db=session, user_id=user.id, character_id=char.id,
        )
        for i in range(10):
            await ConversationService.add_message(
                db=session, conversation_id=conv.id, role="user", content=f"消息{i}",
            )

        messages = await ConversationService.get_messages(
            db=session, conversation_id=conv.id, limit=5,
        )
        assert len(messages) == 5

    @pytest.mark.asyncio
    async def test_get_messages_empty(self, session, seeded_data):
        """无消息时返回空列表"""
        user, char = seeded_data
        conv = await ConversationService.create(
            db=session, user_id=user.id, character_id=char.id,
        )
        messages = await ConversationService.get_messages(db=session, conversation_id=conv.id)
        assert messages == []
