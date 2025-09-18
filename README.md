# Turkify

Convert ASCII-typed Turkish text (typed with an English keyboard) into proper Turkish characters.

- CLI: convert given text or clipboard content
- UI: minimal Tkinter window for paste/convert/copy
- Global hotkey: convert selected text in-place via clipboard round-trip
 - Tray icon: `turkify-tray` provides Pause/Resume, Heuristic/LLM toggle, Change Hotkey, Open UI, Quit

Notes
- For best accuracy, install optional dependency `turkish-deasciifier`.
- On macOS, you may need to grant Accessibility permissions for global hotkeys.
- Optional local LLM: use llama.cpp backend with an auto-downloaded small GGUF model.

Quick start
- Run UI: `python -m turkify`
- CLI examples:
  - `turkify --text "cagri simdi guzeldi"`
  - `turkify --clipboard`
  - `turkify --watch-hotkey`
 - One-command watcher (heuristic): `turkify-watch`
 - One-command watcher (LLM, auto-download): `turkify-watch-llm`
 - Tray icon: `turkify-tray`

LLM usage
- Install extras: `pip install 'turkify[llm]'`
- Auto-download on first use: when you pass `--llm` and no model path is provided, turkify downloads a small default model to your cache automatically (unless `--no-auto-download` is set).
  - `turkify --llm --text "bugun hava cok guzel"`
- Specify model key or URL:
  - `turkify --llm --model-name qwen2.5-0.5b-instruct-q4_k_m --text "Istanbul icin simdi en iyi zaman"`
  - `turkify --llm --model-url https://.../model.gguf --text "ornek cumle"`
- Use an existing local GGUF:
  - `turkify --llm --llama-model /path/to/model.gguf --text "cok guzel"`

UI with LLM
- `export TURKIFY_USE_LLM=1` then `python -m turkify`.
- On initial launch, it prefetches the default model into your cache. Override with:
  - `TURKIFY_MODEL_NAME` (preset key) or `TURKIFY_MODEL_URL` (custom URL)

Packaging binaries
- Build single-file executables with PyInstaller:
  - Install dev deps: `pip install -e .[llm] pyinstaller`
  - CLI binary: `make package-cli` → `dist/turkify`
  - UI binary: `make package-ui` → `dist/turkify-ui`
- Notes:
  - macOS may require codesign/notarization to avoid warnings; Accessibility permission still needed.
  - Linux portability depends on glibc; build on an older distro for broad compatibility.
  - Windows builds run best when built on Windows.

Tray notes
- On macOS, the tray/menu bar icon provided by `pystray` may require `pyobjc`:
  - `pip install pyobjc`
  If the icon doesn’t appear, install pyobjc and try again.

Auto-start on login (optional)
- Install autostart (default LLM mode): `turkify --install-autostart`
- Heuristic-only autostart: `turkify --install-autostart heuristic`
- Tray autostart (LLM): `turkify --install-autostart tray-llm`
- Tray autostart (heuristic): `turkify --install-autostart tray-heuristic`
- Custom hotkey: `turkify --install-autostart llm --autostart-hotkey "<cmd>+<alt>+t"`
- Remove autostart: `turkify --uninstall-autostart`
- Under the hood:
  - macOS: creates `~/Library/LaunchAgents/com.turkify.watch.plist`
  - Windows: writes a `turkify-watch.bat` into the Startup folder
  - Linux: creates `~/.config/autostart/turkify.desktop`
