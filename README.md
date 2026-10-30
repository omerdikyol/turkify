<h1 align="center">Turkify</h1>

<p align="center">
  Restore Turkish characters in text typed on an English keyboard.<br>
  Select text, press a hotkey, and it is corrected in place.
</p>

<p align="center">
  <img alt="language: Python" src="https://img.shields.io/badge/language-Python-3776AB">
  <img alt="platform: macOS | Windows | Linux" src="https://img.shields.io/badge/platform-macOS%20%7C%20Windows%20%7C%20Linux-lightgrey">
  <img alt="model: local GGUF" src="https://img.shields.io/badge/model-local%20GGUF-blue">
</p>

Turkify converts text such as `cok guzel sarki cunku ogrenci simdi` back to proper Turkish. Use the global hotkey, the CLI, a tray app, or a small paste-and-convert UI.

## Features

- **Local LLM by default**: a llama.cpp backend with a small GGUF model (~220–260 MB), downloaded once and cached
- **Heuristic fallback**: conservative rules, improved by `turkish-deasciifier` if installed. Turkify falls back automatically if the LLM backend is unavailable
- **Global hotkey** that replaces the selected text, and restores your clipboard afterwards
- **Tray app** with Pause/Resume, LLM/Heuristic toggle, Change Hotkey, Open UI, and Quit
- **Auto-start on login** for the watcher or the tray app

## Install

Requires Python 3.8+.

```bash
python3 -m pip install .      # macOS / Linux
py -m pip install .           # Windows
```

## Quick start

| Goal | Command |
| --- | --- |
| Hotkey watcher, macOS | `turkify --watch-hotkey "<cmd>+<alt>+t"` |
| Hotkey watcher, Windows / Linux | `turkify --watch-hotkey` (defaults to Ctrl+Alt+T) |
| Watcher shortcut (LLM) | `turkify-watch` |
| Tray icon | `turkify-tray` |
| Paste-and-convert UI | `python -m turkify` |

The first LLM run downloads the model. The clipboard is restored after each conversion; add `--no-restore-clipboard` to keep the converted text on it.

## Examples

```bash
turkify --text "cok guzel sarki cunku ogrenci simdi"
turkify --text "Istanbul icin simdi en iyi zaman"

# Heuristic mode, no LLM
turkify --heuristic --text "bugun hava cok guzel"
turkify --heuristic --watch-hotkey --no-restore-clipboard

# Specific local model, preset, or URL (auto-download)
turkify --llama-model /path/to/model.gguf --text "ornek cumle"
turkify --model-name qwen2.5-0.5b-instruct-q4_k_m --text "sarkilar guzeldir"
turkify --model-url https://.../model.gguf --text "sarki soyle"
```

## Model and cache

The default model is Qwen2.5-0.5B-Instruct Q4_K_M (~220–260 MB).

| OS | Cache location |
| --- | --- |
| macOS | `~/Library/Caches/turkify/models` |
| Linux | `~/.cache/turkify/models` |
| Windows | `%LOCALAPPDATA%\turkify\models` |

Skip the download with `--no-auto-download` or `--heuristic`. For better heuristic rules: `python -m pip install turkish-deasciifier`.

## Auto-start on login

```bash
turkify --install-autostart                 # LLM watcher
turkify --install-autostart heuristic       # heuristic watcher
turkify --install-autostart tray-llm        # or tray-heuristic
turkify --install-autostart llm --autostart-hotkey "<cmd>+<alt>+t"
turkify --uninstall-autostart
```

| OS | Mechanism |
| --- | --- |
| macOS | `~/Library/LaunchAgents/com.turkify.watch.plist` |
| Windows | BAT file in the Startup folder |
| Linux | `~/.config/autostart/turkify.desktop` |

## Permissions and tips

- **macOS**: grant Accessibility permission for hotkeys. If the tray icon doesn't show, `pip install pyobjc`.
- **Linux**: install clipboard helpers (`xclip` or `xsel` on X11, `wl-clipboard` on Wayland). The UI needs Tk (`python3-tk`).

## Packaging (optional)

Single-file executables with PyInstaller:

```bash
pip install -e .[llm] pyinstaller
make package-cli    # dist/turkify
make package-ui     # dist/turkify-ui
```

macOS may require codesign, and Linux binaries depend on glibc. Build on the target OS for best results.

## Code map

[converter.py](turkify/converter.py) handles conversion modes, [llm.py](turkify/llm.py) the local model path, and [watcher.py](turkify/watcher.py) hotkeys and clipboard replacement. [tray.py](turkify/tray.py) and [ui.py](turkify/ui.py) provide the desktop controls.

Conversion can be ambiguous. Model and heuristic results are suggestions, particularly for names and words whose intended Turkish spelling depends on context.
