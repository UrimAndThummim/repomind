"""Chroma 向量库管理：索引构建与检索入口。"""
from __future__ import annotations

from pathlib import Path

import chromadb
from langchain_chroma import Chroma
from langchain_core.embeddings import Embeddings

from repomind.config import Settings, settings
from repomind.indexing.chunker import split_documents
from repomind.indexing.loader import load_repository
from repomind.utils.logging import get_logger

logger = get_logger("vectorstore")


def _persist_path(collection_name: str, config: Settings) -> Path:
    return config.chroma_dir / collection_name


def get_vectorstore(
    collection_name: str,
    embeddings: Embeddings,
    config: Settings | None = None,
) -> Chroma:
    cfg = config or settings
    persist_path = _persist_path(collection_name, cfg)
    persist_path.mkdir(parents=True, exist_ok=True)

    client = chromadb.PersistentClient(path=str(persist_path))
    return Chroma(
        collection_name=collection_name,
        embedding_function=embeddings,
        client=client,
    )


def build_index(
    repo_path: str | Path,
    collection_name: str | None = None,
    embeddings: Embeddings | None = None,
    config: Settings | None = None,
) -> int:
    """加载仓库 -> 分块 -> 写入向量库，返回写入的块数。"""
    cfg = config or settings
    if embeddings is None:
        from repomind.core.embeddings import create_embeddings
        embeddings = create_embeddings(cfg)

    documents = load_repository(repo_path)
    if not documents:
        raise RuntimeError(f"仓库 {repo_path} 中没有可索引的受支持文件")

    collection_name = collection_name or documents[0].metadata["repo_name"]
    chunks = split_documents(documents, cfg)

    # 重建索引：先清掉同名 collection，避免重复写入
    persist_path = _persist_path(collection_name, cfg)
    persist_path.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(str(persist_path))
    try:
        client.delete_collection(collection_name)
    except Exception:
        pass

    vectorstore = Chroma(
        collection_name=collection_name,
        embedding_function=embeddings,
        client=client,
    )
    vectorstore.add_documents(chunks)
    logger.info("集合 %s 写入 %d 个代码块", collection_name, len(chunks))
    return len(chunks)


def list_collections(config: Settings | None = None) -> list[str]:
    cfg = config or settings
    if not cfg.chroma_dir.exists():
        return []
    return [p.name for p in cfg.chroma_dir.iterdir() if p.is_dir()]
