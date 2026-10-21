"""聊天模型工厂。

通过统一接口屏蔽在线 API 与本地 Ollama 的差异，
上层只依赖 BaseChatModel，不关心具体后端。
"""
from __future__ import annotations

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI

from repomind.config import LLMProvider, Settings, settings


def create_chat_model(
    temperature: float = 0.2,
    provider: LLMProvider | None = None,
    config: Settings | None = None,
) -> BaseChatModel:
    cfg = config or settings
    provider = provider or cfg.llm_provider

    if provider == LLMProvider.ONLINE:
        if not cfg.online_api_key:
            raise RuntimeError(
                "未配置在线模型 API Key，请在 .env 中设置 REPOMIND_ONLINE_API_KEY"
            )
        return ChatOpenAI(
            model=cfg.online_model,
            api_key=cfg.online_api_key,
            base_url=cfg.online_base_url,
            temperature=temperature,
        )

    return ChatOllama(
        model=cfg.offline_model,
        base_url=cfg.ollama_base_url,
        temperature=temperature,
    )
