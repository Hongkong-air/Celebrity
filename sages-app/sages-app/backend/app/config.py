"""
人类群星闪耀时 - 全局配置
通过 pydantic-settings 从环境变量加载配置
所有环境变量使用 SAGES_ 前缀，避免与其他项目冲突
"""
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

# 项目根目录 (backend/)
BACKEND_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """应用配置，所有字段均可通过 SAGES_ 前缀的环境变量覆盖"""

    # === 应用 ===
    app_name: str = "SagesApp"
    app_env: str = "development"
    debug: bool = True
    secret_key: str = "change-me-in-production"

    # === 数据库 ===
    database_url: str = "postgresql+asyncpg://sages:sages123@localhost:5432/sages_db"

    # === Redis ===
    redis_url: str = "redis://localhost:6379/0"

    # === Qdrant ===
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "sages"

    # === Embedding 服务 ===
    embedding_service_url: str = "http://localhost:8001"

    # === LLM 服务 ===
    llm_base_url: str = "http://localhost:8002/v1"
    llm_model_name: str = "base-model"
    llm_api_key: str = "not-needed"

    # === JWT ===
    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440  # 24h

    # === 限流 ===
    rate_limit_per_minute: int = 30

    model_config = SettingsConfigDict(
        env_prefix="SAGES_",
        env_file=str(BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


@lru_cache()
def get_settings() -> Settings:
    """获取全局配置单例"""
    return Settings()
