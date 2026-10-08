# Turkify

Restore Turkish characters in text typed with an English keyboard. Select text and use a hotkey, convert a string in the terminal, or paste it into the small desktop UI.

- Global hotkey: select text → press hotkey → it’s corrected in place
- Default uses a tiny local LLM (auto‑downloaded once, cached)
- Also includes a tray app and a minimal paste/convert UI

Works on macOS, Windows, and Linux.

## Features
- LLM by default: llama.cpp backend with a small GGUF model (~220–260MB).
- Heuristic fallback: conservative rules; supports `turkish-deasciifier` if installed.
- Tray: Pause/Resume, LLM/Heuristic toggle, Change Hotkey, Open UI, Quit.
- If the LLM backend isn’t available, Turkify falls back automatically.

## Install
- Requires Python 3.8+.
- macOS/Linux: `python3 -m pip install .`
- Windows: `py -m pip install .`

## Quick Start
- Start hotkey watcher (LLM, auto‑download on first use):
  - macOS: `turkify --watch-hotkey "<cmd>+<alt>+t"`
  - Windows/Linux: `turkify --watch-hotkey` (defaults to Ctrl+Alt+T)
- One‑command shortcuts:
  - `turkify-watch` (LLM default)
  - `turkify-tray` (tray icon)
- UI: `python -m turkify`
- Restore clipboard: enabled by default. To keep converted text on the clipboard, add `--no-restore-clipboard` when running the watcher.

## Examples
- Convert text via CLI:
  - `turkify --text "cok guzel sarki cunku ogrenci simdi"`
  - `turkify --text "Istanbul icin simdi en iyi zaman"`
- Force heuristic mode (no LLM):
  - `turkify --heuristic --text "bugun hava cok guzel"`
  - Watcher without restoring clipboard: `turkify --heuristic --watch-hotkey --no-restore-clipboard`
- Use a specific local GGUF model:
  - `turkify --llama-model /path/to/model.gguf --text "ornek cumle"`
- Pick a preset or URL (auto‑download):
  - `turkify --model-name qwen2.5-0.5b-instruct-q4_k_m --text "sarkilar guzeldir"`
  - `turkify --model-url https://.../model.gguf --text "sarki soyle"`

## Tray App
- Run: `turkify-tray`
- Menu: Pause/Resume, Mode (LLM/Heuristic), Change Hotkey, Open UI, Quit
- macOS: if tray doesn’t show, install `pyobjc` (`pip install pyobjc`).

## LLM Model & Cache
- Default model: Qwen2.5‑0.5B‑Instruct Q4_K_M (~220–260MB), downloaded once.
- Cache locations:
  - macOS: `~/Library/Caches/turkify/models`
  - Linux: `~/.cache/turkify/models`
  - Windows: `%LOCALAPPDATA%\turkify\models`
- Disable download: add `--no-auto-download` or use `--heuristic`.

## Heuristic Mode
- Disable LLM: `--heuristic`.
- Optional library for better rules: `python -m pip install turkish-deasciifier`.

## Auto‑start on Login
- LLM watcher: `turkify --install-autostart`
- Heuristic watcher: `turkify --install-autostart heuristic`
- Tray autostart: `turkify --install-autostart tray-llm` (or `tray-heuristic`)
- Custom hotkey (watcher): `turkify --install-autostart llm --autostart-hotkey "<cmd>+<alt>+t"`
- Remove: `turkify --uninstall-autostart`
- Under the hood:
  - macOS: `~/Library/LaunchAgents/com.turkify.watch.plist`
  - Windows: Startup folder BAT file
  - Linux: `~/.config/autostart/turkify.desktop`

## Packaging (optional)
- Single‑file executables (PyInstaller):
  - `pip install -e .[llm] pyinstaller`
  - CLI: `make package-cli` → `dist/turkify`
  - UI: `make package-ui` → `dist/turkify-ui`
- macOS may require codesign; Linux binaries depend on glibc; build on target OS for best results.

## Permissions & Tips
- macOS: grant Accessibility permission for hotkeys.
- Linux: install clipboard helpers (`xclip`/`xsel` on X11, `wl-clipboard` on Wayland). UI needs Tk (`python3-tk`).

## Code map

[converter.py](turkify/converter.py) handles conversion modes, [llm.py](turkify/llm.py) handles the local model path, and [watcher.py](turkify/watcher.py) integrates hotkeys and clipboard replacement. [tray.py](turkify/tray.py) and [ui.py](turkify/ui.py) provide the desktop controls.

Conversion can be ambiguous: model and heuristic results are suggestions, particularly for names and words whose intended Turkish spelling depends on context.
