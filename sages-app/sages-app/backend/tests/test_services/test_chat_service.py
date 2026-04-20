"""
测试模块 12: 对话编排服务 (services/chat_service.py)
覆盖: ChatService 初始化、编排流程（mock 所有外部依赖）
"""
import pytest
import uuid
from unittest.mock import AsyncMock, patch, MagicMock
from services.chat_service import ChatService


class TestChatServiceInit:
    """ChatService 初始化"""

    def test_create(self):
        svc = ChatService()
        assert svc is not None
        assert svc.retriever is not None


class TestChatServiceOrchestration:
    """对话编排流程（mock 测试）"""

    @pytest.mark.asyncio
    async def test_chat_character_not_found(self):
        """人物不存在时应返回 error"""
        svc = ChatService()
        mock_db = AsyncMock()

        with patch("services.chat_service.CharacterService.get_by_id", return_value=None):
            chunks = []
            async for chunk in svc.chat(
                db=mock_db,
                user_id=uuid.uuid4(),
                character_id=uuid.uuid4(),
                message="你好",
            ):
                chunks.append(chunk)

            assert len(chunks) == 1
            assert chunks[0]["type"] == "error"
            assert "不存在" in chunks[0]["content"]

    @pytest.mark.asyncio
    async def test_chat_sync_raises_on_error(self):
        """非流式接口遇到 error 应抛出 RuntimeError"""
        svc = ChatService()
        mock_db = AsyncMock()

        with patch("services.chat_service.CharacterService.get_by_id", return_value=None):
            with pytest.raises(RuntimeError, match="不存在"):
                await svc.chat_sync(
                    db=mock_db,
                    user_id=uuid.uuid4(),
                    character_id=uuid.uuid4(),
                    message="test",
                )
