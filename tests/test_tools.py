"""Agent 工具测试。"""
from __future__ import annotations

from repomind.agent.tools import create_repo_tools


def _tool(tools, name):
    return next(t for t in tools if t.name == name)


def test_directory_tree(sample_repo):
    tools = create_repo_tools(sample_repo)
    output = _tool(tools, "directory_tree").invoke({"depth": 2})
    assert "demo-project" in output
    assert "src" in output


def test_code_search(sample_repo):
    tools = create_repo_tools(sample_repo)
    output = _tool(tools, "code_search").invoke({"pattern": r"def\s+deposit"})
    assert "bank.py" in output
    assert "deposit" in output


def test_code_search_invalid_regex(sample_repo):
    tools = create_repo_tools(sample_repo)
    output = _tool(tools, "code_search").invoke({"pattern": "("})
    assert "正则表达式无效" in output


def test_read_file(sample_repo):
    tools = create_repo_tools(sample_repo)
    output = _tool(tools, "read_file").invoke({"relative_path": "src/bank.py"})
    assert "BankAccount" in output


def test_read_file_blocks_path_escape(sample_repo):
    tools = create_repo_tools(sample_repo)
    output = _tool(tools, "read_file").invoke({"relative_path": "../../etc/passwd"})
    assert "超出了仓库根目录" in output


def test_git_log(sample_repo):
    tools = create_repo_tools(sample_repo)
    output = _tool(tools, "git_log").invoke({})
    assert "initial commit" in output
