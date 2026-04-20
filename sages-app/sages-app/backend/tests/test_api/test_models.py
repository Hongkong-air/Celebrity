"""
测试模块 3: ORM 数据模型 (models/)
覆盖: 模型字段、关系、约束、默认值
"""
import pytest
from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.dependencies import Base
from models import User, Character, Conversation, Message


# 使用 SQLite 内存数据库
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


class TestUserModel:
    """用户模型"""

    def test_table_name(self):
        assert User.__tablename__ == "users"

    def test_columns_exist(self):
        mapper = inspect(User)
        cols = {c.key for c in mapper.columns}
        assert cols == {"id", "username", "password_hash", "preferences", "created_at"}

    def test_username_unique(self):
        mapper = inspect(User)
        username_col = [c for c in mapper.columns if c.key == "username"][0]
        assert username_col.unique is True

    def test_preferences_default(self):
        mapper = inspect(User)
        prefs_col = [c for c in mapper.columns if c.key == "preferences"][0]
        assert prefs_col.default is not None


class TestCharacterModel:
    """人物模型"""

    def test_table_name(self):
        assert Character.__tablename__ == "characters"

    def test_columns_exist(self):
        mapper = inspect(Character)
        cols = {c.key for c in mapper.columns}
        expected = {"id", "slug", "name", "era", "system_prompt",
                     "lora_name", "avatar_url", "description", "is_active", "created_at"}
        assert cols == expected

    def test_slug_unique(self):
        mapper = inspect(Character)
        slug_col = [c for c in mapper.columns if c.key == "slug"][0]
        assert slug_col.unique is True


class TestConversationModel:
    """会话模型"""

    def test_table_name(self):
        assert Conversation.__tablename__ == "conversations"

    def test_columns_exist(self):
        mapper = inspect(Conversation)
        cols = {c.key for c in mapper.columns}
        assert cols == {"id", "user_id", "character_id", "title", "created_at", "updated_at"}

    def test_foreign_keys(self):
        mapper = inspect(Conversation)
        for col in mapper.columns:
            if col.key == "user_id":
                assert col.foreign_keys
            if col.key == "character_id":
                assert col.foreign_keys


class TestMessageModel:
    """消息模型"""

    def test_table_name(self):
        assert Message.__tablename__ == "messages"

    def test_columns_exist(self):
        mapper = inspect(Message)
        cols = {c.key for c in mapper.columns}
        assert cols == {"id", "conversation_id", "role", "content", "rag_sources", "created_at"}

    def test_conversation_fk(self):
        mapper = inspect(Message)
        conv_col = [c for c in mapper.columns if c.key == "conversation_id"][0]
        assert conv_col.foreign_keys


class TestModelRelationships:
    """模型关系"""

    def test_user_has_conversations(self):
        mapper = inspect(User)
        rels = {r.key: r.mapper.class_ for r in mapper.relationships}
        assert "conversations" in rels
        assert rels["conversations"] == Conversation

    def test_character_has_conversations(self):
        mapper = inspect(Character)
        rels = {r.key: r.mapper.class_ for r in mapper.relationships}
        assert "conversations" in rels

    def test_conversation_has_messages(self):
        mapper = inspect(Conversation)
        rels = {r.key: r.mapper.class_ for r in mapper.relationships}
        assert "messages" in rels
        assert rels["messages"] == Message

    def test_message_belongs_to_conversation(self):
        mapper = inspect(Message)
        rels = {r.key: r.mapper.class_ for r in mapper.relationships}
        assert "conversation" in rels
        assert rels["conversation"] == Conversation


class TestDatabaseCRUD:
    """实际数据库 CRUD 操作（SQLite 内存库）"""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_create_and_get_user(self, session):
        user = User(
            username="testuser",
            password_hash="hashed_pw",
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        assert user.id is not None
        assert user.username == "testuser"

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_create_character(self, session):
        char = Character(
            slug="test-sage",
            name="测试先贤",
            era="测试朝代",
            system_prompt="你是测试先贤。",
        )
        session.add(char)
        await session.commit()
        await session.refresh(char)
        assert char.id is not None
        assert char.slug == "test-sage"
        assert char.is_active is True

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_create_conversation_and_messages(self, session):
        user = User(username="u", password_hash="h")
        char = Character(slug="c", name="n", system_prompt="s")
        session.add(user)
        session.add(char)
        await session.flush()

        conv = Conversation(user_id=user.id, character_id=char.id, title="测试对话")
        session.add(conv)
        await session.flush()

        msg1 = Message(conversation_id=conv.id, role="user", content="你好")
        msg2 = Message(conversation_id=conv.id, role="assistant", content="你好呀")
        session.add(msg1)
        session.add(msg2)
        await session.commit()

        # 验证
        assert msg1.id is not None
        assert msg2.id is not None
        assert msg1.role == "user"
        assert msg2.role == "assistant"
