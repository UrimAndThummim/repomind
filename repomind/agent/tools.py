"""Agent 可调用的仓库工具集。

通过工厂把仓库根目录注入闭包，工具内部做路径穿越防护，
所有工具均为纯只读操作，不会修改用户仓库。
"""
from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

from langchain_core.tools import BaseTool, tool

from repomind.indexing.loader import IGNORE_DIRS, LANGUAGE_BY_EXT

MAX_MATCHES = 30


def create_repo_tools(repo_path: str | Path) -> list[BaseTool]:
    root = Path(repo_path).expanduser().resolve()

    def _resolve(relative_path: str) -> Path:
        target = (root / relative_path).resolve()
        # 防止 ../../etc/passwd 之类的路径穿越
        if root not in target.parents and target != root:
            raise ValueError("路径超出了仓库根目录")
        return target

    @tool
    def directory_tree(depth: int = 2) -> str:
        """打印仓库的目录结构。参数 depth 控制展开的最大层级，默认为 2。"""
        lines = [root.name + "/"]

        def walk(current: Path, prefix: str, level: int) -> None:
            if level >= depth:
                return
            entries = sorted(
                (p for p in current.iterdir()
                 if p.name not in IGNORE_DIRS and not p.name.startswith(".")),
                key=lambda p: (p.is_file(), p.name),
            )
            for entry in entries:
                lines.append(prefix + ("├── " if entry != entries[-1] else "└── ") + entry.name)
                if entry.is_dir():
                    walk(entry, prefix + ("│   " if entry != entries[-1] else "    "), level + 1)

        walk(root, "", 0)
        return "\n".join(lines)

    @tool
    def code_search(pattern: str, file_extension: str = "") -> str:
        """在仓库源码中按正则表达式搜索。pattern 为 Python 正则；
        file_extension 可指定后缀（如 .py）限定文件类型，留空搜索全部源码文件。
        返回匹配的文件、行号与该行内容。"""
        try:
            regex = re.compile(pattern)
        except re.error as exc:
            return f"正则表达式无效: {exc}"

        matches: list[str] = []
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in IGNORE_DIRS and not d.startswith(".")]
            for filename in filenames:
                path = Path(dirpath) / filename
                if file_extension and path.suffix.lower() != file_extension.lower():
                    continue
                if path.suffix.lower() not in LANGUAGE_BY_EXT:
                    continue
                try:
                    text = path.read_text(encoding="utf-8")
                except (UnicodeDecodeError, OSError):
                    continue
                for lineno, line in enumerate(text.splitlines(), start=1):
                    if regex.search(line):
                        relative = path.relative_to(root).as_posix()
                        matches.append(f"{relative}:{lineno}: {line.strip()[:120]}")
                        if len(matches) >= MAX_MATCHES:
                            matches.append(f"... 结果超过 {MAX_MATCHES} 条，已截断，请缩小搜索范围")
                            return "\n".join(matches)
        return "\n".join(matches) if matches else "没有找到匹配的代码"

    @tool
    def read_file(relative_path: str, max_lines: int = 120) -> str:
        """读取仓库内某个文件的内容。relative_path 为相对于仓库根目录的路径；
        max_lines 为最多返回的行数，默认 120。"""
        try:
            target = _resolve(relative_path)
        except ValueError as exc:
            return str(exc)
        if not target.is_file():
            return f"文件不存在: {relative_path}"
        try:
            lines = target.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            return "该文件是二进制文件，无法读取"
        truncated = lines[:max_lines]
        numbered = [f"{i:>4} | {line}" for i, line in enumerate(truncated, start=1)]
        if len(lines) > max_lines:
            numbered.append(f"... 共 {len(lines)} 行，已截断前 {max_lines} 行")
        return "\n".join(numbered)

    @tool
    def git_log(relative_path: str = "", limit: int = 10) -> str:
        """查看仓库的 Git 提交历史。relative_path 留空查看整个仓库，
        传入文件路径则只看该文件的历史；limit 为返回条数，默认 10。"""
        command = ["git", "log", f"--oneline", "-n", str(limit)]
        if relative_path:
            try:
                target = _resolve(relative_path)
            except ValueError as exc:
                return str(exc)
            command.append("--")
            command.append(target.relative_to(root).as_posix())
        try:
            result = subprocess.run(
                command, cwd=root, capture_output=True, text=True, timeout=15,
            )
        except (subprocess.TimeoutExpired, OSError) as exc:
            return f"git 命令执行失败: {exc}"
        if result.returncode != 0:
            return "当前目录不是 Git 仓库或 git 不可用"
        return result.stdout.strip() or "没有提交记录"

    return [directory_tree, code_search, read_file, git_log]
