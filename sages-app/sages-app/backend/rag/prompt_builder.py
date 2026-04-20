"""
Prompt 组装 - 将 system prompt + RAG 上下文 + 对话历史 + 用户问题组装为最终 prompt
"""
from rag.schemas import RAGContext


def build_prompt(
    system_prompt: str,
    rag_context: RAGContext | None,
    history: list[dict],
    user_message: str,
) -> list[dict]:
    """
    组装最终 prompt（OpenAI Chat Completion 格式）

    Args:
        system_prompt: 人物 system prompt
        rag_context: RAG 检索上下文（可能为 None）
        history: 对话历史 [{"role": "user", "content": "..."}, ...]
        user_message: 当前用户消息

    Returns:
        messages 列表，可直接传给 LLM API
    """
    messages = []

    # 1. System prompt
    system_text = system_prompt
    if rag_context and rag_context.formatted_context:
        system_text += f"\n\n{rag_context.formatted_context}\n\n请参考以上资料回答用户的问题。如果资料中没有相关信息，请基于你自身的知识回答，但不要编造引用。"
    messages.append({"role": "system", "content": system_text})

    # 2. 对话历史
    messages.extend(history)

    # 3. 当前用户消息
    messages.append({"role": "user", "content": user_message})

    return messages


def build_prompt_text(
    system_prompt: str,
    rag_context: RAGContext | None,
    history: list[dict],
    user_message: str,
) -> str:
    """
    组装为纯文本 prompt（用于非 Chat 格式的 LLM）

    Returns:
        完整的 prompt 文本
    """
    parts = []

    # System
    parts.append(f"<system>\n{system_prompt}\n</system>")

    # RAG context
    if rag_context and rag_context.formatted_context:
        parts.append(f"<context>\n{rag_context.formatted_context}\n</context>")

    # History
    if history:
        parts.append("<history>")
        for msg in history:
            role = msg["role"]
            content = msg["content"]
            parts.append(f"{role}: {content}")
        parts.append("</history>")

    # User message
    parts.append(f"<user>\n{user_message}\n</user>")

    parts.append("<assistant>")

    return "\n\n".join(parts)
