"""
用户 API - 注册、登录、个人信息
"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from middleware.auth import get_current_user_id
from services.user_service import UserService

router = APIRouter()


# === 请求/响应模型 ===

class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=2, max_length=100, pattern=r"^[a-zA-Z0-9_\u4e00-\u9fff]+$",
                          description="用户名，支持中英文、数字和下划线")
    password: str = Field(..., min_length=6, max_length=128, description="密码，至少6位")


class LoginRequest(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: str
    username: str
    created_at: str

    class Config:
        from_attributes = True


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# === 接口 ===

@router.post("/users/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """用户注册"""
    try:
        user = await UserService.register(db, req.username, req.password)
        token = UserService.authenticate.__func__  # just get token
        # 重新获取 token
        from middleware.auth import create_access_token
        access_token = create_access_token(data={"sub": str(user.id)})
        return AuthResponse(
            access_token=access_token,
            user=UserResponse(
                id=str(user.id),
                username=user.username,
                created_at=user.created_at.isoformat(),
            ),
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.post("/users/login", response_model=AuthResponse)
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    """用户登录"""
    try:
        user, token = await UserService.authenticate(db, req.username, req.password)
        return AuthResponse(
            access_token=token,
            user=UserResponse(
                id=str(user.id),
                username=user.username,
                created_at=user.created_at.isoformat(),
            ),
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.get("/users/me", response_model=UserResponse)
async def get_me(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """获取当前用户信息"""
    user = await UserService.get_by_id(db, UUID(user_id))
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
    return UserResponse(
        id=str(user.id),
        username=user.username,
        created_at=user.created_at.isoformat(),
    )
