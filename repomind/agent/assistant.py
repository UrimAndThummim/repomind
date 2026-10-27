"""智能体装配：工具调用 Agent + 执行器。"""
from __future__ import annotations

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.tools import BaseTool
from langchain_classic.agents import AgentExecutor, create_tool_calling_agent

from repomind.agent.tools import create_repo_tools
from repomind.core.prompts import AGENT_PROMPT


def build_agent_executor(llm: BaseChatModel, tools: list[BaseTool]) -> AgentExecutor:
    agent = create_tool_calling_agent(llm, tools, AGENT_PROMPT)
    return AgentExecutor(
        agent=agent,
        tools=tools,
        max_iterations=8,
        handle_parsing_errors=True,
        verbose=False,
    )


def create_repo_agent(llm: BaseChatModel, repo_path: str) -> AgentExecutor:
    tools = create_repo_tools(repo_path)
    return build_agent_executor(llm, tools)
