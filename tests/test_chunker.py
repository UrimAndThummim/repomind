"""代码分块测试。"""
from __future__ import annotations

from repomind.config import Settings
from repomind.indexing.chunker import split_document
from repomind.indexing.loader import load_repository


def _py_document(sample_repo):
    docs = load_repository(sample_repo)
    return next(d for d in docs if d.metadata["language"] == "python")


def test_line_numbers_match_source(sample_repo):
    doc = _py_document(sample_repo)
    chunks = split_document(doc, Settings(_env_file=None))
    source_lines = doc.page_content.splitlines()

    first = chunks[0]
    start = first.metadata["start_line"]
    # 按记录的行号从原文取回对应行，应与块首行一致
    assert source_lines[start - 1].strip() == first.page_content.splitlines()[0].strip()
    assert first.metadata["end_line"] >= start


def test_symbol_extracted(sample_repo):
    doc = _py_document(sample_repo)
    # 调小分块尺寸，让不同符号各自成块
    cfg = Settings(_env_file=None, chunk_size=300, chunk_overlap=50)
    chunks = split_document(doc, cfg)
    symbols = {c.metadata.get("symbol") for c in chunks}
    assert "BankAccount" in symbols
    assert "transfer" in symbols


def test_chunk_index_continuous(sample_repo):
    doc = _py_document(sample_repo)
    chunks = split_document(doc, Settings(_env_file=None))
    assert [c.metadata["chunk_index"] for c in chunks] == list(range(len(chunks)))
