"""代码感知分块。

不同语言使用各自的语法边界（class/def、花括号等）切分，
并为每个块补充起止行号与符号名，方便答案引用来源。
"""
from __future__ import annotations

import re

from langchain_core.documents import Document
from langchain_text_splitters import Language, RecursiveCharacterTextSplitter

from repomind.config import Settings, settings

# 加载器里的语言标识 -> text-splitter 的语言枚举
LANGUAGE_ENUM = {
    "python": Language.PYTHON,
    "java": Language.JAVA,
    "js": Language.JS,
    "ts": Language.TS,
    "go": Language.GO,
    "rust": Language.RUST,
    "c": Language.C,
    "cpp": Language.CPP,
    "csharp": Language.CSHARP,
    "ruby": Language.RUBY,
    "php": Language.PHP,
    "markdown": Language.MARKDOWN,
}

# 各语言“符号定义”的首行正则，用于给块打上函数/类名标签
SYMBOL_PATTERNS = {
    "python": re.compile(r"^\s*(?:async\s+)?(?:def|class)\s+([A-Za-z_]\w*)", re.M),
    "java": re.compile(r"^\s*(?:public|private|protected)?[\w\s<>\[\]]*?\s([A-Za-z_]\w*)\s*\(", re.M),
    "js": re.compile(r"^\s*(?:export\s+)?(?:async\s+)?(?:function|class)\s+([A-Za-z_]\w*)", re.M),
    "ts": re.compile(r"^\s*(?:export\s+)?(?:async\s+)?(?:function|class)\s+([A-Za-z_]\w*)", re.M),
    "go": re.compile(r"^func\s+(?:\([^)]*\)\s*)?([A-Za-z_]\w*)", re.M),
    "rust": re.compile(r"^\s*(?:pub\s+)?(?:fn|struct|enum|trait)\s+([A-Za-z_]\w*)", re.M),
    "c": re.compile(r"^\s*[\w\s*]+\s+([A-Za-z_]\w*)\s*\([^;]*\)\s*\{", re.M),
    "cpp": re.compile(r"^\s*[\w\s:*&~]+\s+([A-Za-z_]\w*)\s*\([^;]*\)\s*\{", re.M),
}


def _build_splitter(language: str, config: Settings) -> RecursiveCharacterTextSplitter:
    lang_enum = LANGUAGE_ENUM.get(language)
    if lang_enum is None:
        return RecursiveCharacterTextSplitter(
            chunk_size=config.chunk_size,
            chunk_overlap=config.chunk_overlap,
        )
    return RecursiveCharacterTextSplitter.from_language(
        language=lang_enum,
        chunk_size=config.chunk_size,
        chunk_overlap=config.chunk_overlap,
    )


def _first_symbol(language: str, chunk: str) -> str | None:
    pattern = SYMBOL_PATTERNS.get(language)
    if pattern is None:
        return None
    match = pattern.search(chunk)
    return match.group(1) if match else None


def split_document(document: Document, config: Settings | None = None) -> list[Document]:
    cfg = config or settings
    language = document.metadata.get("language", "text")
    splitter = _build_splitter(language, config=cfg)

    full_text = document.page_content
    chunks = splitter.split_text(full_text)

    results: list[Document] = []
    cursor = 0
    for index, chunk in enumerate(chunks):
        offset = full_text.find(chunk, cursor)
        if offset == -1:
            # 极端情况下找不到精确子串，退化为从游标位置估算
            offset = cursor
        start_line = full_text.count("\n", 0, offset) + 1
        end_line = start_line + chunk.count("\n")
        cursor = offset + len(chunk)

        metadata = dict(document.metadata)
        metadata.update({
            "start_line": start_line,
            "end_line": end_line,
            "symbol": _first_symbol(language, chunk),
            "chunk_index": index,
        })
        results.append(Document(page_content=chunk, metadata=metadata))

    return results


def split_documents(documents: list[Document], config: Settings | None = None) -> list[Document]:
    chunks: list[Document] = []
    for doc in documents:
        chunks.extend(split_document(doc, config))
    return chunks
