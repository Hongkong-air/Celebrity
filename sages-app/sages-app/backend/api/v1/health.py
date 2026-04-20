"""
健康检查接口
"""
from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check():
    """基础健康检查"""
    return {
        "status": "ok",
        "service": "sages-app",
    }


@router.get("/health/ready")
async def readiness_check():
    """
    就绪检查 - 验证所有依赖服务是否可用
    当前为基础版本，后续逐步添加各服务检查
    """
    checks = {
        "api": True,
        "database": False,  # 阶段2实现后启用
        "redis": False,     # 阶段3实现后启用
        "qdrant": False,    # 阶段7实现后启用
        "embedding": False, # 阶段6实现后启用
        "llm": False,       # 阶段8实现后启用
    }

    all_ready = all(checks.values())
    status_code = "ok" if all_ready else "degraded"

    return {
        "status": status_code,
        "checks": checks,
    }
