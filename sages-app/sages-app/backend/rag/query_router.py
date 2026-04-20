"""
查询路由 - 判断问题类型，调整检索策略
"""
import re
from rag.schemas import QueryType


# 关键词规则路由（轻量级，无需 LLM）
_RULES = {
    QueryType.CHITCHAT: [
        r"^(你好|嗨|hello|hi|早上好|晚上好|在吗|谢谢|再见|拜拜)",
        r"^(你是谁|你叫什么|你多大|你几岁)",
    ],
    QueryType.QUOTE: [
        r"(原文|出处|哪篇|哪一章|哪一节|原话|说过.*吗)",
        r"(论语|诗经|道德经|弟子规)",
        r"(子曰|诗云|有云)",
    ],
    QueryType.BIOGRAPHY: [
        r"(生平|经历|故事|事迹|传记|什么时候|哪年|哪里人|故乡|出生|去世|死亡)",
        r"(弟子|学生|朋友|家人|父母|妻子|儿子)",
        r"(周游|游历|仕途|做官|流亡|出使)",
    ],
    QueryType.PHILOSOPHY: [
        r"(思想|哲学|理念|观点|主张|学说|主义|理论)",
        r"(仁|义|礼|智|信|忠|孝|悌|勇|恕|中庸|道|德|善|恶|天命)",
        r"(如何.*做人|如何.*处世|人生.*意义|什么是.*道)",
        r"(治国|为政|教育|学习|修身|齐家)",
    ],
}


def classify_query(query: str) -> QueryType:
    """
    基于规则的查询分类

    Args:
        query: 用户查询文本

    Returns:
        查询类型
    """
    query_lower = query.strip().lower()

    for qtype, patterns in _RULES.items():
        for pattern in patterns:
            if re.search(pattern, query_lower):
                return qtype

    return QueryType.GENERAL


def get_retrieval_params(query_type: QueryType) -> dict:
    """
    根据查询类型返回检索参数调整

    Args:
        query_type: 查询类型

    Returns:
        检索参数字典
    """
    params = {
        "top_k": 10,
        "min_score": 0.3,
        "source_type_weights": {
            "dialogue": 1.0,
            "original_work": 1.0,
            "biography": 1.0,
        },
    }

    if query_type == QueryType.CHITCHAT:
        # 闲聊不需要检索
        params["top_k"] = 0
    elif query_type == QueryType.QUOTE:
        # 引用查询优先原著
        params["source_type_weights"] = {
            "original_work": 1.5,
            "dialogue": 1.0,
            "biography": 0.5,
        }
        params["top_k"] = 15
    elif query_type == QueryType.BIOGRAPHY:
        # 生平查询优先传记
        params["source_type_weights"] = {
            "biography": 1.5,
            "dialogue": 1.0,
            "original_work": 0.5,
        }
    elif query_type == QueryType.PHILOSOPHY:
        # 思想查询优先对话和原著
        params["source_type_weights"] = {
            "dialogue": 1.3,
            "original_work": 1.3,
            "biography": 0.8,
        }
        params["top_k"] = 12

    return params
