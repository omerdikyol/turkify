from __future__ import annotations

import argparse
import sys
import time

import pyperclip

from .converter import deasciify
from .llm import deasciify_via_llm


def _convert_clipboard(conv_func, in_place: bool = True) -> str:
    orig = pyperclip.paste()
    conv = conv_func(orig)
    if in_place:
        pyperclip.copy(conv)
    return conv


def _watch_hotkey(hotkey: str, conv_func, restore_clipboard: bool = True) -> None:
    from pynput import keyboard
    from pynput.keyboard import Key, Controller

    is_macos = sys.platform == "darwin"
    copy_combo = [Key.cmd if is_macos else Key.ctrl, "c"]
    paste_combo = [Key.cmd if is_macos else Key.ctrl, "v"]

    kb = Controller()

    def do_roundtrip():
        import pyperclip as _pc
        # Save previous clipboard so we can restore it after paste
        prev_clip = _pc.paste() if restore_clipboard else None
        # Copy
        for k in copy_combo:
            kb.press(k)
        for k in reversed(copy_combo):
            kb.release(k)
        time.sleep(0.05)

        # Convert
        converted = _convert_clipboard(conv_func, in_place=True)

        # Paste
        for k in paste_combo:
            kb.press(k)
        for k in reversed(paste_combo):
            kb.release(k)
        if restore_clipboard and prev_clip is not None:
            # Allow the target app to consume the clipboard before restoring
            time.sleep(0.12)
            try:
                _pc.copy(prev_clip)
            except Exception:
                pass

    print(f"Watching global hotkey: {hotkey}. Press ESC to quit.")

    combo = keyboard.HotKey.parse(hotkey)
    hotkey_handler = keyboard.HotKey(combo, do_roundtrip)

    def on_press(key):
        try:
            hotkey_handler.press(key)
        except Exception:
            pass
        if key == keyboard.Key.esc:
            return False

    def on_release(key):
        try:
            hotkey_handler.release(key)
        except Exception:
            pass

    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="turkify", description="Turkish deasciifier (LLM by default)")
    p.add_argument("--text", help="Convert given text and print result")
    p.add_argument("--clipboard", action="store_true", help="Convert clipboard in place")
    p.add_argument(
        "--watch-hotkey",
        nargs="?",
        const="<ctrl>+<alt>+t",
        help="Watch global hotkey (default: <ctrl>+<alt>+t or use e.g. <cmd>+<alt>+t on macOS)",
    )
    p.add_argument("--ui", action="store_true", help="Launch Tk UI")
    # LLM options
    p.add_argument("--llm", action="store_true", help="Use local LLM (default) if available (Ollama or llama.cpp)")
    p.add_argument("--heuristic", action="store_true", help="Force heuristic/rule-based mode (disable LLM)")
    p.add_argument("--ollama-model", help="Ollama model name (e.g. 'tinyllama:latest')")
    p.add_argument("--ollama-host", default="http://localhost:11434", help="Ollama host URL")
    p.add_argument("--llama-model", help="Path to GGUF model for llama.cpp")
    p.add_argument("--auto-download-model", action="store_true", help="Auto-download a small GGUF to cache if missing (default with LLM)")
    p.add_argument("--no-auto-download", action="store_true", help="Disable auto-download even if --llm is set")
    p.add_argument(
        "--model-name",
        default="qwen2.5-0.5b-instruct-q4_k_m",
        help="Model key for auto-download (e.g., qwen2.5-0.5b-instruct-q4_k_m or phi-2-q4_k_m)",
    )
    p.add_argument("--model-url", help="Custom GGUF URL to download if provided")
    # Autostart management
    p.add_argument(
        "--install-autostart",
        nargs="?",
        const="llm",
        choices=["llm", "heuristic", "tray-llm", "tray-heuristic"],
        help="Install autostart (default: llm). Also supports tray-llm and tray-heuristic",
    )
    p.add_argument("--autostart-hotkey", help="Override hotkey when installing autostart")
    p.add_argument("--uninstall-autostart", action="store_true", help="Remove autostart entry")
    # Clipboard behavior
    p.add_argument("--no-restore-clipboard", action="store_true", help="Do not restore previous clipboard contents after paste")
    return p


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    args = build_parser().parse_args(argv)

    # Handle autostart commands early
    if args.install_autostart or args.uninstall_autostart:
        from .autostart import install_autostart, uninstall_autostart

        if args.uninstall_autostart:
            removed = uninstall_autostart()
            print("Autostart removed" if removed else "No autostart entry found")
            return 0
        # Install
        mode = args.install_autostart or "llm"
        path = install_autostart(mode=mode, hotkey=args.autostart_hotkey)
        print(f"Autostart installed: {path}")
        return 0

    # Optionally prepare local llama.cpp model on startup (first run download)
    def _prepare_llm():
        llm_enabled = (not args.heuristic) or args.llm or args.ollama_model or args.llama_model
        if not llm_enabled:
            return None
        # If Ollama is specified, nothing to prepare locally
        if args.ollama_model:
            return None
        # Decide auto-download default: enabled when using --llm unless explicitly disabled
        auto_download = args.auto_download_model or ((not args.no_auto_download) and (not args.llama_model))
        if auto_download and not args.llama_model:
            try:
                from .models import ensure_model

                path = ensure_model(args.model_name, auto_download=True, custom_url=args.model_url)
                if path:
                    # Stash back so conversion uses it
                    args.llama_model = path
            except Exception:
                pass

    _prepare_llm()

    # Choose conversion function
    def _conv(text: str) -> str:
        llm_enabled = (not args.heuristic) or args.llm or args.ollama_model or args.llama_model
        if llm_enabled:
            out = deasciify_via_llm(
                text,
                backend=None,
                ollama_model=args.ollama_model,
                ollama_host=args.ollama_host,
                llama_model=args.llama_model,
                auto_download_model=(args.auto_download_model or ((not args.no_auto_download) and (not args.llama_model))),
                model_key=args.model_name,
                custom_model_url=args.model_url,
            )
            if out:
                return out
        return deasciify(text)

    if args.ui:
        from .ui import run

        run()
        return 0

    if args.watch_hotkey is not None:
        hotkey = args.watch_hotkey
        # On mac suggest cmd
        if sys.platform == "darwin" and "<cmd>" not in hotkey:
            hotkey = "<cmd>+<alt>+t"
        _watch_hotkey(hotkey, _conv, restore_clipboard=(not args.no_restore_clipboard))
        return 0

    if args.text:
        print(_conv(args.text))
        return 0

    if args.clipboard:
        converted = _convert_clipboard(_conv, in_place=True)
        print(converted)
        return 0

    # Default: print help
    build_parser().print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
