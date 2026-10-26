"""检索器装配：MMR 多样性检索 + 仓库维度过滤。"""
from __future__ import annotations

from langchain_core.retrievers import BaseRetriever
from langchain_core.vectorstores import VectorStore

from repomind.config import Settings, settings


def build_retriever(
    vectorstore: VectorStore,
    repo_name: str | None = None,
    top_k: int | None = None,
    config: Settings | None = None,
) -> BaseRetriever:
    cfg = config or settings
    search_kwargs: dict = {"k": top_k or cfg.top_k}
    if repo_name:
        # 元数据过滤，保证多仓库共存时只检索目标仓库
        search_kwargs["filter"] = {"repo_name": repo_name}

    return vectorstore.as_retriever(
        search_type="mmr",
        search_kwargs=search_kwargs,
    )
