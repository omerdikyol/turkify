from __future__ import annotations

import sys
import threading
import time
from typing import Callable, Optional

from pynput import keyboard


class HotkeyWatcher:
    def __init__(self, hotkey: str, on_trigger: Callable[[], None]):
        self.hotkey = hotkey
        self.on_trigger = on_trigger
        self._listener: Optional[keyboard.Listener] = None
        self._thread: Optional[threading.Thread] = None
        self._stop_ev = threading.Event()
        self._paused = threading.Event()
        self._paused.clear()

    @property
    def paused(self) -> bool:
        return self._paused.is_set()

    def set_paused(self, val: bool) -> None:
        if val:
            self._paused.set()
        else:
            self._paused.clear()

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop_ev.clear()

        combo = keyboard.HotKey.parse(self.hotkey)
        hk = keyboard.HotKey(combo, self._handle)

        def on_press(key):
            try:
                hk.press(key)
            except Exception:
                pass

        def on_release(key):
            try:
                hk.release(key)
            except Exception:
                pass

        def run():
            with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
                self._listener = listener
                while not self._stop_ev.is_set():
                    time.sleep(0.1)
                try:
                    listener.stop()
                except Exception:
                    pass

        self._thread = threading.Thread(target=run, name="turkify-hotkey", daemon=True)
        self._thread.start()

    def _handle(self):
        if self.paused:
            return
        try:
            self.on_trigger()
        except Exception:
            pass

    def stop(self) -> None:
        self._stop_ev.set()
        if self._thread:
            self._thread.join(timeout=1.0)
        self._thread = None
        self._listener = None

    def update_hotkey(self, hotkey: str) -> None:
        self.stop()
        self.hotkey = hotkey
        self.start()

