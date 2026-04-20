"""
Embedding 编码器 - 调用 Embedding 微服务
"""
from dataclasses import dataclass
from typing import Optional

import httpx

from app.config import get_settings

settings = get_settings()


@dataclass
class EmbedOutput:
    """Embedding 输出"""
    dense: list[float]
    sparse: dict[int, float]  # token_id -> weight


class EmbeddingClient:
    """Embedding 微服务客户端"""

    def __init__(self, base_url: Optional[str] = None):
        self.base_url = (base_url or settings.embedding_service_url).rstrip("/")

    async def embed(self, texts: list[str]) -> list[EmbedOutput]:
        """
        调用 Embedding 服务获取 dense + sparse 向量

        Args:
            texts: 待编码文本列表

        Returns:
            EmbedOutput 列表
        """
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{self.base_url}/embed",
                json={"texts": texts},
            )
            resp.raise_for_status()
            data = resp.json()

        outputs = []
        for dense, sparse in zip(data["dense_embeddings"], data["sparse_embeddings"]):
            # sparse 是 {str(token_id): weight}，转为 int key
            sparse_int = {int(k): v for k, v in sparse.items()}
            outputs.append(EmbedOutput(dense=dense, sparse=sparse_int))
        return outputs

    async def embed_single(self, text: str) -> EmbedOutput:
        """编码单条文本"""
        results = await self.embed([text])
        return results[0]

    async def rerank(
        self,
        query: str,
        documents: list[str],
        top_k: int = 3,
    ) -> list[tuple[int, float]]:
        """
        调用 Reranker 服务对文档重排序

        Args:
            query: 查询文本
            documents: 候选文档列表
            top_k: 返回前 k 个结果

        Returns:
            [(原始索引, 分数), ...] 按分数降序
        """
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{self.base_url}/rerank",
                json={
                    "query": query,
                    "documents": documents,
                    "top_k": top_k,
                },
            )
            resp.raise_for_status()
            data = resp.json()

        return [(r["index"], r["score"]) for r in data["results"]]


# 全局单例
embedding_client = EmbeddingClient()
