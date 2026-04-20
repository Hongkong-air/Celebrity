"""
LLM 推理服务 - 对接 vLLM OpenAI 兼容接口
"""
from typing import AsyncGenerator, Optional

import httpx

from app.config import get_settings

settings = get_settings()


class LLMService:
    """vLLM 推理服务封装"""

    def __init__(self, base_url: Optional[str] = None):
        self.base_url = (base_url or settings.llm_base_url).rstrip("/")
        self.model_name = settings.llm_model_name
        self.api_key = settings.llm_api_key

    async def chat(
        self,
        messages: list[dict],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        lora_name: Optional[str] = None,
    ) -> str:
        """
        非流式对话

        Args:
            messages: OpenAI 格式的消息列表
            model: 模型名称（覆盖默认值）
            temperature: 采样温度
            max_tokens: 最大生成 token 数
            lora_name: LoRA 权重名称

        Returns:
            生成的文本
        """
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        body = {
            "model": model or self.model_name,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }

        # vLLM LoRA 动态切换
        if lora_name:
            body["model"] = lora_name

        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                f"{self.base_url}/chat/completions",
                json=body,
                headers=headers,
            )
            resp.raise_for_status()
            data = resp.json()

        return data["choices"][0]["message"]["content"]

    async def stream(
        self,
        messages: list[dict],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        lora_name: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        """
        流式对话（SSE）

        Args:
            messages: OpenAI 格式的消息列表
            model: 模型名称
            temperature: 采样温度
            max_tokens: 最大生成 token 数
            lora_name: LoRA 权重名称

        Yields:
            生成的文本片段
        """
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        body = {
            "model": model or self.model_name,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }

        if lora_name:
            body["model"] = lora_name

        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                json=body,
                headers=headers,
            ) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    line = line.strip()
                    if not line or not line.startswith("data: "):
                        continue
                    data_str = line[6:]  # 去掉 "data: " 前缀
                    if data_str == "[DONE]":
                        break
                    import json
                    try:
                        data = json.loads(data_str)
                        delta = data.get("choices", [{}])[0].get("delta", {})
                        content = delta.get("content", "")
                        if content:
                            yield content
                    except json.JSONDecodeError:
                        continue

    async def health_check(self) -> bool:
        """检查 LLM 服务是否可用"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(f"{self.base_url}/models")
                return resp.status_code == 200
        except Exception:
            return False


# 全局单例
llm_service = LLMService()
