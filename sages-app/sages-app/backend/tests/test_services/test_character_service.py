"""
测试模块: 人物服务 (services/character_service.py)
覆盖: CRUD 操作（获取全部、按ID、按slug、创建、更新）
"""
import pytest
import uuid
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.dependencies import Base
from models.character import Character
from services.character_service import CharacterService


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
async def sample_characters(session):
    """预置测试人物数据"""
    chars = []
    for i, (slug, name, era) in enumerate([
        ("confucius", "孔子", "春秋"),
        ("libai", "李白", "唐代"),
        ("laozi", "老子", "春秋"),
    ]):
        c = Character(
            slug=slug,
            name=name,
            era=era,
            system_prompt=f"你是{name}。",
            is_active=(i != 2),  # 老子设为 inactive
        )
        session.add(c)
        chars.append(c)
    await session.flush()
    for c in chars:
        await session.refresh(c)
    return chars


class TestCharacterServiceGetAll:
    """获取人物列表"""

    @pytest.mark.asyncio
    async def test_get_all_active_only(self, session, sample_characters):
        """active_only=True 只返回活跃人物"""
        result = await CharacterService.get_all(db=session, active_only=True)
        names = [c.name for c in result]
        assert "孔子" in names
        assert "李白" in names
        assert "老子" not in names

    @pytest.mark.asyncio
    async def test_get_all_include_inactive(self, session, sample_characters):
        """active_only=False 返回所有人物"""
        result = await CharacterService.get_all(db=session, active_only=False)
        names = [c.name for c in result]
        assert len(names) == 3
        assert "老子" in names

    @pytest.mark.asyncio
    async def test_get_all_ordered_by_created_at(self, session, sample_characters):
        """结果按 created_at 排序"""
        result = await CharacterService.get_all(db=session, active_only=False)
        for i in range(len(result) - 1):
            assert result[i].created_at <= result[i + 1].created_at

    @pytest.mark.asyncio
    async def test_get_all_empty(self, session):
        """无数据时返回空列表"""
        result = await CharacterService.get_all(db=session)
        assert result == []


class TestCharacterServiceGetById:
    """按 ID 查询"""

    @pytest.mark.asyncio
    async def test_get_existing(self, session, sample_characters):
        char = sample_characters[0]
        found = await CharacterService.get_by_id(db=session, character_id=char.id)
        assert found is not None
        assert found.name == "孔子"

    @pytest.mark.asyncio
    async def test_get_nonexistent(self, session):
        found = await CharacterService.get_by_id(db=session, character_id=uuid.uuid4())
        assert found is None


class TestCharacterServiceGetBySlug:
    """按 slug 查询"""

    @pytest.mark.asyncio
    async def test_get_existing_slug(self, session, sample_characters):
        found = await CharacterService.get_by_slug(db=session, slug="confucius")
        assert found is not None
        assert found.name == "孔子"

    @pytest.mark.asyncio
    async def test_get_nonexistent_slug(self, session):
        found = await CharacterService.get_by_slug(db=session, slug="nonexistent")
        assert found is None


class TestCharacterServiceCreate:
    """创建人物"""

    @pytest.mark.asyncio
    async def test_create_success(self, session):
        char = await CharacterService.create(
            db=session,
            slug="mencius",
            name="孟子",
            era="战国",
            system_prompt="你是孟子。",
        )
        assert char.id is not None
        assert char.slug == "mencius"
        assert char.name == "孟子"
        assert char.is_active is True

    @pytest.mark.asyncio
    async def test_create_with_all_fields(self, session):
        char = await CharacterService.create(
            db=session,
            slug="zhuangzi",
            name="庄子",
            era="战国",
            system_prompt="你是庄子。",
            description="道家代表人物",
            avatar_url="https://example.com/zhuangzi.jpg",
            lora_name="zhuangzi-lora",
        )
        assert char.description == "道家代表人物"
        assert char.avatar_url == "https://example.com/zhuangzi.jpg"
        assert char.lora_name == "zhuangzi-lora"


class TestCharacterServiceUpdate:
    """更新人物"""

    @pytest.mark.asyncio
    async def test_update_existing(self, session, sample_characters):
        char = sample_characters[0]
        updated = await CharacterService.update(
            db=session,
            character_id=char.id,
            description="儒家创始人",
        )
        assert updated is not None
        assert updated.description == "儒家创始人"

    @pytest.mark.asyncio
    async def test_update_nonexistent(self, session):
        updated = await CharacterService.update(
            db=session,
            character_id=uuid.uuid4(),
            name="不存在",
        )
        assert updated is None

    @pytest.mark.asyncio
    async def test_update_multiple_fields(self, session, sample_characters):
        char = sample_characters[0]
        updated = await CharacterService.update(
            db=session,
            character_id=char.id,
            name="孔仲尼",
            era="春秋末期",
            is_active=False,
        )
        assert updated.name == "孔仲尼"
        assert updated.era == "春秋末期"
        assert updated.is_active is False

    @pytest.mark.asyncio
    async def test_update_ignores_unknown_fields(self, session, sample_characters):
        """更新不存在的字段应被忽略（不报错）"""
        char = sample_characters[0]
        updated = await CharacterService.update(
            db=session,
            character_id=char.id,
            nonexistent_field="value",  # 不存在的字段
        )
        assert updated is not None
        # 不应崩溃
