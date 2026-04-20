"""
测试模块 9: LLM 服务 (services/llm_service.py)
覆盖: 初始化、请求构造、流式解析、健康检查（mock）
"""
import pytest
import json
from unittest.mock import AsyncMock, patch, MagicMock
from services.llm_service import LLMService


class TestLLMServiceInit:
    """LLM 服务初始化"""

    def test_default_config(self):
        svc = LLMService()
        assert "localhost:8002" in svc.base_url
        assert svc.model_name == "base-model"

    def test_custom_base_url(self):
        svc = LLMService(base_url="http://gpu-server:8080/v1")
        assert svc.base_url == "http://gpu-server:8080/v1"

    def test_trailing_slash_removed(self):
        svc = LLMService(base_url="http://localhost:8002/v1/")
        assert svc.base_url == "http://localhost:8002/v1"


class TestLLMServiceChat:
    """非流式对话"""

    @pytest.mark.asyncio
    async def test_chat_calls_correct_endpoint(self):
        svc = LLMService(base_url="http://test:8002/v1")
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "你好，吾徒。"}}]
        }
        mock_response.raise_for_status = MagicMock()

        with patch("services.llm_service.httpx.AsyncClient") as mock_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_cls.return_value = mock_client

            result = await svc.chat([{"role": "user", "content": "你好"}])
            assert result == "你好，吾徒。"

            call_args = mock_client.post.call_args
            assert "http://test:8002/v1/chat/completions" in call_args[0][0]
            body = call_args[1]["json"]
            assert body["stream"] is False

    @pytest.mark.asyncio
    async def test_chat_with_lora(self):
        svc = LLMService(base_url="http://test:8002/v1")
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "仁者爱人。"}}]
        }
        mock_response.raise_for_status = MagicMock()

        with patch("services.llm_service.httpx.AsyncClient") as mock_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_cls.return_value = mock_client

            await svc.chat([{"role": "user", "content": "test"}], lora_name="confucius-lora")
            body = mock_client.post.call_args[1]["json"]
            assert body["model"] == "confucius-lora"


class TestLLMServiceStream:
    """流式对话"""

    @pytest.mark.asyncio
    async def test_stream_parses_sse(self):
        svc = LLMService(base_url="http://test:8002/v1")

        # 模拟 SSE 流
        sse_lines = [
            'data: {"choices":[{"delta":{"content":"你"}}]}',
            'data: {"choices":[{"delta":{"content":"好"}}]}',
            'data: {"choices":[{"delta":{"content":"。"}}]}',
            'data: [DONE]',
        ]

        async def mock_aiter_lines():
            for line in sse_lines:
                yield line

        mock_stream_resp = MagicMock()
        mock_stream_resp.aiter_lines = mock_aiter_lines
        mock_stream_resp.raise_for_status = MagicMock()

        # client.stream() 返回一个 async context manager
        mock_stream_ctx = AsyncMock()
        mock_stream_ctx.__aenter__ = AsyncMock(return_value=mock_stream_resp)
        mock_stream_ctx.__aexit__ = AsyncMock(return_value=False)

        with patch("services.llm_service.httpx.AsyncClient") as mock_cls:
            mock_client = AsyncMock()
            mock_client.stream = MagicMock(return_value=mock_stream_ctx)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_cls.return_value = mock_client

            chunks = []
            async for chunk in svc.stream([{"role": "user", "content": "hi"}]):
                chunks.append(chunk)

            assert chunks == ["你", "好", "。"]

    @pytest.mark.asyncio
    async def test_stream_with_lora(self):
        svc = LLMService(base_url="http://test:8002/v1")

        async def empty_lines():
            return
            yield  # empty generator

        mock_stream_resp = MagicMock()
        mock_stream_resp.aiter_lines = empty_lines
        mock_stream_resp.raise_for_status = MagicMock()

        mock_stream_ctx = AsyncMock()
        mock_stream_ctx.__aenter__ = AsyncMock(return_value=mock_stream_resp)
        mock_stream_ctx.__aexit__ = AsyncMock(return_value=False)

        with patch("services.llm_service.httpx.AsyncClient") as mock_cls:
            mock_client = AsyncMock()
            mock_client.stream = MagicMock(return_value=mock_stream_ctx)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_cls.return_value = mock_client

            async for _ in svc.stream([{"role": "user", "content": "test"}], lora_name="libai-lora"):
                pass

            call_kwargs = mock_client.stream.call_args[1]
            assert call_kwargs["json"]["model"] == "libai-lora"


class TestLLMServiceHealthCheck:
    """健康检查"""

    @pytest.mark.asyncio
    async def test_healthy(self):
        svc = LLMService(base_url="http://test:8002/v1")
        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch("services.llm_service.httpx.AsyncClient") as mock_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_cls.return_value = mock_client

            assert await svc.health_check() is True

    @pytest.mark.asyncio
    async def test_unhealthy_connection_error(self):
        svc = LLMService(base_url="http://test:8002/v1")

        with patch("services.llm_service.httpx.AsyncClient") as mock_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.get = AsyncMock(side_effect=Exception("Connection refused"))
            mock_cls.return_value = mock_client

            assert await svc.health_check() is False
