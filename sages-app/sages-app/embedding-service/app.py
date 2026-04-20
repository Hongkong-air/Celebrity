"""
Embedding + Reranker 独立微服务
提供 bge-m3 编码和 bge-reranker-v2-m3 重排序能力
"""
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional
import asyncio

app = FastAPI(
    title="Sages Embedding Service",
    description="bge-m3 编码 + bge-reranker-v2-m3 重排序微服务",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === 全局模型实例 ===
_encoder = None
_reranker = None
_model_loading = False
_model_loaded = False
_load_error: str | None = None  # 记录加载失败原因


# === 请求/响应模型 ===

class EmbedRequest(BaseModel):
    texts: list[str] = Field(..., min_length=1, max_length=32, description="待编码文本列表")
    batch_size: int = Field(32, ge=1, le=128, description="批处理大小")


class EmbedResponse(BaseModel):
    dense_embeddings: list[list[float]] = Field(description="稠密向量列表")
    sparse_embeddings: list[dict] = Field(description="稀疏向量列表 (token_id -> weight)")


class RerankRequest(BaseModel):
    query: str = Field(..., description="查询文本")
    documents: list[str] = Field(..., min_length=1, max_length=50, description="待排序文档列表")
    top_k: int = Field(3, ge=1, le=50, description="返回 top-k 结果")


class RerankResult(BaseModel):
    index: int
    document: str
    score: float


class RerankResponse(BaseModel):
    results: list[RerankResult]


# === 模型加载 ===

async def load_models():
    """异步加载模型（首次请求时触发）"""
    global _encoder, _reranker, _model_loading, _model_loaded, _load_error

    if _model_loaded or _model_loading:
        return

    _model_loading = True
    try:
        import torch
        from FlagEmbedding import FlagModel, FlagReranker

        device = "cuda" if torch.cuda.is_available() else "cpu"

        # 加载 bge-m3 编码器
        _encoder = FlagModel(
            "BAAI/bge-m3",
            use_fp16=(device == "cuda"),
            device=device,
        )

        # 加载 bge-reranker-v2-m3
        _reranker = FlagReranker(
            "BAAI/bge-reranker-v2-m3",
            use_fp16=(device == "cuda"),
            device=device,
        )

        _model_loaded = True
        _load_error = None
        print(f"✅ 模型加载完成 (device={device})")
    except Exception as e:
        _load_error = str(e)
        print(f"❌ 模型加载失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"模型加载失败: {e}。请确保已安装 torch 和 FlagEmbedding。",
        )
    finally:
        _model_loading = False


def _ensure_model_loaded():
    """检查模型是否已加载，未加载则抛出友好错误"""
    if _model_loaded:
        return
    if _load_error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"模型不可用: {_load_error}",
        )
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="模型正在加载中，请稍后重试",
    )


# === 接口 ===

@app.post("/embed", response_model=EmbedResponse)
async def embed(req: EmbedRequest):
    """
    文本编码 - 返回 dense + sparse 双向量

    使用 bge-m3 模型，支持中英文混合文本。
    dense: 1024维稠密向量，用于语义检索
    sparse: 稀疏向量，用于关键词匹配
    """
    if not _model_loaded:
        await load_models()
    _ensure_model_loaded()

    # 在线程池中执行 CPU/GPU 密集型操作
    loop = asyncio.get_event_loop()

    dense_embeddings, sparse_embeddings = await loop.run_in_executor(
        None,
        lambda: _encoder.encode(
            req.texts,
            batch_size=req.batch_size,
            return_dense=True,
            return_sparse=True,
        ),
    )

    # 转换 sparse 格式
    sparse_list = []
    for sparse in sparse_embeddings:
        if hasattr(sparse, 'indices') and hasattr(sparse, 'values'):
            sparse_list.append({
                'indices': sparse.indices.tolist(),
                'values': sparse.values.tolist(),
            })
        else:
            sparse_list.append({})

    return EmbedResponse(
        dense_embeddings=[e.tolist() for e in dense_embeddings],
        sparse_embeddings=sparse_list,
    )


@app.post("/rerank", response_model=RerankResponse)
async def rerank(req: RerankRequest):
    """
    文档重排序 - 使用 cross-encoder 精排

    输入查询和候选文档列表，返回按相关性排序的结果。
    """
    if not _model_loaded:
        await load_models()
    _ensure_model_loaded()

    loop = asyncio.get_event_loop()

    # 构造 reranker 输入对
    pairs = [[req.query, doc] for doc in req.documents]

    scores = await loop.run_in_executor(
        None,
        lambda: _reranker.compute_score(pairs),
    )

    # 排序并返回 top_k
    scored_docs = list(zip(range(len(req.documents)), req.documents, scores))
    scored_docs.sort(key=lambda x: x[2], reverse=True)

    results = [
        RerankResult(index=idx, document=doc, score=float(score))
        for idx, doc, score in scored_docs[:req.top_k]
    ]

    return RerankResponse(results=results)


@app.get("/health")
async def health():
    """健康检查"""
    return {
        "status": "ok",
        "service": "embedding-service",
        "model_loaded": _model_loaded,
    }


@app.get("/health/ready")
async def ready():
    """就绪检查"""
    return {
        "status": "ready" if _model_loaded else "loading",
        "encoder": _encoder is not None,
        "reranker": _reranker is not None,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
