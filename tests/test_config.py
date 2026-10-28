"""配置模块测试。"""
from __future__ import annotations

from repomind.config import LLMProvider, Settings


def test_default_values():
    cfg = Settings(_env_file=None)
    assert cfg.top_k == 6
    assert cfg.llm_provider == LLMProvider.ONLINE
    assert cfg.chunk_size > cfg.chunk_overlap


def test_env_override(monkeypatch):
    monkeypatch.setenv("REPOMIND_TOP_K", "3")
    monkeypatch.setenv("REPOMIND_LLM_PROVIDER", "offline")
    cfg = Settings(_env_file=None)
    assert cfg.top_k == 3
    assert cfg.llm_provider == LLMProvider.OFFLINE
    assert cfg.is_offline
