"""
会话与消息 API
"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from middleware.auth import get_current_user_id
from services.conversation_service import ConversationService

router = APIRouter()


# === 响应模型 ===

class MessageResponse(BaseModel):
    id: str
    role: str
    content: str
    rag_sources: list | None
    created_at: str

    class Config:
        from_attributes = True


class ConversationResponse(BaseModel):
    id: str
    character_id: str
    title: str | None
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class ConversationDetailResponse(ConversationResponse):
    messages: list[MessageResponse] = []


class CreateConversationRequest(BaseModel):
    character_id: str
    title: str | None = None


# === 接口 ===

@router.post("/conversations", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    req: CreateConversationRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """创建新会话"""
    conv = await ConversationService.create(
        db,
        user_id=UUID(user_id),
        character_id=UUID(req.character_id),
        title=req.title,
    )
    return ConversationResponse.model_validate(conv)


@router.get("/conversations", response_model=list[ConversationResponse])
async def list_conversations(
    character_id: str | None = Query(None, description="按人物过滤"),
    limit: int = Query(20, ge=1, le=100),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """获取当前用户的会话列表"""
    char_uuid = UUID(character_id) if character_id else None
    conversations = await ConversationService.list_by_user(
        db, UUID(user_id), character_id=char_uuid, limit=limit
    )
    return [ConversationResponse.model_validate(c) for c in conversations]


@router.get("/conversations/{conversation_id}", response_model=ConversationDetailResponse)
async def get_conversation(
    conversation_id: UUID,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """获取会话详情（含消息历史）"""
    conv = await ConversationService.get_by_id(db, conversation_id, user_id=UUID(user_id))
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="会话不存在")
    return ConversationDetailResponse(
        id=str(conv.id),
        character_id=str(conv.character_id),
        title=conv.title,
        created_at=conv.created_at.isoformat(),
        updated_at=conv.updated_at.isoformat(),
        messages=[MessageResponse.model_validate(m) for m in conv.messages],
    )


@router.get("/conversations/{conversation_id}/messages", response_model=list[MessageResponse])
async def get_messages(
    conversation_id: UUID,
    limit: int = Query(50, ge=1, le=200),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """获取会话的消息历史"""
    conv = await ConversationService.get_by_id(db, conversation_id, user_id=UUID(user_id))
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="会话不存在")
    messages = await ConversationService.get_messages(db, conversation_id, limit=limit)
    return [MessageResponse.model_validate(m) for m in messages]
