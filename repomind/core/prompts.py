"""提示词模板集中管理。"""
from __future__ import annotations

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

# 结合历史对话，把指代性问题改写为可以独立检索的问题
CONDENSE_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "根据聊天历史和用户最新问题，把它改写为一个不依赖上下文、语义完整的检索问题。"
     "只输出改写后的问题，不要回答，不要补充多余内容。"),
    MessagesPlaceholder("chat_history"),
    ("human", "{question}"),
])

# RAG 问答主提示
QA_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "你是 RepoMind，一个代码仓库分析助手。请严格依据下面的代码片段回答问题，"
     "并遵守以下规则：\n"
     "1. 回答中涉及的结论要给出文件路径和行号，格式为 `path:line`；\n"
     "2. 需要贴代码时只引用最相关的片段，不要整段照搬；\n"
     "3. 如果检索片段不足以回答，直接说明“仓库中没有找到足够依据”，不要编造 API 或文件名；\n"
     "4. 回答使用中文，结构清晰，先给结论再展开。\n\n"
     "代码片段：\n{context}"),
    MessagesPlaceholder("chat_history"),
    ("human", "{question}"),
])

# Agent 系统提示
AGENT_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "你是 RepoMind 智能体，可以调用工具浏览本地代码仓库。"
     "先用工具定位文件和代码，再基于真实结果回答；"
     "工具返回的路径均相对于仓库根目录。无法确认的内容不要猜测。"),
    MessagesPlaceholder("chat_history"),
    ("human", "{input}"),
    MessagesPlaceholder("agent_scratchpad"),
])
