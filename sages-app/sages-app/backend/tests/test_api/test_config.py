"""
测试模块 2: 配置 (app/config.py)
覆盖: 默认值、环境变量覆盖、SAGES_ 前缀隔离
"""
import os
import pytest


class TestSettings:
    """配置加载测试"""

    def test_default_values(self):
        from app.config import Settings
        # 注意：conftest 设置了 SAGES_JWT_EXPIRE_MINUTES=60，这里测试实际生效值
        s = Settings(_env_file=None)
        assert s.app_name == "SagesApp"
        assert s.app_env == "development"
        assert s.debug is True
        assert s.jwt_algorithm == "HS256"
        assert s.jwt_expire_minutes == 60  # conftest 设置的测试值
        assert s.rate_limit_per_minute == 30
        assert s.qdrant_collection == "sages"

    def test_env_prefix_isolation(self):
        """SAGES_ 前缀确保不与系统 DATABASE_URL 冲突"""
        from app.config import Settings
        # 设置一个不带前缀的环境变量
        os.environ["DATABASE_URL"] = "sqlite:///wrong.db"
        os.environ["SAGES_DATABASE_URL"] = "postgresql://correct:db"
        try:
            s = Settings(_env_file=None)
            assert s.database_url == "postgresql://correct:db"
        finally:
            os.environ.pop("DATABASE_URL", None)
            os.environ.pop("SAGES_DATABASE_URL", None)

    def test_env_override(self):
        from app.config import Settings
        os.environ["SAGES_APP_NAME"] = "TestApp"
        os.environ["SAGES_DEBUG"] = "false"
        try:
            s = Settings(_env_file=None)
            assert s.app_name == "TestApp"
            assert s.debug is False
        finally:
            os.environ.pop("SAGES_APP_NAME", None)
            os.environ.pop("SAGES_DEBUG", None)

    def test_lru_cache_singleton(self):
        from app.config import get_settings
        s1 = get_settings()
        s2 = get_settings()
        assert s1 is s2

    def test_all_service_urls_have_defaults(self):
        from app.config import Settings
        s = Settings(_env_file=None)
        assert s.database_url
        assert s.redis_url
        assert s.qdrant_url
        assert s.embedding_service_url
        assert s.llm_base_url
