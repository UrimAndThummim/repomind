"""向量库构建与检索测试。"""
from __future__ import annotations

from repomind.config import Settings
from repomind.indexing.vectorstore import build_index, get_vectorstore


def test_build_and_search(sample_repo, embeddings, tmp_path):
    cfg = Settings(_env_file=None, chroma_dir=tmp_path / "store")
    count = build_index(sample_repo, embeddings=embeddings, config=cfg)
    assert count > 0

    store = get_vectorstore("demo-project", embeddings, cfg)
    results = store.similarity_search("BankAccount 存款", k=2)
    assert len(results) == 2
    assert all("repo_name" in d.metadata for d in results)


def test_rebuild_does_not_duplicate(sample_repo, embeddings, tmp_path):
    cfg = Settings(_env_file=None, chroma_dir=tmp_path / "store")
    build_index(sample_repo, embeddings=embeddings, config=cfg)
    second_count = build_index(sample_repo, embeddings=embeddings, config=cfg)

    store = get_vectorstore("demo-project", embeddings, cfg)
    assert store._collection.count() == second_count
