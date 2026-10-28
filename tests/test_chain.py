"""RAG 链与会话测试（LLM 全部使用假模型）。"""
from __future__ import annotations

from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage

from repomind.config import Settings
from repomind.indexing.vectorstore import build_index, get_vectorstore
from repomind.retrieval.chain import ChatSession, build_rag_chain
from repomind.retrieval.retriever import build_retriever


def _build(sample_repo, embeddings, tmp_path, llm):
    cfg = Settings(_env_file=None, chroma_dir=tmp_path / "store")
    build_index(sample_repo, embeddings=embeddings, config=cfg)
    store = get_vectorstore("demo-project", embeddings, cfg)
    retriever = build_retriever(store, repo_name="demo-project", config=cfg)
    return build_rag_chain(llm, retriever)


def test_chain_returns_answer_and_docs(sample_repo, embeddings, tmp_path, fake_llm):
    chain = _build(sample_repo, embeddings, tmp_path, fake_llm)
    result = chain.invoke({"question": "入口在哪里？", "chat_history": []})

    assert "BankAccount" in result["answer"]
    assert len(result["docs"]) > 0
    assert result["context"]  # 上下文已被格式化


def test_chat_session_accumulates_history(sample_repo, embeddings, tmp_path):
    llm = GenericFakeChatModel(messages=iter([
        AIMessage(content="独立问题：入口在哪里"),  # 第一次：无历史，不触发改写
        AIMessage(content="第一次回答"),
        AIMessage(content="第二次回答"),
    ]))
    chain = _build(sample_repo, embeddings, tmp_path, llm)
    session = ChatSession()

    session.ask(chain, "入口在哪里？")
    session.ask(chain, "那它有哪些方法？")
    assert len(session.history) == 4  # 两轮，每轮 human + ai 各一条
    session.clear()
    assert session.history == []
