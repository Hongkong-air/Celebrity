"""
对话 API - 流式/非流式对话接口
"""
import json
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from middleware.auth import get_current_user_id
from services.chat_service import chat_service

router = APIRouter()


# === 请求模型 ===

class ChatRequest(BaseModel):
    character_id: str
    message: str
    conversation_id: str | None = None


class ChatSyncResponse(BaseModel):
    content: str
    conversation_id: str
    message_id: str


# === 接口 ===

@router.post("/chat")
async def chat_stream(
    req: ChatRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    流式对话接口 (SSE)

    返回 Server-Sent Events 流:
    - data: {"type": "token", "content": "..."}
    - data: {"type": "done", "conversation_id": "...", "message_id": "..."}
    - data: {"type": "error", "content": "..."}
    """
    async def event_generator():
        async for chunk in chat_service.chat(
            db=db,
            user_id=UUID(user_id),
            character_id=UUID(req.character_id),
            message=req.message,
            conversation_id=UUID(req.conversation_id) if req.conversation_id else None,
        ):
            yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/chat/sync", response_model=ChatSyncResponse)
async def chat_sync_endpoint(
    req: ChatRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """非流式对话接口（等待完整响应后返回）"""
    try:
        result = await chat_service.chat_sync(
            db=db,
            user_id=UUID(user_id),
            character_id=UUID(req.character_id),
            message=req.message,
            conversation_id=UUID(req.conversation_id) if req.conversation_id else None,
        )
        return ChatSyncResponse(**result)
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))
