"""
索引构建器 - 将数据入库到 Qdrant
"""
import json
import uuid
from pathlib import Path

from qdrant_client import AsyncQdrantClient
from qdrant_client.models import models

from app.config import get_settings
from rag.encoder import embedding_client
from rag.schemas import SourceType

settings = get_settings()


async def build_index(
    data_dir: str | Path,
    character: str,
    batch_size: int = 32,
):
    """
    从数据目录构建 Qdrant 索引

    Args:
        data_dir: 数据目录路径（包含 JSONL 文件）
        character: 人物 slug（如 "confucius"）
        batch_size: 批量入库大小
    """
    data_dir = Path(data_dir)
    client = AsyncQdrantClient(url=settings.qdrant_url)

    # 确保 collection 存在
    from rag.retriever import HybridRetriever
    retriever = HybridRetriever()
    await retriever.ensure_collection()

    # 读取所有 JSONL 文件
    all_records = []
    for jsonl_file in sorted(data_dir.glob("*.jsonl")):
        with open(jsonl_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    all_records.append(json.loads(line))

    print(f"📖 读取 {len(all_records)} 条记录")

    # 分批编码并入库
    for i in range(0, len(all_records), batch_size):
        batch = all_records[i:i + batch_size]
        texts = [r["text"] for r in batch]

        # 调用 Embedding 服务
        embeddings = await embedding_client.embed(texts)

        # 构造 Qdrant points
        points = []
        for record, emb in zip(batch, embeddings):
            payload = {
                "character": character,
                "source_type": record.get("source_type", "dialogue"),
                "source_work": record.get("source_work", ""),
                "topic": record.get("topic", []),
                "emotion": record.get("emotion", ""),
                "text": record["text"],
            }

            points.append(models.PointStruct(
                id=str(uuid.uuid4()),
                vector={
                    "dense": emb.dense,
                    "sparse": models.SparseVector(
                        indices=list(emb.sparse.keys()),
                        values=list(emb.sparse.values()),
                    ),
                },
                payload=payload,
            ))

        # 批量 upsert
        await client.upsert(
            collection_name=settings.qdrant_collection,
            points=points,
        )
        print(f"   已入库 {min(i + batch_size, len(all_records))}/{len(all_records)}")

    print(f"✅ {character} 索引构建完成，共 {len(all_records)} 条记录")
