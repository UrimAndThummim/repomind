"""仓库文件加载：遍历目录、过滤无关文件、产出 LangChain Document。"""
from __future__ import annotations

import os
from pathlib import Path

from langchain_core.documents import Document

from repomind.utils.logging import get_logger

logger = get_logger("loader")

# 依赖目录、构建产物和 IDE 配置不纳入索引
IGNORE_DIRS = {
    ".git", ".venv", "venv", "env", "node_modules", "__pycache__",
    ".idea", ".vscode", "dist", "build", ".vectorstore", ".pytest_cache",
    "target", ".mvn",
}

# 扩展名 -> 语言标识，同时决定分块策略
LANGUAGE_BY_EXT = {
    ".py": "python",
    ".java": "java",
    ".js": "js",
    ".jsx": "js",
    ".ts": "ts",
    ".tsx": "ts",
    ".go": "go",
    ".rs": "rust",
    ".c": "c",
    ".h": "c",
    ".cpp": "cpp",
    ".cc": "cpp",
    ".hpp": "cpp",
    ".cs": "csharp",
    ".rb": "ruby",
    ".php": "php",
    ".md": "markdown",
    ".txt": "text",
    ".yml": "yaml",
    ".yaml": "yaml",
    ".toml": "ini",
    ".json": "json",
}

MAX_FILE_SIZE = 300 * 1024  # 单文件超过 300KB 跳过，避免生成数据/压缩包污染索引


def _read_text(path: Path) -> str | None:
    try:
        if path.stat().st_size > MAX_FILE_SIZE:
            logger.debug("跳过超大文件 %s", path)
            return None
        with open(path, "r", encoding="utf-8", errors="strict") as f:
            return f.read()
    except (UnicodeDecodeError, OSError):
        # 二进制文件或无权限文件直接跳过
        return None


def load_repository(repo_path: str | Path) -> list[Document]:
    root = Path(repo_path).expanduser().resolve()
    if not root.is_dir():
        raise NotADirectoryError(f"仓库路径不存在或不是目录: {root}")

    documents: list[Document] = []
    for dirpath, dirnames, filenames in os.walk(root):
        # 原地修改 dirnames，让 os.walk 不再进入忽略目录
        dirnames[:] = [
            d for d in dirnames
            if d not in IGNORE_DIRS and not d.startswith(".") and not d.endswith(".egg-info")
        ]

        for filename in filenames:
            file_path = Path(dirpath) / filename
            ext = file_path.suffix.lower()
            language = LANGUAGE_BY_EXT.get(ext)
            if language is None:
                continue

            content = _read_text(file_path)
            if content is None or not content.strip():
                continue

            relative = file_path.relative_to(root).as_posix()
            documents.append(
                Document(
                    page_content=content,
                    metadata={
                        "repo_name": root.name,
                        "source": relative,
                        "language": language,
                        "file_size": file_path.stat().st_size,
                    },
                )
            )

    logger.info("在 %s 中加载了 %d 个文件", root.name, len(documents))
    return documents
