"""
混合检索器 - Dense + Sparse 向量检索 + RRF 融合
"""
from typing import Optional

from qdrant_client import AsyncQdrantClient
from qdrant_client.models import (
    Filter, FieldCondition, MatchValue,
    NamedVector, NamedSparseVector,
    FusionQuery, Fusion,
    models,
)

from app.config import get_settings
from rag.schemas import RetrievalResult, SourceType

settings = get_settings()


class HybridRetriever:
    """Qdrant 混合检索器"""

    def __init__(self):
        self.client: Optional[AsyncQdrantClient] = None
        self.collection = settings.qdrant_collection

    async def connect(self):
        """建立 Qdrant 连接"""
        if self.client is None:
            self.client = AsyncQdrantClient(url=settings.qdrant_url)

    async def ensure_collection(self):
        """确保 collection 存在且配置正确"""
        await self.connect()
        collections = await self.client.get_collections()
        exists = any(c.name == self.collection for c in collections.collections)

        if not exists:
            await self.client.create_collection(
                collection_name=self.collection,
                vectors_config={
                    "dense": models.VectorParams(
                        size=1024,  # bge-m3 输出维度
                        distance=models.Distance.COSINE,
                    ),
                },
                sparse_vectors_config={
                    "sparse": models.SparseVectorParams(
                        index=models.SparseIndexParams(on_disk=False),
                    ),
                },
            )

    async def retrieve(
        self,
        query_dense: list[float],
        query_sparse: dict[int, float],
        character: str,
        top_k: int = 10,
    ) -> list[RetrievalResult]:
        """
        混合检索：Dense + Sparse + RRF 融合

        Args:
            query_dense: 稠密查询向量
            query_sparse: 稀疏查询向量 {token_id: weight}
            character: 人物 slug（用于 metadata 过滤）
            top_k: 返回结果数量

        Returns:
            检索结果列表
        """
        await self.ensure_collection()

        # 构造人物过滤条件
        character_filter = Filter(
            must=[
                FieldCondition(key="character", match=MatchValue(value=character))
            ]
        )

        # 使用 Qdrant 的 RRF (Reciprocal Rank Fusion) 查询
        results = await self.client.query_points(
            collection_name=self.collection,
            prefetch=[
                # Dense 向量检索
                models.Prefetch(
                    query=models.NamedVector(name="dense", vector=query_dense),
                    filter=character_filter,
                    limit=top_k,
                ),
                # Sparse 向量检索
                models.Prefetch(
                    query=models.NamedSparseVector(
                        name="sparse",
                        vector=models.SparseVector(
                            indices=list(query_sparse.keys()),
                            values=list(query_sparse.values()),
                        ),
                    ),
                    filter=character_filter,
                    limit=top_k,
                ),
            ],
            query=FusionQuery(fusion=Fusion.RRF),
            limit=top_k,
            with_payload=True,
        )

        retrieval_results = []
        for point in results.points:
            payload = point.payload or {}
            retrieval_results.append(RetrievalResult(
                text=payload.get("text", ""),
                score=float(point.score),
                source_type=payload.get("source_type", "unknown"),
                source_work=payload.get("source_work"),
                topic=payload.get("topic", []),
                metadata=payload,
            ))

        return retrieval_results


# 全局单例
retriever = HybridRetriever()
