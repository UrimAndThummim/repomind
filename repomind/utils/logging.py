"""日志初始化，统一各模块的输出格式。"""
from __future__ import annotations

import logging

_CONFIGURED = False


def setup_logging(level: str = "INFO") -> None:
    global _CONFIGURED
    if _CONFIGURED:
        return

    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter("%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
                          datefmt="%H:%M:%S")
    )
    root = logging.getLogger("repomind")
    root.setLevel(level.upper())
    root.addHandler(handler)
    root.propagate = False
    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(f"repomind.{name}")
