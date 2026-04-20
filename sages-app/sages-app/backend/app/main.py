"""
人类群星闪耀时 - FastAPI 应用入口
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings

settings = get_settings()


def create_app() -> FastAPI:
    """创建 FastAPI 应用实例"""
    app = FastAPI(
        title=settings.app_name,
        description="AI 驱动的古人对话应用 - 与古代先贤沉浸式对话",
        version="0.1.0",
        debug=settings.debug,
    )

    # === 中间件 ===
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.debug else [],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # === 注册路由 ===
    _register_routers(app)

    # === 生命周期事件 ===
    _register_lifecycle(app)

    return app


def _register_routers(app: FastAPI) -> None:
    """注册所有 API 路由"""
    from api.v1.health import router as health_router
    from api.v1.users import router as users_router
    from api.v1.characters import router as characters_router
    from api.v1.conversations import router as conversations_router
    from api.v1.chat import router as chat_router

    app.include_router(health_router, prefix="/api/v1", tags=["健康检查"])
    app.include_router(users_router, prefix="/api/v1", tags=["用户"])
    app.include_router(characters_router, prefix="/api/v1", tags=["人物"])
    app.include_router(conversations_router, prefix="/api/v1", tags=["会话"])
    app.include_router(chat_router, prefix="/api/v1", tags=["对话"])


def _register_lifecycle(app: FastAPI) -> None:
    """注册启动/关闭事件"""
    @app.on_event("startup")
    async def startup():
        from loguru import logger
        logger.info(f"🚀 {settings.app_name} 启动中...")
        logger.info(f"   环境: {settings.app_env}")
        logger.info(f"   调试模式: {settings.debug}")

    @app.on_event("shutdown")
    async def shutdown():
        from loguru import logger
        logger.info("👋 应用关闭")


# 创建应用实例
app = create_app()
