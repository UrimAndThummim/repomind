"""Streamlit Web 界面：streamlit run repomind/app.py"""
from __future__ import annotations

import streamlit as st

from repomind.agent.assistant import create_repo_agent
from repomind.config import settings
from repomind.core.embeddings import create_embeddings
from repomind.core.llm_factory import create_chat_model
from repomind.indexing.vectorstore import build_index, get_vectorstore
from repomind.retrieval.chain import ChatSession, build_rag_chain
from repomind.retrieval.retriever import build_retriever

st.set_page_config(page_title="RepoMind", page_icon="🔍", layout="wide")


def _load_chain(repo_path: str, collection: str, repo_name: str):
    embeddings = create_embeddings()
    vectorstore = get_vectorstore(collection, embeddings, settings)
    # 过滤条件必须使用文档元数据中的真实仓库名，而非集合名
    retriever = build_retriever(vectorstore, repo_name=repo_name, config=settings)
    llm = create_chat_model(temperature=0.2)
    return build_rag_chain(llm, retriever)


with st.sidebar:
    st.title("RepoMind")
    st.caption(f"模型后端：{settings.llm_provider.value} · "
               f"{'本地 Ollama' if settings.is_offline else settings.online_model}")

    repo_path = st.text_input("本地仓库路径", placeholder="/home/user/my-project")
    collection = st.text_input("索引集合名", placeholder="留空则使用仓库名")

    col1, col2 = st.columns(2)
    if col1.button("构建索引", use_container_width=True):
        if not repo_path:
            st.error("请先填写仓库路径")
        else:
            with st.spinner("正在构建索引..."):
                count = build_index(repo_path, collection_name=collection or None,
                                    config=settings)
            st.success(f"索引完成，共 {count} 个代码块")

    if col2.button("加载仓库", use_container_width=True):
        if not repo_path:
            st.error("请先填写仓库路径")
        else:
            name = collection or repo_path.rstrip("/").split("/")[-1]
            repo_name = repo_path.rstrip("/").split("/")[-1]
            st.session_state.chain = _load_chain(repo_path, name, repo_name)
            st.session_state.repo_name = repo_name
            st.session_state.session = ChatSession()
            st.session_state.messages = []
            st.success("仓库已加载，可以开始提问")

    if st.button("清空对话", use_container_width=True):
        if "session" in st.session_state:
            st.session_state.session.clear()
        st.session_state.messages = []

    st.divider()
    st.markdown("**提问示例**")
    st.caption("这个项目的入口在哪里？\n\n哪个函数负责建立数据库连接？\n\n模块之间的调用关系是什么？")

st.header("代码仓库智能问答")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message.get("sources"):
            with st.expander("引用来源"):
                st.code("\n".join(message["sources"]), language="text")

if question := st.chat_input("针对已加载的仓库提问..."):
    if "chain" not in st.session_state:
        st.error("请先在左侧填写仓库路径并点击「加载仓库」")
    else:
        st.chat_message("user").markdown(question)
        st.session_state.messages.append({"role": "user", "content": question})

        with st.chat_message("assistant"):
            with st.spinner("检索与生成中..."):
                result = st.session_state.session.ask(st.session_state.chain, question)
            st.markdown(result["answer"])

            sources = []
            for doc in result["docs"]:
                meta = doc.metadata
                sources.append(
                    f"{meta.get('source')}:{meta.get('start_line')}-{meta.get('end_line')}"
                )
            with st.expander("引用来源"):
                st.code("\n".join(dict.fromkeys(sources)), language="text")

        st.session_state.messages.append(
            {"role": "assistant", "content": result["answer"], "sources": sources}
        )
