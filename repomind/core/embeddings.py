"""嵌入模型工厂，与聊天模型保持相同的在线/离线切换逻辑。"""
from __future__ import annotations

from langchain_core.embeddings import Embeddings
from langchain_ollama import OllamaEmbeddings
from langchain_openai import OpenAIEmbeddings

from repomind.config import LLMProvider, Settings, settings


def create_embeddings(config: Settings | None = None) -> Embeddings:
    cfg = config or settings

    if cfg.embedding_provider == LLMProvider.ONLINE:
        if not cfg.online_api_key:
            raise RuntimeError(
                "未配置在线模型 API Key，无法使用在线嵌入；"
                "可在 .env 中将 REPOMIND_EMBEDDING_PROVIDER 改为 offline"
            )
        return OpenAIEmbeddings(
            model=cfg.embedding_model,
            api_key=cfg.online_api_key,
            base_url=cfg.online_base_url,
        )

    return OllamaEmbeddings(
        model=cfg.offline_embedding_model,
        base_url=cfg.ollama_base_url,
    )
