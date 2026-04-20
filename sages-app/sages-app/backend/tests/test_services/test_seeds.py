"""
测试模块 10: 种子数据 (db/seeds/characters.json)
覆盖: JSON 格式、必填字段、system_prompt 完整性
"""
import json
import pytest
from pathlib import Path


class TestCharacterSeeds:
    """人物种子数据"""

    @pytest.fixture
    def seed_path(self):
        return Path(__file__).resolve().parent.parent.parent / "db" / "seeds" / "characters.json"

    @pytest.fixture
    def characters(self, seed_path):
        with open(seed_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def test_file_exists(self, seed_path):
        assert seed_path.exists()

    def test_is_list(self, characters):
        assert isinstance(characters, list)

    def test_at_least_two_characters(self, characters):
        assert len(characters) >= 2

    def test_confucius_exists(self, characters):
        slugs = [c["slug"] for c in characters]
        assert "confucius" in slugs

    def test_libai_exists(self, characters):
        slugs = [c["slug"] for c in characters]
        assert "libai" in slugs

    @pytest.mark.parametrize("field", ["slug", "name", "era", "description", "system_prompt", "is_active"])
    def test_required_fields(self, characters, field):
        for c in characters:
            assert field in c, f"人物 {c.get('slug', '?')} 缺少字段 {field}"

    def test_slugs_are_unique(self, characters):
        slugs = [c["slug"] for c in characters]
        assert len(slugs) == len(set(slugs))

    def test_system_prompt_min_length(self, characters):
        for c in characters:
            assert len(c["system_prompt"]) >= 100, \
                f"{c['slug']} 的 system_prompt 太短 ({len(c['system_prompt'])} 字符)"

    def test_system_prompt_contains_personality(self, characters):
        """system_prompt 应包含人格定义关键词"""
        for c in characters:
            sp = c["system_prompt"]
            # 应包含说话风格或性格描述
            assert any(kw in sp for kw in ["风格", "性格", "说话", "自称", "态度"]), \
                f"{c['slug']} 的 system_prompt 缺少人格描述"

    def test_is_active_boolean(self, characters):
        for c in characters:
            assert isinstance(c["is_active"], bool)

    def test_lora_name_format(self, characters):
        for c in characters:
            if c.get("lora_name"):
                assert isinstance(c["lora_name"], str)
                assert len(c["lora_name"]) > 0
