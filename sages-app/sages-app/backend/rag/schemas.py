"""
RAG 数据结构定义
"""
from dataclasses import dataclass, field
from enum import Enum


class QueryType(str, Enum):
    """查询类型分类"""
    CHITCHAT = "chitchat"          # 闲聊/寒暄
    QUOTE = "quote"                # 引用/原文查询
    BIOGRAPHY = "biography"        # 生平事迹
    PHILOSOPHY = "philosophy"      # 思想/哲学
    GENERAL = "general"            # 通用问题


class SourceType(str, Enum):
    """数据来源类型"""
    DIALOGUE = "dialogue"          # 对话数据集
    ORIGINAL_WORK = "original_work"  # 原著文本
    BIOGRAPHY = "biography"        # 传记资料


@dataclass
class RetrievalResult:
    """单条检索结果"""
    text: str
    score: float
    source_type: str
    source_work: str | None = None
    topic: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)


@dataclass
class RAGContext:
    """RAG 检索上下文（传递给 Prompt 组装）"""
    query: str
    query_type: QueryType
    results: list[RetrievalResult]
    character: str  # 人物 slug

    @property
    def formatted_context(self) -> str:
        """格式化为可注入 prompt 的文本"""
        if not self.results:
            return ""
        lines = ["【参考资料】"]
        for i, r in enumerate(self.results, 1):
            source = f"（{r.source_work}）" if r.source_work else ""
            lines.append(f"{i}. {r.text}{source}")
        return "\n".join(lines)
