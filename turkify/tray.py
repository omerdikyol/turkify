from __future__ import annotations

import io
import os
import sys
import threading
import time
from typing import Optional

import pyperclip
from PIL import Image, ImageDraw
import pystray
from pystray import MenuItem as Item, Menu

from .converter import deasciify
from .llm import deasciify_via_llm
from .models import ensure_model
from .watcher import HotkeyWatcher


def _make_icon(paused: bool) -> Image.Image:
    # Simple generated icon: circle with T
    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    bg = (30, 144, 255, 255) if not paused else (128, 128, 128, 255)
    d.ellipse((2, 2, size - 2, size - 2), fill=bg)
    # Draw 'T'
    d.rectangle((28, 18, 36, 48), fill=(255, 255, 255, 255))
    d.rectangle((20, 18, 44, 26), fill=(255, 255, 255, 255))
    return img


class TrayApp:
    def __init__(self, use_llm: bool = False, hotkey: Optional[str] = None):
        self.use_llm = use_llm
        self.hotkey = hotkey or ("<cmd>+<alt>+t" if sys.platform == "darwin" else "<ctrl>+<alt>+t")
        self.icon: Optional[pystray.Icon] = None
        self.watcher: Optional[HotkeyWatcher] = None
        self._icon_lock = threading.Lock()

    def _conv(self, text: str) -> str:
        if self.use_llm:
            out = deasciify_via_llm(
                text,
                auto_download_model=True,
                model_key=os.environ.get("TURKIFY_MODEL_NAME", "qwen2.5-0.5b-instruct-q4_k_m"),
                custom_model_url=os.environ.get("TURKIFY_MODEL_URL"),
            )
            if out:
                return out
        return deasciify(text)

    def _roundtrip(self):
        from pynput.keyboard import Key, Controller
        kb = Controller()
        is_macos = sys.platform == "darwin"
        copy_combo = [Key.cmd if is_macos else Key.ctrl, "c"]
        paste_combo = [Key.cmd if is_macos else Key.ctrl, "v"]

        # Save current clipboard to restore later
        prev_clip = pyperclip.paste()

        # Copy
        for k in copy_combo:
            kb.press(k)
        for k in reversed(copy_combo):
            kb.release(k)
        time.sleep(0.05)

        # Convert clipboard
        orig = pyperclip.paste()
        conv = self._conv(orig)
        pyperclip.copy(conv)

        # Paste
        for k in paste_combo:
            kb.press(k)
        for k in reversed(paste_combo):
            kb.release(k)
        # Restore previous clipboard after paste
        time.sleep(0.12)
        try:
            pyperclip.copy(prev_clip)
        except Exception:
            pass

    def _toggle_pause(self, icon, item):
        if not self.watcher:
            return
        self.watcher.set_paused(not self.watcher.paused)
        self._refresh_icon()

    def _set_heuristic(self, icon, item):
        self.use_llm = False

    def _set_llm(self, icon, item):
        self.use_llm = True
        # Prefetch to avoid surprise delay on first press
        try:
            ensure_model(os.environ.get("TURKIFY_MODEL_NAME", "qwen2.5-0.5b-instruct-q4_k_m"), auto_download=True,
                         custom_url=os.environ.get("TURKIFY_MODEL_URL"))
        except Exception:
            pass

    def _open_ui(self, icon, item):
        import subprocess

        py = sys.executable
        subprocess.Popen([py, "-m", "turkify"])  # opens Tk UI

    def _change_hotkey(self, hotkey: str):
        if self.watcher:
            self.watcher.update_hotkey(hotkey)
        self.hotkey = hotkey

    def _refresh_icon(self):
        with self._icon_lock:
            if self.icon:
                self.icon.icon = _make_icon(paused=self.watcher.paused if self.watcher else False)

    def run(self):
        # Start watcher
        self.watcher = HotkeyWatcher(self.hotkey, self._roundtrip)
        self.watcher.start()

        menu = Menu(
            Item(lambda item: f"Hotkey: {self.hotkey}", lambda icon, item: None, enabled=False),
            Item(lambda item: "Pause" if not (self.watcher and self.watcher.paused) else "Resume", self._toggle_pause),
            Item("Mode", Menu(
                Item("Heuristic", self._set_heuristic, checked=lambda item: not self.use_llm),
                Item("LLM (local)", self._set_llm, checked=lambda item: self.use_llm),
            )),
            Item("Change Hotkey", Menu(
                Item("Default", lambda icon, item: self._change_hotkey("<cmd>+<alt>+t" if sys.platform == "darwin" else "<ctrl>+<alt>+t")),
                Item("Alt+Shift+T", lambda icon, item: self._change_hotkey("<cmd>+<shift>+t" if sys.platform == "darwin" else "<alt>+<shift>+t")),
                Item("Ctrl+Alt+Y", lambda icon, item: self._change_hotkey("<ctrl>+<alt>+y")),
            )),
            Item("Open UI", self._open_ui),
            Item("Quit", lambda icon, item: self._quit()),
        )

        self.icon = pystray.Icon("turkify", _make_icon(False), "Turkify", menu)

        def _run_icon():
            self.icon.run()

        t = threading.Thread(target=_run_icon, daemon=True)
        t.start()

        try:
            while t.is_alive():
                self._refresh_icon()
                time.sleep(0.5)
        finally:
            self._cleanup()

    def _quit(self):
        if self.icon:
            self.icon.stop()

    def _cleanup(self):
        if self.watcher:
            self.watcher.stop()
        self.watcher = None


def main(argv: Optional[list[str]] = None) -> int:
    env_val = os.environ.get("TURKIFY_USE_LLM", "1").strip().lower()
    use_llm = env_val not in ("0", "false", "no", "off", "")
    TrayApp(use_llm=use_llm).run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
