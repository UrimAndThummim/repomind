"""命令行入口。

子命令:
    index       构建仓库索引
    ask         单次问答
    chat        多轮对话
    agent       工具调用智能体
    collections 查看已索引的仓库
"""
from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from repomind.agent.assistant import create_repo_agent
from repomind.config import settings
from repomind.core.embeddings import create_embeddings
from repomind.core.llm_factory import create_chat_model
from repomind.indexing.vectorstore import build_index, get_vectorstore, list_collections
from repomind.retrieval.chain import ChatSession, build_rag_chain
from repomind.retrieval.retriever import build_retriever
from repomind.utils.logging import setup_logging

app = typer.Typer(no_args_is_help=True, add_completion=False, help="RepoMind 命令行工具")
console = Console()


def _prepare_chain(repo_path: Path, collection_name: str | None = None):
    # 仓库名来自路径，写入文档元数据；集合名只用于定位向量库，二者可能不同
    repo_name = Path(repo_path).resolve().name
    collection = collection_name or repo_name
    embeddings = create_embeddings()
    vectorstore = get_vectorstore(collection, embeddings, settings)
    retriever = build_retriever(vectorstore, repo_name=repo_name, config=settings)
    llm = create_chat_model(temperature=0.2)
    return build_rag_chain(llm, retriever)


def _render_sources(docs: list) -> None:
    if not docs:
        return
    lines = []
    seen = set()
    for doc in docs:
        meta = doc.metadata
        tag = f"{meta.get('source')}:{meta.get('start_line')}"
        if tag in seen:
            continue
        seen.add(tag)
        symbol = f"（{meta['symbol']}）" if meta.get("symbol") else ""
        lines.append(f"- {tag}-{meta.get('end_line')} {symbol}")
    console.print(Panel("\n".join(lines), title="引用来源", border_style="cyan", expand=False))


@app.command()
def index(
    repo_path: Path = typer.Argument(..., exists=True, help="待索引的本地仓库路径"),
    collection: str = typer.Option("", "--collection", "-c", help="自定义集合名，默认取仓库名"),
) -> None:
    """为本地代码仓库构建向量索引。"""
    setup_logging(settings.log_level)
    with console.status("正在解析文件并构建索引..."):
        count = build_index(repo_path, collection_name=collection or None, config=settings)
    console.print(f"[green]索引完成[/green]，共写入 {count} 个代码块。")


@app.command()
def ask(
    repo_path: Path = typer.Argument(..., exists=True, help="已索引的仓库路径"),
    question: str = typer.Argument(..., help="要提问的问题"),
) -> None:
    """基于仓库内容进行单次问答。"""
    setup_logging(settings.log_level)
    chain = _prepare_chain(repo_path)
    with console.status("检索与生成中..."):
        result = chain.invoke({"question": question, "chat_history": []})
    console.print(Markdown(result["answer"]))
    _render_sources(result["docs"])


@app.command()
def chat(repo_path: Path = typer.Argument(..., exists=True, help="已索引的仓库路径")) -> None:
    """进入多轮对话模式，输入 /clear 清空历史，/exit 退出。"""
    setup_logging(settings.log_level)
    chain = _prepare_chain(repo_path)
    session = ChatSession()
    console.print(f"[bold]RepoMind 多轮对话[/bold]（后端: {settings.llm_provider.value}），"
                  "输入 /exit 退出。")

    while True:
        question = typer.prompt("你")
        if question in ("/exit", "/quit"):
            break
        if question == "/clear":
            session.clear()
            console.print("[yellow]历史已清空[/yellow]")
            continue
        if not question.strip():
            continue
        with console.status("思考中..."):
            result = session.ask(chain, question)
        console.print(Markdown(result["answer"]))
        _render_sources(result["docs"])


@app.command()
def agent(repo_path: Path = typer.Argument(..., exists=True, help="目标仓库路径")) -> None:
    """进入智能体模式，由模型自主调用工具浏览仓库。"""
    setup_logging(settings.log_level)
    llm = create_chat_model(temperature=0.1)
    executor = create_repo_agent(llm, str(repo_path))
    history = []
    console.print("[bold]RepoMind 智能体[/bold]，可让它浏览目录、搜索代码、查看提交历史。")

    while True:
        user_input = typer.prompt("你")
        if user_input in ("/exit", "/quit"):
            break
        if not user_input.strip():
            continue
        with console.status("智能体执行中..."):
            result = executor.invoke({"input": user_input, "chat_history": history})
        history.extend([
            {"role": "user", "content": user_input},
            {"role": "assistant", "content": result["output"]},
        ])
        console.print(Markdown(result["output"]))


@app.command()
def collections() -> None:
    """列出本地已经建立的索引集合。"""
    names = list_collections(settings)
    if not names:
        console.print("暂无索引，先使用 [cyan]repomind index <仓库路径>[/cyan] 构建。")
        return
    for name in names:
        console.print(f"- {name}")


if __name__ == "__main__":
    app()
