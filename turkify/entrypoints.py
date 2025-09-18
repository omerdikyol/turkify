from __future__ import annotations

import sys

from .cli import main


def watch_main() -> int:
    # Start watcher with default hotkey and heuristic converter
    args = ["--watch-hotkey"]
    return main(args)


def watch_llm_main() -> int:
    # Start watcher with default hotkey and LLM with auto-download on first use
    args = ["--llm", "--watch-hotkey"]
    return main(args)


if __name__ == "__main__":
    raise SystemExit(watch_main())

