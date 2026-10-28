"""仓库加载器测试。"""
from __future__ import annotations

import pytest

from repomind.indexing.loader import load_repository


def test_load_filters_ignored_dirs(sample_repo):
    docs = load_repository(sample_repo)
    sources = [d.metadata["source"] for d in docs]
    # .venv 下的文件必须被跳过
    assert ".venv/ignore.py" not in sources
    assert "src/bank.py" in sources
    assert "README.md" in sources
    assert len(docs) == 2


def test_metadata_fields(sample_repo):
    docs = load_repository(sample_repo)
    py_doc = next(d for d in docs if d.metadata["source"] == "src/bank.py")
    assert py_doc.metadata["language"] == "python"
    assert py_doc.metadata["repo_name"] == "demo-project"
    assert py_doc.metadata["file_size"] > 0


def test_missing_path_raises(tmp_path):
    with pytest.raises(NotADirectoryError):
        load_repository(tmp_path / "not-exist")
