"""
人物 API - 列表、详情
"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from services.character_service import CharacterService

router = APIRouter()


# === 响应模型 ===

class CharacterResponse(BaseModel):
    id: str
    slug: str
    name: str
    era: str | None
    description: str | None
    avatar_url: str | None
    is_active: bool

    class Config:
        from_attributes = True


class CharacterDetailResponse(CharacterResponse):
    system_prompt: str
    lora_name: str | None


# === 接口 ===

@router.get("/characters", response_model=list[CharacterResponse])
async def list_characters(
    active_only: bool = Query(True, description="仅返回已激活的人物"),
    db: AsyncSession = Depends(get_db),
):
    """获取所有可用人物列表"""
    characters = await CharacterService.get_all(db, active_only=active_only)
    return [CharacterResponse.model_validate(c) for c in characters]


@router.get("/characters/{character_id}", response_model=CharacterDetailResponse)
async def get_character(
    character_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """获取人物详情"""
    character = await CharacterService.get_by_id(db, character_id)
    if not character:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="人物不存在",
        )
    return CharacterDetailResponse.model_validate(character)
