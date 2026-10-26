"""RAG 问答链，全部使用 LCEL 原语拼装。

输入: {"question": str, "chat_history": list[BaseMessage]}
输出: {"answer": str, "docs": list[Document], ...}
"""
from __future__ import annotations

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.retrievers import BaseRetriever
from langchain_core.runnables import RunnableBranch, RunnableLambda, RunnablePassthrough

from repomind.core.prompts import CONDENSE_PROMPT, QA_PROMPT


def format_docs(docs: list) -> str:
    """把检索结果整理成带路径行号的上下文文本。"""
    blocks = []
    for doc in docs:
        meta = doc.metadata
        header = f"[{meta.get('source')}:{meta.get('start_line')}-{meta.get('end_line')}"
        if meta.get("symbol"):
            header += f"，符号: {meta['symbol']}"
        header += "]"
        blocks.append(f"{header}\n{doc.page_content}")
    return "\n\n".join(blocks)


def build_rag_chain(llm: BaseChatModel, retriever: BaseRetriever):
    # 有历史时先把指代性问题改写成独立问题，没有历史时直接透传
    condense_chain = CONDENSE_PROMPT | llm | StrOutputParser()
    standalone_question = RunnableBranch(
        (lambda x: bool(x.get("chat_history")), condense_chain),
        RunnableLambda(lambda x: x["question"]),
    )

    chain = (
        RunnablePassthrough.assign(question=standalone_question)
        .assign(docs=lambda x: retriever.invoke(x["question"]))
        .assign(context=lambda x: format_docs(x["docs"]))
        .assign(answer=QA_PROMPT | llm | StrOutputParser())
    )
    return chain


class ChatSession:
    """维护一轮会话内的对话历史，供 CLI 和 Web 端复用。"""

    def __init__(self) -> None:
        self.history: list[BaseMessage] = []

    def ask(self, chain, question: str) -> dict:
        result = chain.invoke({
            "question": question,
            "chat_history": self.history,
        })
        self.history.append(HumanMessage(content=question))
        self.history.append(AIMessage(content=result["answer"]))
        return result

    def clear(self) -> None:
        self.history.clear()
