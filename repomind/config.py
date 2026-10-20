"""全局配置。

配置优先级：环境变量 / .env 文件 > 代码内默认值，
所有环境变量统一使用 REPOMIND_ 前缀。
"""
from __future__ import annotations

from enum import Enum
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class LLMProvider(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_prefix="REPOMIND_",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # 大模型后端
    llm_provider: LLMProvider = LLMProvider.ONLINE
    online_model: str = "deepseek-chat"
    online_api_key: str = ""
    online_base_url: str = "https://api.deepseek.com/v1"

    # 本地 Ollama
    offline_model: str = "qwen2.5:7b"
    ollama_base_url: str = "http://localhost:11434"

    # 嵌入模型
    embedding_provider: LLMProvider = LLMProvider.ONLINE
    embedding_model: str = "text-embedding-3-small"
    offline_embedding_model: str = "nomic-embed-text"

    # 索引与检索
    chroma_dir: Path = PROJECT_ROOT / ".vectorstore"
    chunk_size: int = Field(default=1200, gt=100)
    chunk_overlap: int = Field(default=150, ge=0)
    top_k: int = Field(default=6, ge=1)

    log_level: str = "INFO"

    @field_validator("chroma_dir", mode="before")
    @classmethod
    def _expand_path(cls, value: str | Path) -> Path:
        return Path(value).expanduser().resolve()

    @property
    def is_offline(self) -> bool:
        return self.llm_provider == LLMProvider.OFFLINE


settings = Settings()
