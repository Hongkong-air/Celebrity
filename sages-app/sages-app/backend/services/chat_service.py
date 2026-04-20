"""
对话编排服务 - 串联检索 → 组装 → 推理 → 返回的完整流程
"""
import uuid
from typing import AsyncGenerator, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from models.conversation import Conversation
from models.message import Message
from rag.query_router import classify_query, get_retrieval_params
from rag.retriever import HybridRetriever, retriever
from rag.reranker import rerank
from rag.prompt_builder import build_prompt
from rag.schemas import RAGContext, QueryType
from services.llm_service import llm_service
from services.character_service import CharacterService
from services.conversation_service import ConversationService


class ChatService:
    """对话编排核心"""

    def __init__(self):
        self.retriever = retriever

    async def chat(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        character_id: uuid.UUID,
        message: str,
        conversation_id: Optional[uuid.UUID] = None,
    ) -> AsyncGenerator[dict, None]:
        """
        完整对话流程（流式返回）

        流程:
        1. 获取人物配置
        2. 获取或创建会话
        3. RAG 检索
        4. 组装 Prompt
        5. LLM 推理（流式）
        6. 持久化消息

        Yields:
            {"type": "token", "content": "..."} 或 {"type": "done", ...}
        """
        # 1. 获取人物配置
        character = await CharacterService.get_by_id(db, character_id)
        if not character:
            yield {"type": "error", "content": "人物不存在"}
            return

        # 2. 获取或创建会话
        if conversation_id:
            conversation = await ConversationService.get_by_id(
                db, conversation_id, user_id=user_id
            )
            if not conversation:
                yield {"type": "error", "content": "会话不存在"}
                return
        else:
            conversation = await ConversationService.create(
                db, user_id=user_id, character_id=character_id
            )

        # 保存用户消息
        user_msg = await ConversationService.add_message(
            db, conversation.id, role="user", content=message
        )

        # 3. RAG 检索
        query_type = classify_query(message)
        rag_context = None

        if query_type != QueryType.CHITCHAT:
            try:
                # 获取对话历史（最近 10 轮）
                history_msgs = await ConversationService.get_messages(
                    db, conversation.id, limit=20
                )
                history = [
                    {"role": m.role, "content": m.content}
                    for m in history_msgs[:-1]  # 排除刚添加的用户消息
                ]

                # 检索
                params = get_retrieval_params(query_type)
                if params["top_k"] > 0:
                    from rag.encoder import embedding_client

                    query_emb = await embedding_client.embed_single(message)
                    results = await self.retriever.retrieve(
                        query_dense=query_emb.dense,
                        query_sparse=query_emb.sparse,
                        character=character.slug,
                        top_k=params["top_k"],
                    )

                    # 重排序
                    if results:
                        results = await rerank(message, results, top_k=3)
                        rag_context = RAGContext(
                            query=message,
                            query_type=query_type,
                            results=results,
                            character=character.slug,
                        )
            except Exception as e:
                # RAG 失败不阻塞对话，仅记录
                import logging
                logging.warning(f"RAG 检索失败，跳过: {e}")
                history = []
        else:
            history = []

        # 4. 组装 Prompt
        messages = build_prompt(
            system_prompt=character.system_prompt,
            rag_context=rag_context,
            history=history,
            user_message=message,
        )

        # 5. LLM 推理（流式）
        full_response = ""
        try:
            async for chunk in llm_service.stream(
                messages=messages,
                lora_name=character.lora_name,
            ):
                full_response += chunk
                yield {"type": "token", "content": chunk}
        except Exception as e:
            yield {"type": "error", "content": f"推理服务暂时不可用: {e}"}
            return

        # 6. 持久化助手消息
        rag_sources = (
            [{"text": r.text, "source": r.source_work} for r in rag_context.results]
            if rag_context
            else []
        )
        assistant_msg = await ConversationService.add_message(
            db,
            conversation.id,
            role="assistant",
            content=full_response,
            rag_sources=rag_sources,
        )

        # 7. 完成
        yield {
            "type": "done",
            "conversation_id": str(conversation.id),
            "message_id": str(assistant_msg.id),
        }

    async def chat_sync(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        character_id: uuid.UUID,
        message: str,
        conversation_id: Optional[uuid.UUID] = None,
    ) -> dict:
        """
        非流式对话（收集所有 token 后返回）

        Returns:
            {"content": "...", "conversation_id": "...", "message_id": "..."}
        """
        full_content = ""
        result = None
        async for chunk in self.chat(
            db, user_id, character_id, message, conversation_id
        ):
            if chunk["type"] == "token":
                full_content += chunk["content"]
            elif chunk["type"] == "done":
                result = chunk
            elif chunk["type"] == "error":
                raise RuntimeError(chunk["content"])

        return {
            "content": full_content,
            "conversation_id": result["conversation_id"],
            "message_id": result["message_id"],
        }


# 全局单例
chat_service = ChatService()
