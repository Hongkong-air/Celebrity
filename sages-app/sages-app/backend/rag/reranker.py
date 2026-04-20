"""
重排序模块 - 调用 bge-reranker 微服务精排
"""
from rag.encoder import embedding_client
from rag.schemas import RetrievalResult


async def rerank(
    query: str,
    results: list[RetrievalResult],
    top_k: int = 3,
) -> list[RetrievalResult]:
    """
    对检索结果进行重排序

    Args:
        query: 用户查询
        results: 初步检索结果
        top_k: 返回前 k 个

    Returns:
        重排序后的结果
    """
    if not results:
        return []

    documents = [r.text for r in results]
    ranked = await embedding_client.rerank(query, documents, top_k=top_k)

    return [
        results[idx]
        for idx, score in ranked
    ]
