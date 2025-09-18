from __future__ import annotations

import sys

from .cli import main


def watch_main() -> int:
    # Start watcher with default hotkey (LLM by default unless --heuristic used)
    args = ["--watch-hotkey"]
    return main(args)


def watch_llm_main() -> int:
    # Back-compat alias (LLM is default now)
    args = ["--watch-hotkey"]
    return main(args)


if __name__ == "__main__":
    raise SystemExit(watch_main())
