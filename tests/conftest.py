"""pytest 公共夹具：确定性嵌入、假模型、临时示例仓库。"""
from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path

import pytest
from langchain_core.embeddings import Embeddings
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage


class HashEmbeddings(Embeddings):
    """基于哈希的确定性嵌入，不依赖任何网络服务。"""

    dimension = 16

    def _embed(self, text: str) -> list[float]:
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        return [b / 255.0 - 0.5 for b in digest[: self.dimension]]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._embed(t) for t in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._embed(text)


SAMPLE_PY = '''"""示例银行账户模块。"""


class BankAccount:
    def __init__(self, owner: str, balance: float = 0.0):
        self.owner = owner
        self.balance = balance

    def deposit(self, amount: float) -> None:
        if amount <= 0:
            raise ValueError("存款金额必须为正数")
        self.balance += amount

    def withdraw(self, amount: float) -> None:
        if amount > self.balance:
            raise ValueError("余额不足")
        self.balance -= amount


def transfer(src: BankAccount, dst: BankAccount, amount: float) -> None:
    src.withdraw(amount)
    dst.deposit(amount)
'''

SAMPLE_MD = """# Demo 项目

一个用于测试的小项目，入口模块是 `bank.py`。
"""


@pytest.fixture
def sample_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "demo-project"
    src = repo / "src"
    src.mkdir(parents=True)
    (src / "bank.py").write_text(SAMPLE_PY, encoding="utf-8")
    (repo / "README.md").write_text(SAMPLE_MD, encoding="utf-8")
    # 构建依赖目录，验证加载器会跳过它
    (repo / ".venv").mkdir()
    (repo / ".venv" / "ignore.py").write_text("SECRET = 1", encoding="utf-8")

    subprocess.run(["git", "init"], cwd=repo, capture_output=True, check=True)
    subprocess.run(
        ["git", "-c", "user.name=tester", "-c", "user.email=tester@example.com",
         "commit", "--allow-empty", "-m", "initial commit"],
        cwd=repo, capture_output=True, check=True,
    )
    return repo


@pytest.fixture
def embeddings() -> HashEmbeddings:
    return HashEmbeddings()


@pytest.fixture
def fake_llm() -> GenericFakeChatModel:
    return GenericFakeChatModel(messages=iter([
        AIMessage(content="入口在 src/bank.py，核心类是 BankAccount。"),
    ]))
